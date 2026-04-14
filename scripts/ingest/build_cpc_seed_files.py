from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs" / "ipc_cpc"
SEEDS_DIR = ROOT / "dbt_patent_led" / "seeds"

TITLE_DIR = DOCS_DIR / "CPCTitleList202601"
VALIDITY_TXT = DOCS_DIR / "CPCValidityFile202601" / "CPCValidityFile202601" / "CPCValidityFile202601.txt"

TITLE_OUT = SEEDS_DIR / "cpc_title_list.csv"
VALIDITY_OUT = SEEDS_DIR / "cpc_validity.csv"


def clean_text(value: str) -> str:
    value = value.replace("\ufeff", "").replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_title_files() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    txt_files = sorted(TITLE_DIR.glob("cpc-section-*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No CPC title txt files found in {TITLE_DIR}")

    for txt_file in txt_files:
        with txt_file.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.rstrip("\n\r")
                if not line.strip():
                    continue

                parts = line.split("\t")
                parts = [clean_text(p) for p in parts]

                # Expected common shapes:
                # H        ELECTRICITY
                # H01B1/00 0 Conductors ...
                # Some lines may have empty middle columns.
                if len(parts) < 2:
                    continue

                code = parts[0]
                if not code:
                    continue

                hierarchy = ""
                title = ""

                if len(parts) >= 3:
                    hierarchy = parts[1]
                    title = " ".join(p for p in parts[2:] if p)
                else:
                    title = parts[1]

                title = clean_text(title)

                if not title:
                    # Skip malformed rows with no title text
                    continue

                rows.append(
                    {
                        "cpc_code_raw": code,
                        "hierarchy_level_raw": hierarchy,
                        "title_text": title,
                        "source_file": txt_file.name,
                    }
                )

    # Deduplicate by code, keep first occurrence
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped.setdefault(row["cpc_code_raw"], row)

    return list(deduped.values())


def parse_date(value: str) -> str:
    value = clean_text(value)
    if not value:
        return ""

    # Accept common formats like YYYYMMDD, YYYY-MM-DD
    if re.fullmatch(r"\d{8}", value):
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value

    return value


def parse_validity_file() -> list[dict[str, str]]:
    if not VALIDITY_TXT.exists():
        raise FileNotFoundError(f"Validity file not found: {VALIDITY_TXT}")

    rows: list[dict[str, str]] = []

    with VALIDITY_TXT.open("r", encoding="utf-8-sig", errors="replace") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n\r")
            if not line.strip():
                continue

            parts = [clean_text(p) for p in line.split("\t")]

            # Skip header-ish rows
            joined = " ".join(parts).lower()
            if "valid from" in joined and "valid to" in joined:
                continue

            # Expect at least: symbol, from, to
            if len(parts) < 3:
                continue

            cpc_code = parts[0]
            valid_from = parse_date(parts[1])
            valid_to = parse_date(parts[2])

            if not cpc_code:
                continue

            rows.append(
                {
                    "cpc_code": cpc_code,
                    "valid_from_date": valid_from,
                    "valid_to_date": valid_to,
                }
            )

    # Deduplicate by code, keep first occurrence
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped.setdefault(row["cpc_code"], row)

    return list(deduped.values())


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    title_rows = parse_title_files()
    validity_rows = parse_validity_file()

    write_csv(
        TITLE_OUT,
        title_rows,
        ["cpc_code_raw", "hierarchy_level_raw", "title_text", "source_file"],
    )
    write_csv(
        VALIDITY_OUT,
        validity_rows,
        ["cpc_code", "valid_from_date", "valid_to_date"],
    )

    print(f"Wrote {len(title_rows)} rows -> {TITLE_OUT}")
    print(f"Wrote {len(validity_rows)} rows -> {VALIDITY_OUT}")


if __name__ == "__main__":
    main()