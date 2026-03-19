IF OBJECT_ID('silver.publication_abstract', 'U') IS NOT NULL
    DROP TABLE silver.publication_abstract;
GO

SELECT
    JSON_VALUE(b.json_payload, '$.publication_number') AS publication_number,
    JSON_VALUE(b.json_payload, '$.family_id')          AS family_id,
    JSON_VALUE(b.json_payload, '$.title')              AS title_jsonl,
    JSON_VALUE(b.json_payload, '$.abstract')           AS abstract_jsonl,
    b.source_file_name,
    b.ingested_at
INTO silver.publication_abstract
FROM bronze.patents_canonical_raw b
WHERE JSON_VALUE(b.json_payload, '$.publication_number') IS NOT NULL;
GO

SELECT COUNT(*) AS row_count
FROM silver.publication_abstract;
GO

SELECT TOP 20 *
FROM silver.publication_abstract
ORDER BY publication_number;
GO