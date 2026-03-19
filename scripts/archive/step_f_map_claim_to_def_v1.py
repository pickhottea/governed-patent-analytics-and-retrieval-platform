#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
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


# very conservative component extractor (English-biased, but works ok for your corpus)
# extracts noun-phrases after "a/an/the/said" up to comma/semicolon
NP_PAT = re.compile(r"\b(a|an|the|said)\s+([a-z0-9][a-z0-9 \-\_]{2,60})(?=,|;|\(|\.)", re.I)

STOP = {
    "device", "apparatus", "system", "module", "unit", "method", "circuit", "lamp", "lighting device"
}


def extract_components(claim_text: str, max_terms: int = 12) -> List[str]:
    text = (claim_text or "").replace("\n", " ")
    terms: List[str] = []
    for m in NP_PAT.finditer(text):
        t = m.group(2).strip()
        t = re.sub(r"\s+", " ", t)
        if len(t) < 3:
            continue
        # prune very generic headwords
        low = t.lower()
        if low in STOP:
            continue
        if low.startswith("one or more"):
            continue
        terms.append(t)

    # de-dup preserve order
    out = []
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist_dir", default="vector_db")
    ap.add_argument("--claims_collection", default="claims_all_A")
    ap.add_argument("--spec_focus_collection", default="spec_focus_A")
    ap.add_argument("--claims_jsonl", default="artifacts/chunks_claims_all_v1.jsonl")
    ap.add_argument("--model", default="AI-Growth-Lab/PatentSBERTa")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--out", default="artifacts/map_claim_to_def_v1.jsonl")
    ap.add_argument("--only_independent", action="store_true", default=True)
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

            ctx = {
                "family_id": r.get("family_id"),
                "asset_id": r.get("asset_id"),
                "selected_publication": r.get("selected_publication"),
                "jurisdiction": r.get("jurisdiction"),
                "claim_no": r.get("claim_no"),
                "claim_id": r.get("chunk_id"),
            }

            for comp in comps:
                # component->definition query template
                q = f'{comp} as used herein defined as means refers to'
                q_emb = model.encode([q])[0]

                res = spec_col.query(
                    query_embeddings=[q_emb],
                    n_results=args.topk,
                    include=["documents", "metadatas", "distances"],
                )

                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                dists = res.get("distances", [[]])[0]

                hits: List[Dict[str, Any]] = []
                for doc, meta, dist in zip(docs, metas, dists):
                    doc = doc or ""
                    meta = meta or {}
                    hits.append({
                        "distance": dist,
                        "spec_chunk_type": meta.get("chunk_type"),
                        "spec_source": meta.get("spec_source"),
                        "jurisdiction": meta.get("jurisdiction"),
                        "selected_publication": meta.get("selected_publication"),
                        "preview": doc[:400].replace("\n", " "),
                    })

                rec = {
                    "created_at": now_iso(),
                    **ctx,
                    "component": comp,
                    "hits": hits,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1

    print(f"[done] wrote {out_path} rows={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
