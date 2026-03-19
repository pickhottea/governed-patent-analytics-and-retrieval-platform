from pathlib import Path
import os
import json
import pyodbc

PROJECT_ROOT = Path("/home/pickhottea/project3/patent_led")
JSONL_PATH = PROJECT_ROOT / "data" / "raw" / "retrieval" / "patents_canonical.jsonl"

SQL_SERVER = os.getenv("SQL_SERVER", "127.0.0.1,1433")
SQL_DATABASE = os.getenv("SQL_DATABASE", "patent_analytics")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQLSERVER_SA_PASSWORD", "")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

TARGET_TABLE = "bronze.patents_canonical_raw"
SOURCE_FILE_NAME = "patents_canonical.jsonl"
BATCH_SIZE = 1000

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
    json_payload
)
VALUES (?, ?)
"""

truncate_sql = f"TRUNCATE TABLE {TARGET_TABLE}"


def validate_json_line(line: str, line_number: int) -> str:
    try:
        obj = json.loads(line)
        return json.dumps(obj, ensure_ascii=False)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON at line {line_number}: {e}") from e


def chunked(iterable, size: int):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def read_jsonl_rows(jsonl_path: Path):
    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            normalized_json = validate_json_line(line, line_number)
            yield (SOURCE_FILE_NAME, normalized_json)


def main():
    print(f"[INFO] JSONL path: {JSONL_PATH}")
    print(f"[INFO] JSONL exists: {JSONL_PATH.exists()}")
    print(f"[INFO] SQL_SERVER: {SQL_SERVER}")
    print(f"[INFO] SQL_DATABASE: {SQL_DATABASE}")
    print(f"[INFO] SQL_USERNAME: {SQL_USERNAME}")
    print(f"[INFO] SQL_DRIVER: {SQL_DRIVER}")
    print(f"[INFO] SQL password loaded: {'YES' if bool(SQL_PASSWORD) else 'NO'}")
    print(f"[INFO] Target table: {TARGET_TABLE}")

    rows_inserted = 0

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        print("[INFO] Truncating target table...")
        cursor.execute(truncate_sql)
        conn.commit()



        print("[INFO] Loading JSONL into bronze table...")

        for batch in chunked(read_jsonl_rows(JSONL_PATH), BATCH_SIZE):
            cursor.executemany(insert_sql, batch)
            conn.commit()
            rows_inserted += len(batch)
            print(f"[INFO] Inserted rows: {rows_inserted}")

    print(f"[DONE] Finished loading {rows_inserted} rows into {TARGET_TABLE}")


if __name__ == "__main__":
    main()