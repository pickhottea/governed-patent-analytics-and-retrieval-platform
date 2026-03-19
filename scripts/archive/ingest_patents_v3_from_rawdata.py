# scripts/ingest_patents_v3_from_rawdata.py
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

ES = os.environ.get("ES_URL", "http://localhost:9200")
INDEX = os.environ.get("ES_INDEX", "patents_v3")
XLSX = os.environ.get("RAW_XLSX", "rawdata_patents.xlsx")

# --- Token regex (best-effort, no taxonomy mapping) ---
IPC_RE = re.compile(r"\b([A-H]\d{2}[A-Z]\d{0,3}(?:\d+)?(?:/\d+)?)\b")
# CPC can be like: Y02B 40/10, H01L 33/00, F21V 23/00 ...
CPC_RE = re.compile(r"\b([A-Z]\d{2}[A-Z]\s*\d+(?:/\d+)?)\b")

# WO should not be shown on map (proxy rule), but keep in ES
WO_PREFIX = "WO"


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def pub_to_docdb(pub: str) -> str:
    """
    Convert raw publication_number like 'EP3919806A1' or 'US2021381658A1'
    into docdb-ish 'EP.3919806.A1' for consistency in UI.
    If already contains '.', keep it.
    """
    p = (pub or "").strip()
    if not p:
        return ""
    if "." in p:
        return p.upper()

    p = p.upper().replace(" ", "")
    if len(p) < 6:
        return p

    cc = p[:2]
    kind = p[-2:]
    num = p[2:-2]
    if not num.isdigit():
        # fallback: just return cleaned
        return re.sub(r"[^A-Z0-9]", "", p)
    return f"{cc}.{num}.{kind}"


def pub_to_jur(pub_docdb: str) -> str:
    return (pub_docdb or "").split(".", 1)[0].upper()


def extract_tokens(val: Any, pattern: re.Pattern) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        s = " ".join(str(x) for x in val)
    else:
        s = str(val)
    s = s.upper()
    tokens = pattern.findall(s)
    # normalize spaces in CPC tokens
    out = []
    for t in tokens:
        out.append(re.sub(r"\s+", "", t))
    # dedup, stable order
    seen = set()
    uniq = []
    for t in out:
        if t and t not in seen:
            uniq.append(t)
            seen.add(t)
    return uniq


def bulk_ndjson(lines: List[str]) -> Dict[str, Any]:
    # IMPORTANT: bulk body MUST end with newline
    body = "\n".join(lines) + "\n"
    r = requests.post(
        f"{ES}/_bulk",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
        timeout=180,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"bulk failed {r.status_code}: {r.text[:800]}")
    out = r.json()
    if out.get("errors"):
        items = out.get("items", [])[:10]
        raise RuntimeError(f"bulk errors: {json.dumps(items, ensure_ascii=False)[:2000]}")
    return out


def ensure_index() -> None:
    # create if not exists
    r = requests.get(f"{ES}/{INDEX}", timeout=30)
    if r.status_code == 200:
        return

    mapping = {
        "mappings": {
            "properties": {
                # identity
                "doc_id": {"type": "keyword"},
                "publication_number": {"type": "keyword"},
                "publication_docdb": {"type": "keyword"},
                "jurisdiction": {"type": "keyword"},
                "family_id": {"type": "keyword"},

                # people/org
                "applicants": {"type": "keyword"},
                "inventors": {"type": "keyword"},

                # classification
                "ipc": {"type": "keyword"},
                "cpc": {"type": "keyword"},
                "ipc_tokens": {"type": "keyword"},
                "cpc_tokens": {"type": "keyword"},

                # dates
                "earliest_priority_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||yyyyMMdd"},
                "publication_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd||yyyyMMdd"},

                # text fields
                "title": {"type": "text"},
                # optional: keep as text if you want later
                "abstract": {"type": "text"},

                # governance
                "governance_flags": {"type": "keyword"},
            }
        }
    }
    cr = requests.put(f"{ES}/{INDEX}", json=mapping, timeout=60)
    cr.raise_for_status()


def read_raw_xlsx(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_excel(p, engine="openpyxl")
    # normalize columns (keep your original names)
    # Required:
    # No, title, inventors, applicants, publication_number, grant_number,
    # earliest_priority_date, ipc, cpc, publication_date, earliest_publication, family_id
    return df


def main() -> None:
    ensure_index()

    df = read_raw_xlsx(XLSX)
    df = df.fillna("")

    actions: List[str] = []
    sent = 0

    for _, row in df.iterrows():
        pub_raw = str(row.get("publication_number", "")).strip()
        if not pub_raw:
            continue

        pub_docdb = pub_to_docdb(pub_raw)
        jur = pub_to_jur(pub_docdb)

        family_id = str(row.get("family_id", "")).strip() or None

        # doc_id should be stable + allow strict separation if needed
        doc_id = sha1(f"pubfam|{pub_docdb}|{family_id or 'NA'}")

        ipc_val = row.get("ipc", "")
        cpc_val = row.get("cpc", "")

        doc = {
            "doc_id": doc_id,
            "publication_number": pub_raw,
            "publication_docdb": pub_docdb,
            "jurisdiction": jur,
            "family_id": family_id,

            "title": str(row.get("title", "")).strip(),
            "inventors": str(row.get("inventors", "")).strip(),
            "applicants": str(row.get("applicants", "")).strip(),

            "ipc": str(ipc_val).strip(),
            "cpc": str(cpc_val).strip(),
            "ipc_tokens": extract_tokens(ipc_val, IPC_RE),
            "cpc_tokens": extract_tokens(cpc_val, CPC_RE),

            "earliest_priority_date": str(row.get("earliest_priority_date", "")).strip() or None,
            "publication_date": str(row.get("publication_date", "")).strip() or None,

            # keep for later if you want
            "governance_flags": [],
        }

        actions.append(json.dumps({"index": {"_index": INDEX, "_id": doc_id}}, ensure_ascii=False))
        actions.append(json.dumps(doc, ensure_ascii=False))
        sent += 1

        if sent % 300 == 0:
            bulk_ndjson(actions)
            actions = []

    if actions:
        bulk_ndjson(actions)

    # refresh so _count is correct immediately
    requests.post(f"{ES}/{INDEX}/_refresh", timeout=60)

    print(f"[ok] indexed rows={sent} into {INDEX}")


if __name__ == "__main__":
    main()
