# scripts/build_chroma.py
import json
import re
from pathlib import Path
from typing import Iterable, Dict, Any, List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

DATA_JSONL = Path("artifacts/claims_representation_v3.jsonl")  # <- 改成你的
CHROMA_DIR = Path("artifacts/chroma_patents_v1")
COLLECTION = "patent_chunks_v1"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 免費、輕量

def load_jsonl(p: Path) -> Iterable[Dict[str, Any]]:
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def chunk_claims_all(claims_text: str) -> List[str]:
    """
    兩種都行：
    A) 每條 claim 一 chunk（最好）
    B) 若你只有大段文字，就先粗切（示範簡化版）
    """
    t = claims_text or ""
    # 嘗試用 "1." "2." 分段（很粗但 demo 夠）
    parts = re.split(r"\n(?=\d+\.\s)", t)
    parts = [normalize_ws(x) for x in parts if normalize_ws(x)]
    return parts[:200]  # 避免炸

def chunk_spec_paragraphs(spec_text: str) -> List[str]:
    t = spec_text or ""
    paras = [normalize_ws(x) for x in t.split("\n\n")]
    paras = [p for p in paras if len(p) >= 40]
    return paras[:400]

def main():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    col = client.get_or_create_collection(name=COLLECTION)

    embedder = SentenceTransformer(MODEL_NAME)

    ids, docs, metas = [], [], []
    n = 0

    for row in load_jsonl(DATA_JSONL):
        family_id = str(row.get("family_id") or "")
        pub = str(row.get("selected_publication") or row.get("claims_publication_number") or "")
        claims_source = str(row.get("claims_source") or "")
        flags = row.get("governance_flags") or []
        has_claim1 = bool(row.get("claim_1"))

        # 你自己的欄位名可能不同：自己對一下
        claim_1 = normalize_ws(row.get("claim_1") or "")
        claims_all = normalize_ws(row.get("claims_text") or row.get("claims_all") or "")
        spec = normalize_ws(row.get("spec_text") or row.get("description") or "")

        # --- chunk: claim_1 (1 chunk)
        if claim_1:
            ids.append(f"{family_id}|{pub}|claim_1")
            docs.append(claim_1)
            metas.append({
                "family_id": family_id,
                "publication": pub,
                "chunk_type": "claim_1",
                "claims_source": claims_source,
                "has_claim1": has_claim1,
                "flags": ",".join(flags),
            })

        # --- chunk: claims_all (N chunks)
        if claims_all:
            for i, c in enumerate(chunk_claims_all(claims_all)):
                ids.append(f"{family_id}|{pub}|claims_all|{i}")
                docs.append(c)
                metas.append({
                    "family_id": family_id,
                    "publication": pub,
                    "chunk_type": "claims_all",
                    "chunk_i": i,
                    "claims_source": claims_source,
                    "has_claim1": has_claim1,
                    "flags": ",".join(flags),
                })

        # --- chunk: spec_paragraphs (N chunks)
        if spec:
            for i, p in enumerate(chunk_spec_paragraphs(spec)):
                ids.append(f"{family_id}|{pub}|spec|{i}")
                docs.append(p)
                metas.append({
                    "family_id": family_id,
                    "publication": pub,
                    "chunk_type": "spec_paragraphs",
                    "chunk_i": i,
                    "claims_source": claims_source,
                    "has_claim1": has_claim1,
                    "flags": ",".join(flags),
                })

        # 批次寫入避免記憶體爆
        if len(ids) >= 256:
            embs = embedder.encode(docs, normalize_embeddings=True).tolist()
            col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
            n += len(ids)
            ids, docs, metas = [], [], []

    if ids:
        embs = embedder.encode(docs, normalize_embeddings=True).tolist()
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        n += len(ids)

    print(f"[ok] wrote chunks -> {COLLECTION}, total={n}, dir={CHROMA_DIR}")

if __name__ == "__main__":
    main()
