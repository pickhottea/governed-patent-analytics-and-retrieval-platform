# scripts/rag_ask_v2.py
from __future__ import annotations

import argparse
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests

CHROMA_DIR = "artifacts/chroma_patents_v1"
COLLECTION = "patent_chunks_v1"

# IMPORTANT: Chroma 內部 embeddings 是用哪個模型建的，查詢就必須用同一個模型。
# 你目前是 all-MiniLM-L6-v2；如果換成 multilingual，記得要重建 Chroma。
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "mistral:latest"


def ollama_run(prompt: str) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=600,
    )
    if r.status_code != 200:
        print("Ollama error status:", r.status_code)
        print("Ollama error body:", r.text[:500])
        r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()


def scope_where(scope: str) -> Dict[str, Any] | None:
    scope = (scope or "all").strip().lower()
    if scope == "claim":
        return {"chunk_type": "claim"}
    if scope == "spec":
        return {"chunk_type": "spec_fulltext"}
    return None


def retrieve_grouped(
    query: str,
    *,
    scope: str = "all",
    n_results: int = 30,
    top_pubs: int = 3,
    per_pub_topk: int = 2,
) -> Tuple[List[str], List[str]]:
    """
    Returns:
      pubs: ["EP....", ...] top publications (deduped)
      ctx:  ["[1] pub=...\\n<doc>\\n", ...] evidence chunks for LLM prompt
    """
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    col = client.get_collection(COLLECTION)

    model = SentenceTransformer(EMB_MODEL)
    qemb = model.encode([query], normalize_embeddings=True).tolist()[0]

    res = col.query(
        query_embeddings=[qemb],
        n_results=n_results,
        where=scope_where(scope),
        include=["documents", "metadatas", "distances"],
    )

    # group by publication
    by_pub: Dict[str, List[Tuple[float, str, Dict[str, Any]]]] = defaultdict(list)
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        pub = meta.get("publication") or meta.get("selected_publication") or "UNKNOWN"
        by_pub[pub].append((dist, doc, meta))

    # per pub: keep best K (by distance)
    pub_items: List[Tuple[float, str, List[Tuple[float, str, Dict[str, Any]]]]] = []
    for pub, lst in by_pub.items():
        lst_sorted = sorted(lst, key=lambda x: x[0])
        top_chunks = lst_sorted[:per_pub_topk]
        best_dist = top_chunks[0][0]
        pub_items.append((best_dist, pub, top_chunks))

    # pick top pubs
    pub_items.sort(key=lambda x: x[0])
    chosen = pub_items[:top_pubs]

    # build ctx for LLM
    ctx: List[str] = []
    chunk_id = 0
    pubs: List[str] = []
    for _, pub, chunks in chosen:
        pubs.append(pub)
        for dist, doc, meta in chunks:
            chunk_id += 1
            doc = (doc or "")[:1200]  # keep memory safe
            ctype = meta.get("chunk_type")
            claim_no = meta.get("claim_no")
            src = meta.get("claims_source") or meta.get("spec_source")
            flags = meta.get("flags", "")

            ctx.append(
                f"[{chunk_id}] pub={pub} type={ctype} claim_no={claim_no} src={src} flags={flags}\n"
                f"{doc}\n"
            )

    return pubs, ctx


def build_prompt(query: str, ctx: List[str]) -> str:
    return f"""
You are a patent analyst assistant.

User query:
{query}

Evidence chunks:
{chr(10).join(ctx)}

Output requirements:
A) Plain-language answer (1 short paragraph). No citations required.
B) Evidence-backed analysis (must cite chunk IDs):
   1) Top 3 publications with 1-2 sentences each explaining why (include chunk citations).
   2) For EACH of the top 3, provide:
      (a) technical problem
      (b) technical means (solution)
      (c) 2-3 evidence snippets (<=15 words each), each snippet must cite [chunk_id].

Rules:
- You MUST cite evidence using chunk IDs like [1], [2], etc.
- Do NOT infer sensors or features if not explicitly stated in evidence.
- If evidence is insufficient, say "insufficient evidence" and what is missing.

Return in English.
""".strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["all", "claim", "spec"], default="all", help="Search scope in Chroma")
    ap.add_argument("--view", choices=["user", "lite", "debug"], default="user",
                    help="user=only answer; lite=pub list + answer; debug=pub list + previews + answer")
    ap.add_argument("--query", default="", help="Query text. If omitted, you'll be prompted.")
    ap.add_argument("--top_pubs", type=int, default=3)
    ap.add_argument("--per_pub_topk", type=int, default=2)
    ap.add_argument("--n_results", type=int, default=30)
    args = ap.parse_args()

    q = (args.query or "").strip()
    if not q:
        q = input("Query: ").strip()
    if not q:
        return

    pubs, ctx = retrieve_grouped(
        q,
        scope=args.scope,
        n_results=args.n_results,
        top_pubs=args.top_pubs,
        per_pub_topk=args.per_pub_topk,
    )

    # View layer
    if args.view in ("lite", "debug"):
        print("\n=== Top Publications ===\n")
        for i, pub in enumerate(pubs, 1):
            print(f"{i}. {pub}")

    if args.view == "debug":
        # show a short preview per evidence chunk (still no distance)
        print("\n=== Evidence Preview (debug) ===\n")
        for line in ctx:
            header, body = line.split("\n", 1)
            preview = " ".join(body.split())[:180]
            print(header)
            print(f"  ↳ {preview}...\n")

    prompt = build_prompt(q, ctx)

    print("\n=== RAG Answer ===\n")
    ans = ollama_run(prompt)
    print(ans)


if __name__ == "__main__":
    main()
