SELECT TOP 20 *
FROM silver.rawdata_patents;
GO

SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT family_id) AS family_cnt,
    COUNT(DISTINCT publication_number) AS pub_cnt
FROM silver.rawdata_patents;
GO