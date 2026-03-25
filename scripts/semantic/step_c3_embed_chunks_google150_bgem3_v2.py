#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import chromadb
from sentence_transformers import SentenceTransformer


CHUNK_TYPES = ["claim_1", "claim_set", "spec"]
DEFAULT_COLLECTION_PREFIX = "semantic"
DEFAULT_PERSIST_ROOT = "artifacts/_prod_semantic"
DEFAULT_MODEL_KEY = "bge-m3"
DEFAULT_BATCH_SIZE = 8
DEFAULT_ENCODE_BATCH_SIZE = 8
DEFAULT_DEVICE = "cpu"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fail(msg: str, code: int = 1) -> None:
    print(f"[FATAL] {msg}")
    raise SystemExit(code)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as ex:
                fail(f"invalid JSON in {path} line {line_no}: {ex}")
    return rows


def batched(seq: List[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def resolve_model_name(model_key: str) -> str:
    alias_map = {
        "bge-m3": "BAAI/bge-m3",
        "patentsberta": "AI-Growth-Lab/PatentSBERTa",
    }
    if model_key not in alias_map:
        fail(f"unknown model_key: {model_key}")
    return alias_map[model_key]


def sanitize_model_key(model_key: str) -> str:
    return model_key.replace("-", "_")


def collection_name(prefix: str, chunk_type: str) -> str:
    return f"{prefix}_{chunk_type}_v2"


def vector_id(row: Dict[str, Any], embedding_version_id: str) -> str:
    family_id = str(row.get("family_id") or "").strip()
    chunk_type = str(row.get("chunk_type") or "").strip()
    if not family_id or not chunk_type:
        fail("missing family_id or chunk_type while constructing vector id")
    return f"{family_id}#{chunk_type}#{embedding_version_id}"


def ensure_required_rows(rows: List[Dict[str, Any]], chunk_type: str) -> None:
    required_fields = [
        "family_id",
        "selected_publication",
        "source",
        "chunk_type",
        "chunk_policy_version",
        "created_at",
        "text",
    ]
    for idx, row in enumerate(rows, start=1):
        for field in required_fields:
            if field not in row:
                fail(f"{chunk_type}: missing field '{field}' at row {idx}")
        if row.get("chunk_type") != chunk_type:
            fail(f"{chunk_type}: unexpected chunk_type at row {idx}: {row.get('chunk_type')}")
        if not str(row.get("family_id") or "").strip():
            fail(f"{chunk_type}: empty family_id at row {idx}")
        if not str(row.get("selected_publication") or "").strip():
            fail(f"{chunk_type}: empty selected_publication at row {idx}")
        if str(row.get("source") or "").strip().upper() != "GOOGLE":
            fail(f"{chunk_type}: non-GOOGLE source at row {idx}: {row.get('source')}")
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            fail(f"{chunk_type}: empty text at row {idx}")


def ensure_family_consistency(rows_by_type: Dict[str, List[Dict[str, Any]]], expected_families: int | None) -> List[str]:
    family_sets: Dict[str, set[str]] = {}
    for chunk_type, rows in rows_by_type.items():
        seen: Dict[str, int] = {}
        for row in rows:
            fid = str(row["family_id"]).strip()
            seen[fid] = seen.get(fid, 0) + 1
        bad = [fid for fid, n in seen.items() if n != 1]
        if bad:
            fail(f"{chunk_type}: expected exactly one row per family, sample duplicates={bad[:20]}")
        family_sets[chunk_type] = set(seen.keys())

    base = family_sets[CHUNK_TYPES[0]]
    for chunk_type in CHUNK_TYPES[1:]:
        if family_sets[chunk_type] != base:
            only_base = sorted(list(base - family_sets[chunk_type]))[:20]
            only_other = sorted(list(family_sets[chunk_type] - base))[:20]
            fail(
                f"family set mismatch between {CHUNK_TYPES[0]} and {chunk_type}; "
                f"only_{CHUNK_TYPES[0]}={only_base}, only_{chunk_type}={only_other}"
            )

    if expected_families is not None and len(base) != expected_families:
        fail(f"families={len(base)} != expected_families={expected_families}")

    return sorted(base)


def build_manifest_base(
    *,
    run_id: str,
    model_key: str,
    hf_model: str,
    device: str,
    persist_dir: Path,
    temp_dir: Path,
    collection_prefix: str,
    families: List[str],
    encode_batch_size: int,
    upsert_batch_size: int,
    max_seq_length: int,
    normalize_embeddings: bool,
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": utc_now(),
        "model_key": model_key,
        "hf_model": hf_model,
        "device": device,
        "chunk_policy_version": "v2.0",
        "embedding_policy_version": "v2.0",
        "source_lane": "GOOGLE_ONLY",
        "family_count": len(families),
        "families": families,
        "collection_prefix": collection_prefix,
        "persist_dir": str(persist_dir),
        "temp_dir": str(temp_dir),
        "encode_batch_size": encode_batch_size,
        "upsert_batch_size": upsert_batch_size,
        "max_seq_length": max_seq_length,
        "normalize_embeddings": normalize_embeddings,
        "collections": {},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_id", required=True)
    ap.add_argument("--model_key", default=DEFAULT_MODEL_KEY, help="bge-m3 or patentsberta")
    ap.add_argument("--persist_root", default=DEFAULT_PERSIST_ROOT)
    ap.add_argument("--collection_prefix", default=DEFAULT_COLLECTION_PREFIX)
    ap.add_argument("--expected_families", type=int, default=150)
    ap.add_argument("--device", default=DEFAULT_DEVICE, help="cpu / cuda / mps")
    ap.add_argument("--encode_batch_size", type=int, default=DEFAULT_ENCODE_BATCH_SIZE)
    ap.add_argument("--upsert_batch_size", type=int, default=DEFAULT_BATCH_SIZE)
    ap.add_argument("--max_seq_length", type=int, default=512)
    ap.add_argument("--normalize_embeddings", action="store_true")
    ap.add_argument("--allow_overwrite", action="store_true")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    run_dir = repo / "artifacts" / "_pipeline_runs" / args.run_id
    chunk_dir = run_dir / "chunks_v2"
    if not chunk_dir.exists():
        fail(f"chunks_v2 directory not found: {chunk_dir}")

    files = {chunk_type: chunk_dir / f"{chunk_type}.jsonl" for chunk_type in CHUNK_TYPES}
    for chunk_type, path in files.items():
        if not path.exists():
            fail(f"missing chunk file: {path}")

    rows_by_type: Dict[str, List[Dict[str, Any]]] = {}
    for chunk_type, path in files.items():
        rows = load_jsonl(path)
        ensure_required_rows(rows, chunk_type)
        rows_by_type[chunk_type] = rows

    families = ensure_family_consistency(rows_by_type, args.expected_families)
    hf_model = resolve_model_name(args.model_key)
    model_key_safe = sanitize_model_key(args.model_key)

    persist_root = repo / args.persist_root
    final_dir = persist_root / f"{model_key_safe}_v2_google150"
    temp_dir = persist_root / f"_tmp_{model_key_safe}_v2_google150__{args.run_id}"

    if final_dir.exists() and not args.allow_overwrite:
        fail(f"final persist dir already exists: {final_dir} (use --allow_overwrite to replace)")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] loading model {hf_model} on device={args.device}")
    model = SentenceTransformer(hf_model, device=args.device)
    try:
        model.max_seq_length = args.max_seq_length
    except Exception:
        pass

    dim = model.get_sentence_embedding_dimension()
    embedding_version_id = f"{args.model_key}__v2.0__google150"

    client = chromadb.PersistentClient(path=str(temp_dir))
    manifest = build_manifest_base(
        run_id=args.run_id,
        model_key=args.model_key,
        hf_model=hf_model,
        device=args.device,
        persist_dir=final_dir,
        temp_dir=temp_dir,
        collection_prefix=args.collection_prefix,
        families=families,
        encode_batch_size=args.encode_batch_size,
        upsert_batch_size=args.upsert_batch_size,
        max_seq_length=args.max_seq_length,
        normalize_embeddings=args.normalize_embeddings,
    )
    manifest["embedding_dim"] = dim
    manifest["embedding_version_id"] = embedding_version_id

    try:
        for chunk_type in CHUNK_TYPES:
            rows = rows_by_type[chunk_type]
            coll_name = collection_name(args.collection_prefix, chunk_type)
            try:
                client.delete_collection(coll_name)
            except Exception:
                pass
            collection = client.get_or_create_collection(name=coll_name)

            total = len(rows)
            print(f"[info] {chunk_type}: {total} rows -> collection={coll_name}")

            for batch_idx, batch_rows in enumerate(batched(rows, args.upsert_batch_size), start=1):
                texts = [str(r["text"]) for r in batch_rows]
                embeddings = model.encode(
                    texts,
                    batch_size=args.encode_batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=args.normalize_embeddings,
                    convert_to_numpy=True,
                )
                ids = [vector_id(r, embedding_version_id) for r in batch_rows]
                metadatas = []
                for row in batch_rows:
                    metadatas.append({
                        "family_id": str(row["family_id"]),
                        "dataset_family_id": str(row.get("dataset_family_id") or row["family_id"]),
                        "selected_publication": str(row["selected_publication"]),
                        "source": str(row.get("source") or "GOOGLE"),
                        "chunk_type": chunk_type,
                        "chunk_policy_version": str(row.get("chunk_policy_version") or "v2.0"),
                        "embedding_version_id": embedding_version_id,
                        "run_id": args.run_id,
                        "embedded_at": utc_now(),
                        "claims_lang_hint": row.get("claims_lang_hint", ""),
                        "spec_policy": row.get("spec_policy", ""),
                        "claim1_extraction_quality": row.get("claim1_extraction_quality", ""),
                    })
                collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                )
                done = min(batch_idx * args.upsert_batch_size, total)
                print(f"[progress] {chunk_type}: {done}/{total}")

            manifest["collections"][coll_name] = {
                "chunk_type": chunk_type,
                "count": total,
            }
            print(f"[ok] {coll_name} -> {total} vectors")

        if final_dir.exists() and args.allow_overwrite:
            shutil.rmtree(final_dir)
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_dir), str(final_dir))

        success_flag = final_dir / "SUCCESS.flag"
        success_flag.write_text("OK\n", encoding="utf-8")

        manifest_path = run_dir / f"embedding_manifest_{args.model_key}_google150.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print("[done] embedding complete")
        print(f"[done] manifest: {manifest_path}")
        print(f"[done] persist_dir: {final_dir}")
        print(f"[done] success_flag: {success_flag}")
        return 0

    except KeyboardInterrupt:
        print("[warn] interrupted; cleaning temp dir")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise SystemExit(130)
    except Exception as ex:
        print(f"[error] build failed: {ex}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
