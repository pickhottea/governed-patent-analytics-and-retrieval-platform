# scripts/rag_ask_v1.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests

CHROMA_DIR = "artifacts/chroma_patents_v1"
COLLECTION = "patent_chunks_v1"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "mistral"  # 你有 pull 的話


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


def main():
    scope = input("Scope (all/claim/spec) [all]: ").strip().lower() or "all"
    where = None
    if scope == "claim":
        where = {"chunk_type": "claim"}
    elif scope == "spec":
        where = {"chunk_type": "spec_fulltext"}

    q = input("Query: ").strip()
    if not q:
        return

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    col = client.get_collection(COLLECTION)

    model = SentenceTransformer(EMB_MODEL)
    qemb = model.encode([q], normalize_embeddings=True).tolist()[0]

    res = col.query(
        query_embeddings=[qemb],
        n_results=4,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    print("\n=== Top Chunks (retrieval) ===\n")

    ctx = []
    for i,(doc,meta,dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1
    ):
        doc = doc[:1200]
        pub = meta.get("publication") or meta.get("selected_publication")
        ctype = meta.get("chunk_type")
        claim_no = meta.get("claim_no")
        src = meta.get("claims_source") or meta.get("spec_source")
        flags = meta.get("flags","")

        print(f"[{i}] dist={dist:.3f} pub={pub} type={ctype} claim_no={claim_no} src={src} flags={flags}")

        ctx.append(
            f"[{i}] pub={pub} type={ctype} claim_no={claim_no} src={src} flags={flags} dist={dist:.3f}\n"
            f"{doc}\n"
        )

    prompt = f"""
You are a patent analyst assistant.

User query:
{q}

Evidence chunks:
{chr(10).join(ctx)}

Task:
1) Pick the best-matching publications (top 3) and explain why.
2) For EACH of the top 3, provide:
   (a) technical problem
   (b) technical means (solution)
   (c) 2-3 evidence snippets (<=15 words each)

Rules:
- You MUST cite evidence using chunk IDs like [1], [2], etc.
- Do NOT infer sensors if not explicitly stated.
- If insufficient evidence, say so.

Output format:
- Top 3 list
- Then one section per publication
""".strip()

    print("\n=== Generating Answer ===\n")
    ans = ollama_run(prompt)
    print("\n=== RAG Answer ===\n")
    print(ans)



if __name__ == "__main__":
    main()
