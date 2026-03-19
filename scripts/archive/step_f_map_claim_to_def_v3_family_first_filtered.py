#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# -------------------------
# Component extraction (conservative)
# -------------------------
NP_PAT = re.compile(r"\b(a|an|the|said)\s+([a-z0-9][a-z0-9 \-\_]{2,80})(?=,|;|\(|\.)", re.I)

STOP_EXACT = {
    "lamp","base","plate","member","portion","part","unit","device","system","apparatus",
    "module","housing","substrate","opening","column"
}

STOP_TOKENS = {"lamp","base","plate","member","portion","part","unit","device","system","apparatus","module","housing","substrate"}

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def is_low_value_component(comp: str) -> bool:
    c = normalize_ws(comp).lower()
    if not c:
        return True
    toks = c.split()
    # drop single-token generic nouns
    if len(toks) < 2:
        return True
    if c in STOP_EXACT:
        return True
    # drop if ALL tokens are generic
    if all(t in STOP_TOKENS for t in toks):
        return True
    return False

def extract_components(claim_text: str, max_terms: int = 12) -> List[str]:
    text = normalize_ws((claim_text or "").replace("\n", " "))
    cand: List[str] = []
    for m in NP_PAT.finditer(text):
        t = normalize_ws(m.group(2))
        if len(t) < 4:
            continue
        if is_low_value_component(t):
            continue
        cand.append(t)

    out: List[str] = []
    seen = set()
    for t in cand:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
        if len(out) >= max_terms:
            break
    return out


# -------------------------
# Hit filtering (remove boilerplate / fig captions)
# -------------------------
BAD_SNIPPETS = [
    "it is noted that when a component",
    "first and second are used for descriptive purposes",
    "the term \"plurality\"",
    "fig.",
    "is a perspective view",
    "is a structural diagram",
]

def is_bad_hit_text(txt: str) -> bool:
    t = (txt or "").lower()
    return any(b in t for b in BAD_SNIPPETS)


def pack_hits(docs, metas, dists, topk: int) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        doc = doc or ""
        meta = meta or {}
        if is_bad_hit_text(doc):
            continue
        hits.append(
            {
                "distance": dist,
                "spec_chunk_type": meta.get("chunk_type"),
                "spec_source": meta.get("spec_source"),
                "jurisdiction": meta.get("jurisdiction"),
                "selected_publication": meta.get("selected_publication"),
                "family_id": meta.get("family_id"),
                "preview": doc[:450].replace("\n", " "),
            }
        )
        if len(hits) >= topk:
            break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist_dir", default="vector_db")
    ap.add_argument("--spec_focus_collection", default="spec_focus_A")
    ap.add_argument("--claims_jsonl", default="artifacts/chunks_claims_all_v1.jsonl")
    ap.add_argument("--model", default="AI-Growth-Lab/PatentSBERTa")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--out", default="artifacts/map_claim_to_def_v3_family_first_filtered.jsonl")
    ap.add_argument("--only_independent", action="store_true", default=True)
    ap.add_argument("--min_family_hits", type=int, default=3)
    args = ap.parse_args()

    claims_rows = load_jsonl(args.claims_jsonl)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=args.persist_dir)
    spec_col = client.get_collection(args.spec_focus_collection)

    model = SentenceTransformer(args.model)
    try:
        model.max_seq_length = 512
    except Exception:
        pass

    n = 0
    with out_path.open("w", encoding="utf-8") as out:
        for r in claims_rows:
            if args.only_independent and r.get("claim_type") != "independent":
                continue

            claim_text = str(r.get("text") or "")
            comps = extract_components(claim_text)
            if not comps:
                continue

            family_id = r.get("family_id")
            ctx = {
                "created_at": now_iso(),
                "family_id": family_id,
                "asset_id": r.get("asset_id"),
                "selected_publication": r.get("selected_publication"),
                "jurisdiction": r.get("jurisdiction"),
                "claim_no": r.get("claim_no"),
                "claim_id": r.get("chunk_id"),
            }

            for comp in comps:
                q = f'{comp} definition as used herein refers to'
                q_emb = model.encode([q])[0]

                # family-first
                res_fam = spec_col.query(
                    query_embeddings=[q_emb],
                    n_results=max(args.topk * 3, 10),
                    include=["documents", "metadatas", "distances"],
                    where={"family_id": family_id} if family_id is not None else None,
                )
                hits_f = pack_hits(
                    res_fam.get("documents", [[]])[0],
                    res_fam.get("metadatas", [[]])[0],
                    res_fam.get("distances", [[]])[0],
                    topk=args.topk,
                )

                hits = hits_f
                fallback_used = False

                if len(hits_f) < args.min_family_hits:
                    res_g = spec_col.query(
                        query_embeddings=[q_emb],
                        n_results=max(args.topk * 3, 10),
                        include=["documents", "metadatas", "distances"],
                    )
                    hits_g = pack_hits(
                        res_g.get("documents", [[]])[0],
                        res_g.get("metadatas", [[]])[0],
                        res_g.get("distances", [[]])[0],
                        topk=args.topk,
                    )

                    # merge: family first, then global fill; dedup by (pub, preview head)
                    seen = set()
                    merged: List[Dict[str, Any]] = []
                    for h in hits_f + hits_g:
                        k = (h.get("selected_publication"), (h.get("preview") or "")[:120])
                        if k in seen:
                            continue
                        seen.add(k)
                        merged.append(h)
                        if len(merged) >= args.topk:
                            break
                    hits = merged
                    fallback_used = True

                rec = {**ctx, "component": comp, "fallback_used": fallback_used, "hits": hits}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1

    print(f"[done] wrote {out_path} rows={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
