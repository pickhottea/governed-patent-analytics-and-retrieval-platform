#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

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


# Conservative component extractor (English-biased)
NP_PAT = re.compile(r"\b(a|an|the|said)\s+([a-z0-9][a-z0-9 \-\_]{2,60})(?=,|;|\(|\.)", re.I)
STOP = {"device", "apparatus", "system", "module", "unit", "method"}


def extract_components(claim_text: str, max_terms: int = 12) -> List[str]:
    text = (claim_text or "").replace("\n", " ")
    terms: List[str] = []
    for m in NP_PAT.finditer(text):
        t = re.sub(r"\s+", " ", m.group(2).strip())
        if len(t) < 3:
            continue
        low = t.lower()
        if low in STOP:
            continue
        terms.append(t)

    out: List[str] = []
    seen = set()
    for t in terms:
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
        if len(out) >= max_terms:
            break
    return out


def pack_hits(docs, metas, dists) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        doc = doc or ""
        meta = meta or {}
        hits.append(
            {
                "distance": dist,
                "spec_chunk_type": meta.get("chunk_type"),
                "spec_source": meta.get("spec_source"),
                "jurisdiction": meta.get("jurisdiction"),
                "selected_publication": meta.get("selected_publication"),
                "family_id": meta.get("family_id"),
                "preview": doc[:400].replace("\n", " "),
            }
        )
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist_dir", default="vector_db")
    ap.add_argument("--spec_focus_collection", default="spec_focus_A")
    ap.add_argument("--claims_jsonl", default="artifacts/chunks_claims_all_v1.jsonl")
    ap.add_argument("--model", default="AI-Growth-Lab/PatentSBERTa")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--out", default="artifacts/map_claim_to_def_v2_family_first.jsonl")
    ap.add_argument("--only_independent", action="store_true", default=True)
    ap.add_argument("--min_family_hits", type=int, default=3, help="If family-scoped hits < this, fallback to global search to fill")
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
                q = f'{comp} as used herein defined as means refers to'
                q_emb = model.encode([q])[0]

                # 1) family-first
                res_fam = spec_col.query(
                    query_embeddings=[q_emb],
                    n_results=args.topk,
                    include=["documents", "metadatas", "distances"],
                    where={"family_id": family_id} if family_id is not None else None,
                )
                docs_f = res_fam.get("documents", [[]])[0]
                metas_f = res_fam.get("metadatas", [[]])[0]
                dists_f = res_fam.get("distances", [[]])[0]
                hits_f = pack_hits(docs_f, metas_f, dists_f)

                # 2) fallback to global if too few
                hits = hits_f
                fallback_used = False
                if len(hits_f) < args.min_family_hits:
                    res_g = spec_col.query(
                        query_embeddings=[q_emb],
                        n_results=args.topk,
                        include=["documents", "metadatas", "distances"],
                    )
                    docs_g = res_g.get("documents", [[]])[0]
                    metas_g = res_g.get("metadatas", [[]])[0]
                    dists_g = res_g.get("distances", [[]])[0]
                    hits_g = pack_hits(docs_g, metas_g, dists_g)

                    # merge: keep family hits first, then fill from global (dedup by selected_publication+preview head)
                    seen = set()
                    merged: List[Dict[str, Any]] = []
                    for h in hits_f + hits_g:
                        k = (h.get("selected_publication"), h.get("preview")[:80])
                        if k in seen:
                            continue
                        seen.add(k)
                        merged.append(h)
                        if len(merged) >= args.topk:
                            break
                    hits = merged
                    fallback_used = True

                rec = {
                    **ctx,
                    "component": comp,
                    "family_first": True,
                    "fallback_used": fallback_used,
                    "hits": hits,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1

    print(f"[done] wrote {out_path} rows={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
