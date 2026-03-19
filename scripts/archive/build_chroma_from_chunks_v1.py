import json
from pathlib import Path
from collections import Counter

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path("artifacts/chroma_patents_v1")
COLLECTION = "patent_chunks_v1"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_FILES = [
    Path("artifacts/chunks_claims_all_v1.jsonl"),
    Path("artifacts/chunks_spec_all_v1.jsonl"),
]

def load_jsonl(p: Path):
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def main():
    seen_ids = set()
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    col = client.get_or_create_collection(name=COLLECTION)

    embedder = SentenceTransformer(MODEL_NAME)
    ctr = Counter()

    ids, docs, metas = [], [], []

    for fp in CHUNK_FILES:
        if not fp.exists():
            print(f"[warn] missing: {fp}")
            ctr["missing_file"] += 1
            continue

        for o in load_jsonl(fp):
            ctr["seen"] += 1

            text = (o.get("text") or "").strip()
            if not text:
                ctr["skip:no_text"] += 1
                continue

            family_id = str(o.get("family_id") or "")
            pub = str(o.get("selected_publication") or "")
            chunk_type = str(o.get("chunk_type") or fp.stem)

            # 強制把 chunk_type + pub 放進 ID，避免跨檔/跨類型撞 id
            raw_chunk_id = o.get("chunk_id")
            if raw_chunk_id:
                cid = f"{chunk_type}|{pub}|{raw_chunk_id}"
            else:
                # spec 檔沒有 chunk_id，就用 (pub + seen) 或 hash(text) 也行
                cid = f"{chunk_type}|{pub}|{ctr['seen']}"


            meta = {
                "family_id": family_id,
                "publication": pub,
                "chunk_type": chunk_type,
            }

            # 可選：把治理欄位帶進 metadata（你 UI 會想顯示 badge）
            if "claims_source" in o:
                meta["claims_source"] = str(o.get("claims_source") or "")
            if "spec_source" in o:
                meta["spec_source"] = str(o.get("spec_source") or "")
            if "governance_flags" in o and isinstance(o["governance_flags"], list):
                meta["flags"] = ",".join(map(str, o["governance_flags"]))
            if "claim_no" in o and o["claim_no"] is not None:
                meta["claim_no"] = int(o["claim_no"])
            if cid in seen_ids:
                ctr["skip:dup_id"] += 1
                continue
            seen_ids.add(cid)


            ids.append(cid)
            docs.append(text)
            metas.append(meta)

            if len(ids) >= 256:
                embs = embedder.encode(docs, normalize_embeddings=True).tolist()
                col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
                ctr["emit"] += len(ids)
                ids, docs, metas = [], [], []

    if ids:
        embs = embedder.encode(docs, normalize_embeddings=True).tolist()
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        ctr["emit"] += len(ids)

    print("[ok] build chroma done")
    print("counters:", dict(ctr))
    print("dir:", CHROMA_DIR)
    print("collection:", COLLECTION)

if __name__ == "__main__":
    main()
