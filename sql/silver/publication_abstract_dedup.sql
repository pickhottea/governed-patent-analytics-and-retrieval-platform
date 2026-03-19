IF OBJECT_ID('silver.publication_abstract_dedup', 'U') IS NOT NULL
    DROP TABLE silver.publication_abstract_dedup;
GO

WITH ranked AS (
    SELECT
        publication_number,
        family_id,
        title_jsonl,
        abstract_jsonl,
        source_file_name,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY publication_number
            ORDER BY
                CASE
                    WHEN abstract_jsonl IS NOT NULL
                     AND LTRIM(RTRIM(abstract_jsonl)) <> '' THEN 0
                    ELSE 1
                END,
                ingested_at DESC
        ) AS rn
    FROM silver.publication_abstract
)
SELECT
    publication_number,
    family_id,
    title_jsonl,
    abstract_jsonl,
    source_file_name,
    ingested_at
INTO silver.publication_abstract_dedup
FROM ranked
WHERE rn = 1;
GO

SELECT COUNT(*) AS row_count
FROM silver.publication_abstract_dedup;
GO

SELECT TOP 20 *
FROM silver.publication_abstract_dedup
ORDER BY publication_number;
GO