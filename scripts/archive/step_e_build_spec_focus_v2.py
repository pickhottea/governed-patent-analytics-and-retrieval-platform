#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# If paragraph markers like [0001]
PARA_RX = re.compile(r"\[(\d{4})\]")

# Hard exclude topic blocks in focus layer
EXCLUDE_TOPIC = re.compile(
    r"\b(technical field|background|field of|description of related art)\b",
    re.I,
)

# Also exclude "summary" blocks that are just problem statement soup
EXCLUDE_SUMMARY_OPEN = re.compile(r"^\s*(summary|brief summary)\b", re.I)

# Keep only “explanatory / structural” style sentences
KEEP_EXPLAIN = re.compile(
    r"\b(is|are|includes?|comprises?|has|have|formed|provided|arranged|disposed|mounted|coupled|connected|configured)\b",
    re.I,
)

def load_jsonl(p: str) -> List[Dict[str, Any]]:
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def get_para_minmax(text: str) -> Tuple[int | None, int | None]:
    nums = [int(x) for x in PARA_RX.findall(text or "")]
    if not nums:
        return (None, None)
    return (min(nums), max(nums))

def is_focus_candidate(chunk_type: str) -> bool:
    return chunk_type in {"spec_def", "spec_embodiment", "spec_summary"}

def decide_keep(row: Dict[str, Any]) -> bool:
    txt = (row.get("text") or "").strip()
    if not txt:
        return False

    # Exclude early paragraphs like [0001]-[0005] which are almost always TF/BG
    pmin, _ = get_para_minmax(txt)
    if pmin is not None and pmin <= 5:
        return False

    low = txt.lower()

    # Exclude technical field / background blocks
    if EXCLUDE_TOPIC.search(low):
        return False

    # Exclude summary openers (too generic)
    if EXCLUDE_SUMMARY_OPEN.search(low):
        return False

    # Keep only if it has explanatory verbs (more likely to define/describe components)
    if not KEEP_EXPLAIN.search(txt):
        return False

    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default="artifacts/chunks_spec_all_v1.jsonl")
    ap.add_argument("--out", default="artifacts/chunks_spec_focus_v2.jsonl")
    args = ap.parse_args()

    rows = load_jsonl(args.in_path)

    kept = 0
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    with outp.open("w", encoding="utf-8") as out:
        for r in rows:
            ct = r.get("chunk_type")
            if not is_focus_candidate(str(ct or "")):
                continue
            if not decide_keep(r):
                continue
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            kept += 1

    print("[done] wrote", outp)
    print("  total_in =", len(rows), "kept_focus =", kept)

if __name__ == "__main__":
    main()
