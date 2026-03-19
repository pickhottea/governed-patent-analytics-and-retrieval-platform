IF OBJECT_ID('gold.bm25_document', 'U') IS NOT NULL
    DROP TABLE gold.bm25_document;
GO

SELECT
    a.publication_number,
    a.family_id,
    a.title_jsonl AS title,
    a.abstract_jsonl AS abstract,
    CONCAT(
        COALESCE(a.title_jsonl, ''),
        CASE
            WHEN a.abstract_jsonl IS NOT NULL
             AND LTRIM(RTRIM(a.abstract_jsonl)) <> ''
                THEN N' ' + a.abstract_jsonl
            ELSE N''
        END
    ) AS bm25_text,
    CAST('title_abstract' AS VARCHAR(30)) AS retrieval_mode,
    SYSUTCDATETIME() AS loaded_at
INTO gold.bm25_document
FROM silver.publication_abstract_dedup a;
GO

SELECT COUNT(*) AS row_count
FROM gold.bm25_document;
GO

SELECT
    SUM(CASE WHEN title IS NULL OR LTRIM(RTRIM(title)) = '' THEN 1 ELSE 0 END) AS missing_title,
    SUM(CASE WHEN abstract IS NULL OR LTRIM(RTRIM(abstract)) = '' THEN 1 ELSE 0 END) AS missing_abstract,
    SUM(CASE WHEN bm25_text IS NULL OR LTRIM(RTRIM(bm25_text)) = '' THEN 1 ELSE 0 END) AS empty_bm25_text
FROM gold.bm25_document;
GO

SELECT TOP 20 *
FROM gold.bm25_document
ORDER BY publication_number;
GO