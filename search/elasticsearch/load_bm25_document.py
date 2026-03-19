import os
import pyodbc
from elasticsearch import Elasticsearch, helpers

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ES_INDEX", "patent_bm25_v1")

SQL_SERVER = os.getenv("SQL_SERVER", "127.0.0.1,1433")
SQL_DATABASE = os.getenv("SQL_DATABASE", "patent_analytics")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQLSERVER_SA_PASSWORD", "")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

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

SQL_QUERY = """
SELECT
    CAST(publication_number AS NVARCHAR(255)) AS doc_id,
    CAST(family_id AS NVARCHAR(255)) AS family_id,
    CAST(publication_number AS NVARCHAR(255)) AS publication_number,
    bm25_text
FROM gold.bm25_document
WHERE bm25_text IS NOT NULL
  AND LTRIM(RTRIM(bm25_text)) <> ''
"""

BATCH_SIZE = 500


def fetch_rows():
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute(SQL_QUERY)
        columns = [c[0] for c in cur.description]
        fetched_any = False

        while True:
            rows = cur.fetchmany(BATCH_SIZE)
            if not rows:
                break

            fetched_any = True
            print(f"[INFO] fetched batch rows: {len(rows)}")

            for row in rows:
                record = dict(zip(columns, row))
                yield {
                    "_index": INDEX_NAME,
                    "_id": record["doc_id"],
                    "_source": {
                        "doc_id": record["doc_id"],
                        "family_id": record["family_id"],
                        "publication_number": record["publication_number"],
                        "bm25_text": record["bm25_text"],
                    },
                }

        if not fetched_any:
            print("[WARN] SQL query returned 0 rows")


def main():
    print(f"[INFO] ES_URL: {ES_URL}")
    print(f"[INFO] INDEX_NAME: {INDEX_NAME}")
    print(f"[INFO] SQL_SERVER: {SQL_SERVER}")
    print(f"[INFO] SQL_DATABASE: {SQL_DATABASE}")

    es = Elasticsearch(ES_URL)

    success, errors = helpers.bulk(
        es,
        fetch_rows(),
        raise_on_error=False,
        stats_only=False,
    )

    print(f"[DONE] indexed docs: {success}")
    print(f"[INFO] errors count: {len(errors)}")
    if errors:
        print(errors[:3])


if __name__ == "__main__":
    main()