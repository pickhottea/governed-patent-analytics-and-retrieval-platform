# scripts/rag_ask_v2.py
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import requests
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

PROD_REGISTRY = "artifacts/PROD_EMBEDDING_REGISTRY.json"

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:latest")


def load_registry() -> dict:
    if os.path.exists(PROD_REGISTRY):
        return json.loads(open(PROD_REGISTRY, "r", encoding="utf-8").read())
    # fallback
    return {
        "chroma_dir": "artifacts/chroma_patents_patentsberta_v1",
        "collection": "patent_chunks_patentsberta_v1",
        "embedding_model": "AI-Growth-Lab/PatentSBERTa",
    }


def ollama_run(prompt: str, *, timeout_s: int = 90, num_predict: int = 256, num_ctx: int = 2048) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": int(num_predict), "num_ctx": int(num_ctx)},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
    if r.status_code != 200:
        try:
            msg = r.json()
        except Exception:
            msg = {"error": r.text[:800]}
        raise RuntimeError(f"Ollama error {r.status_code}: {msg}")
    data = r.json()
    return (data.get("response") or "").strip()


def scope_where(scope: str) -> Dict[str, Any] | None:
    scope = (scope or "all").strip().lower()
    if scope == "claim":
        return {"chunk_type": "claim"}
    if scope == "spec":
        return {"chunk_type": "spec_fulltext"}
    return None


def retrieve_grouped_fast(
    query: str,
    *,
    scope: str = "all",
    n_results: int = 20,
    top_pubs: int = 3,
    per_pub_topk: int = 1,
) -> Tuple[List[dict], List[str]]:
    reg = load_registry()
    chroma_dir = reg.get("chroma_dir") or reg.get("path") or "artifacts/chroma_patents_patentsberta_v1"
    collection = reg.get("collection") or reg.get("collection_name") or "patent_chunks_patentsberta_v1"
    emb_model = reg.get("embedding_model") or "AI-Growth-Lab/PatentSBERTa"

    client = chromadb.PersistentClient(path=chroma_dir, settings=Settings(anonymized_telemetry=False))
    col = client.get_collection(collection)

    model = SentenceTransformer(emb_model)
    try:
        model.max_seq_length = 384
    except Exception:
        pass

    qemb = model.encode([query], normalize_embeddings=True).tolist()[0]

    res = col.query(
        query_embeddings=[qemb],
        n_results=n_results,
        where=scope_where(scope),
        include=["documents", "metadatas", "distances"],
    )

    by_pub: Dict[str, List[Tuple[float, str, Dict[str, Any]]]] = defaultdict(list)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        pub = meta.get("publication") or meta.get("selected_publication") or "UNKNOWN"
        by_pub[pub].append((float(dist), doc or "", meta))

    pub_items: List[Tuple[float, str, List[Tuple[float, str, Dict[str, Any]]]]] = []
    for pub, lst in by_pub.items():
        lst_sorted = sorted(lst, key=lambda x: x[0])
        top_chunks = lst_sorted[:per_pub_topk]
        best_dist = top_chunks[0][0]
        pub_items.append((best_dist, pub, top_chunks))

    pub_items.sort(key=lambda x: x[0])
    chosen = pub_items[:top_pubs]

    ctx: List[str] = []
    pubs: List[dict] = []
    chunk_id = 0

    for best_dist, pub, chunks in chosen:
        pubs.append({"publication": pub, "best_distance": float(best_dist)})
        for dist, doc, meta in chunks:
            chunk_id += 1
            doc = (doc or "")[:650]
            ctype = meta.get("chunk_type")
            claim_no = meta.get("claim_no")
            src = meta.get("claims_source") or meta.get("spec_source")
            flags = meta.get("flags", "")
            ctx.append(
                f"[{chunk_id}] pub={pub} dist={float(dist):.4f} type={ctype} claim_no={claim_no} src={src} flags={flags}\n"
                f"{doc}\n"
            )

    return pubs, ctx


def build_prompt(query: str, pubs: List[dict], ctx: List[str]) -> str:
    top_lines = "\n".join([f"- {p['publication']} (best_distance={p['best_distance']:.4f})" for p in pubs])
    return f"""
You are a patent analyst assistant.

User query:
{query}

Top publications:
{top_lines}

Evidence chunks (cite [chunk_id]):
{chr(10).join(ctx)}

Explain:
1) Why these Top matches the query (1-2 sentences each, MUST cite chunk IDs).
2) For each publication:
   - technical problem
   - technical means
   - 2 short evidence snippets (<=15 words) with citations.

Rules:
- Cite evidence using [1], [2]...
- Distance: higher = less similar.
Return in English.
""".strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["all", "claim", "spec"], default="spec")
    ap.add_argument("--query", default="")
    ap.add_argument("--top_pubs", type=int, default=3)
    ap.add_argument("--per_pub_topk", type=int, default=1)
    ap.add_argument("--n_results", type=int, default=20)
    args = ap.parse_args()

    q = (args.query or "").strip()
    if not q:
        q = input("Query: ").strip()
    if not q:
        return

    pubs, ctx = retrieve_grouped_fast(
        q,
        scope=args.scope,
        n_results=args.n_results,
        top_pubs=args.top_pubs,
        per_pub_topk=args.per_pub_topk,
    )

    print("\n=== Top Publications ===\n")
    for i, p in enumerate(pubs, 1):
        print(f"{i}. {p['publication']}  best_distance={p['best_distance']:.4f}")

    prompt = build_prompt(q, pubs, ctx)

    print("\n=== RAG Answer ===\n")
    ans = ollama_run(prompt, timeout_s=90, num_predict=256, num_ctx=2048)
    print(ans)


if __name__ == "__main__":
    main()
