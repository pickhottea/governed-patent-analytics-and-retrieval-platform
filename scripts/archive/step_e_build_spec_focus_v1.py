#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# Keep patterns (high-value)
DEF_PAT = re.compile(r"\b(as used herein|defined as|refers to|means\b|the term)\b", re.I)
SUM_PAT = re.compile(r"\b(problem|solution|advantage|improve|improved|reduce|reducing|efficiency)\b", re.I)
EMB_PAT = re.compile(r"\b(in one embodiment|in some embodiments|embodiment|variant|alternative)\b", re.I)

# Drop patterns (low semantic density / noise)
FIG_PAT = re.compile(r"\b(fig\.|figure|is a side view of|is a view of|illustrates)\b", re.I)
CLAIMISH_PAT = re.compile(r"\bcomprising\b\s*:?", re.I)


def classify(text: str) -> str | None:
    t = text or ""
    if not t.strip():
        return None
    if FIG_PAT.search(t):
        return None
    # if the chunk is basically claim-ish, drop it from focus
    if CLAIMISH_PAT.search(t) and len(t) < 400:
        return None

    if DEF_PAT.search(t):
        return "spec_def"
    if EMB_PAT.search(t):
        return "spec_embodiment"
    if SUM_PAT.search(t):
        return "spec_summary"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="artifacts/chunks_spec_all_v1.jsonl")
    ap.add_argument("--out", default="artifacts/chunks_spec_focus_v1.jsonl")
    args = ap.parse_args()

    rows = load_jsonl(args.in_path)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    kept = 0
    total = 0

    with out_path.open("w", encoding="utf-8") as out:
        for r in rows:
            total += 1
            text = str(r.get("text") or "")
            c = classify(text)
            if c is None:
                continue

            # ensure chunk_id exists
            base = r.get("chunk_id")
            if not isinstance(base, str) or not base.strip():
                pub = str(r.get("selected_publication") or "")
                base = sha1(f"spec|{pub}|{sha1(text)}")

            rec = dict(r)
            rec["chunk_type"] = c
            rec["chunk_id"] = sha1(f"{base}|focus|{c}")  # stable derived id
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            kept += 1

    print(f"[done] wrote {out_path}")
    print(f"  total_in={total} kept_focus={kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
