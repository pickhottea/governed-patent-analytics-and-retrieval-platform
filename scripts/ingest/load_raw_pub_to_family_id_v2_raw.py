from pathlib import Path
import os
import json
import pyodbc

PROJECT_ROOT = Path("/home/pickhottea/project3/patent_led")
JSON_PATH = PROJECT_ROOT / "data" / "raw" / "expansion" / "raw_pub_to_family_id_v2.json"

SQL_SERVER = os.getenv("SQL_SERVER", "127.0.0.1,1433")
SQL_DATABASE = os.getenv("SQL_DATABASE", "patent_analytics")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQLSERVER_SA_PASSWORD", "")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

TARGET_TABLE = "bronze.raw_pub_to_family_id_v2_raw"
SOURCE_FILE_NAME = "raw_pub_to_family_id_v2.json"
BATCH_SIZE = 500

if not SQL_PASSWORD:
    raise ValueError("Missing environment variable: SQLSERVER_SA_PASSWORD")

conn_str = (
    f"DRIVER={{{SQL_DRIVER}}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)

insert_sql = f"""
INSERT INTO {TARGET_TABLE} (
    source_file_name,
    json_payload,
    ingested_at
)
VALUES (?, ?, SYSUTCDATETIME())
"""

truncate_sql = f"TRUNCATE TABLE {TARGET_TABLE}"


def chunked(iterable, size: int):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def normalize_record(pub_key: str, value):
    """
    Expand root-level dict entries into row-level JSON records.

    Supported examples:
    - {"EP123A1": "71103201"}
    - {"EP123A1": {"family_id": "71103201", "ops_family_id": "69845166"}}
    - {"EP123A1": [{"family_id": "71103201"}, {"family_id": "71103201"}]}
    """
    rows = []

    # Case 1: value is just family_id string/int
    if isinstance(value, (str, int, float, bool)) or value is None:
        rec = {
            "publication_number": str(pub_key),
            "seed_publication_number": str(pub_key),
            "family_id": None if value is None else str(value)
        }
        rows.append(rec)
        return rows

    # Case 2: value is dict
    if isinstance(value, dict):
        rec = dict(value)

        if "publication_number" not in rec or not rec.get("publication_number"):
            rec["publication_number"] = str(pub_key)

        if "seed_publication_number" not in rec or not rec.get("seed_publication_number"):
            rec["seed_publication_number"] = str(pub_key)

        # common alias cleanup
        if "family_id" not in rec:
            for k in ("docdb_family_id", "familyId", "family"):
                if k in rec and rec[k] is not None:
                    rec["family_id"] = str(rec[k])
                    break

        rows.append(rec)
        return rows

    # Case 3: value is list
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                rec = dict(item)

                if "publication_number" not in rec or not rec.get("publication_number"):
                    rec["publication_number"] = str(pub_key)

                if "seed_publication_number" not in rec or not rec.get("seed_publication_number"):
                    rec["seed_publication_number"] = str(pub_key)

                if "family_id" not in rec:
                    for k in ("docdb_family_id", "familyId", "family"):
                        if k in rec and rec[k] is not None:
                            rec["family_id"] = str(rec[k])
                            break

                rows.append(rec)
            else:
                rec = {
                    "publication_number": str(pub_key),
                    "seed_publication_number": str(pub_key),
                    "family_id": None if item is None else str(item)
                }
                rows.append(rec)
        return rows

    raise ValueError(f"Unsupported JSON value type under key {pub_key}: {type(value).__name__}")


def read_json_rows(json_path: Path):
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    raw = json.loads(json_path.read_text(encoding="utf-8"))

    # root array
    if isinstance(raw, list):
        for obj in raw:
            yield (SOURCE_FILE_NAME, json.dumps(obj, ensure_ascii=False))
        return

    # root dict -> EXPAND
    if isinstance(raw, dict):
        for pub_key, value in raw.items():
            for rec in normalize_record(pub_key, value):
                yield (SOURCE_FILE_NAME, json.dumps(rec, ensure_ascii=False))
        return

    raise ValueError(f"Unsupported root JSON structure: {type(raw).__name__}")


def main():
    print(f"[INFO] JSON path: {JSON_PATH}")
    print(f"[INFO] JSON exists: {JSON_PATH.exists()}")
    print(f"[INFO] SQL_SERVER: {SQL_SERVER}")
    print(f"[INFO] SQL_DATABASE: {SQL_DATABASE}")
    print(f"[INFO] Target table: {TARGET_TABLE}")

    rows_inserted = 0

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        print("[INFO] Truncating target table...")
        cursor.execute(truncate_sql)
        conn.commit()

        print("[INFO] Loading JSON into bronze table...")

        for batch in chunked(read_json_rows(JSON_PATH), BATCH_SIZE):
            cursor.executemany(insert_sql, batch)
            conn.commit()
            rows_inserted += len(batch)
            print(f"[INFO] Inserted rows: {rows_inserted}")

    print(f"[DONE] Finished loading {rows_inserted} rows into {TARGET_TABLE}")


if __name__ == "__main__":
    main()