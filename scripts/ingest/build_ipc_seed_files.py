from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs" / "ipc_cpc"
SEEDS_DIR = ROOT / "dbt_patent_led" / "seeds"

TITLE_DIR = DOCS_DIR / "EN_ipc_title_list_20260101"
TITLE_OUT = SEEDS_DIR / "ipc_title_list.csv"


def clean_text(value: str) -> str:
    value = value.replace("\ufeff", "").replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_title_files() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    txt_files = sorted(TITLE_DIR.glob("EN_ipc_section_*_title_list_20260101.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No IPC title txt files found in {TITLE_DIR}")

    for txt_file in txt_files:
        with txt_file.open("r", encoding="utf-8-sig", errors="replace") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n\r")
                if not line.strip():
                    continue

                parts = [clean_text(p) for p in line.split("\t")]
                if len(parts) < 2:
                    continue

                ipc_code = parts[0]
                if not ipc_code:
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
                    continue

                rows.append(
                    {
                        "ipc_code_raw": ipc_code,
                        "hierarchy_level_raw": hierarchy,
                        "title_text": title,
                        "source_file": txt_file.name,
                    }
                )

    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped.setdefault(row["ipc_code_raw"], row)

    return list(deduped.values())


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    title_rows = parse_title_files()

    write_csv(
        TITLE_OUT,
        title_rows,
        ["ipc_code_raw", "hierarchy_level_raw", "title_text", "source_file"],
    )

    print(f"Wrote {len(title_rows)} rows -> {TITLE_OUT}")


if __name__ == "__main__":
    main()