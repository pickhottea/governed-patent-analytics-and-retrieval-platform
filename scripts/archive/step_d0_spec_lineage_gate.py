#!/usr/bin/env python3
import argparse
import json
import os
import sys


REQUIRED_FLAGS = {"THIRD_PARTY_SOURCE", "COVERAGE_FALLBACK"}


def is_nonempty(x):
    return isinstance(x, str) and x.strip() != ""


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                raise ValueError(f"Invalid JSON at line {i}: {e}")
    return rows


def validate(row):
    reasons = []

    if row.get("chunk_type") != "spec_fulltext":
        reasons.append("chunk_type must be spec_fulltext")

    if not is_nonempty(row.get("family_id")):
        reasons.append("missing family_id")

    if not is_nonempty(row.get("asset_id")):
        reasons.append("missing asset_id")

    if not is_nonempty(row.get("selected_publication")):
        reasons.append("missing selected_publication")

    spec_source = row.get("spec_source")
    if spec_source not in {"OPS", "GOOGLE"}:
        reasons.append("invalid spec_source")

    flags = row.get("governance_flags")
    if not isinstance(flags, list):
        reasons.append("governance_flags must be list")
    else:
        missing = REQUIRED_FLAGS - set(flags)
        if missing:
            reasons.append(f"missing flags: {','.join(missing)}")

    if spec_source == "GOOGLE":
        if not is_nonempty(row.get("spec_google_text_path")):
            reasons.append("GOOGLE missing spec_google_text_path")
        if not is_nonempty(row.get("google_status")):
            reasons.append("GOOGLE missing google_status")

    if spec_source == "OPS":
        if not is_nonempty(row.get("spec_raw_xml_path")):
            reasons.append("OPS missing spec_raw_xml_path")

    return len(reasons) == 0, reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    args = ap.parse_args()

    rows = load_jsonl(args.in_path)


    bad = []
    for r in rows:
        ok, reasons = validate(r)
        if not ok:
            bad.append((r.get("selected_publication"), reasons))

    if bad:
        print(f"FAIL: {len(bad)} invalid rows")
        for pub, reasons in bad[:20]:
            print(pub)
            for rr in reasons:
                print("  -", rr)
        sys.exit(1)

    print(f"PASS: spec lineage gate passed ({len(rows)} chunks)")
    sys.exit(0)


if __name__ == "__main__":
    main()
