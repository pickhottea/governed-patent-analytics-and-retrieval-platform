/*
Purpose: Parse bronze.raw_pub_to_family_id_v2_raw into family-to-publication mapping rows.
Target: silver.raw_pub_to_family_id_v2
Grain: 1 row = 1 family_id x 1 publication_number
Warnings:
- This is a mapping support table, not canonical family truth by itself.
- It exists to support family-to-OPS alignment and downstream bridge modeling.
- publication_number here should represent the publication used for family mapping / lookup lineage.
*/

IF OBJECT_ID('silver.raw_pub_to_family_id_v2', 'U') IS NOT NULL
    DROP TABLE silver.raw_pub_to_family_id_v2;
GO

WITH parsed AS (
    SELECT
        b.row_id AS bronze_row_id,
        JSON_VALUE(b.json_payload, '$.family_id') AS family_id,
        JSON_VALUE(b.json_payload, '$.publication_number') AS publication_number,
        JSON_VALUE(b.json_payload, '$.publication_docdb') AS publication_docdb,
        JSON_VALUE(b.json_payload, '$.seed_publication_number') AS seed_publication_number,
        JSON_VALUE(b.json_payload, '$.seed_publication_docdb') AS seed_publication_docdb,
        JSON_VALUE(b.json_payload, '$.ops_family_id') AS ops_family_id,
        b.source_file_name,
        b.ingested_at
    FROM bronze.raw_pub_to_family_id_v2_raw b
),
normalized AS (
    SELECT
        bronze_row_id,
        family_id,
        publication_number,
        publication_docdb,
        seed_publication_number,
        seed_publication_docdb,
        ops_family_id,
        source_file_name,
        ingested_at
    FROM parsed
    WHERE family_id IS NOT NULL
      AND (
            publication_number IS NOT NULL
         OR seed_publication_number IS NOT NULL
      )
),
deduped AS (
    SELECT DISTINCT
        family_id,
        publication_number,
        publication_docdb,
        seed_publication_number,
        seed_publication_docdb,
        ops_family_id,
        source_file_name,
        ingested_at
    FROM normalized
)
SELECT
    family_id,
    publication_number,
    publication_docdb,
    seed_publication_number,
    seed_publication_docdb,
    ops_family_id,
    source_file_name,
    ingested_at
INTO silver.raw_pub_to_family_id_v2
FROM deduped;
GO

SELECT COUNT(*) AS row_count
FROM silver.raw_pub_to_family_id_v2;
GO

SELECT COUNT(DISTINCT family_id) AS distinct_family_id
FROM silver.raw_pub_to_family_id_v2;
GO

SELECT COUNT(DISTINCT publication_number) AS distinct_publication_number
FROM silver.raw_pub_to_family_id_v2;
GO

SELECT COUNT(DISTINCT seed_publication_number) AS distinct_seed_publication_number
FROM silver.raw_pub_to_family_id_v2;
GO

SELECT TOP 20
    family_id,
    publication_number,
    seed_publication_number,
    ops_family_id,
    publication_docdb,
    seed_publication_docdb
FROM silver.raw_pub_to_family_id_v2
ORDER BY family_id, publication_number, seed_publication_number;
GO