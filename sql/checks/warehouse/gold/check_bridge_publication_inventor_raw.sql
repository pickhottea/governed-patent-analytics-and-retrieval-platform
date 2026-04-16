SELECT TOP 30 *
FROM gold.bridge_publication_inventor_raw;
GO

SELECT publication_number, COUNT(*) AS inventor_cnt
FROM gold.bridge_publication_inventor_raw
GROUP BY publication_number
ORDER BY inventor_cnt DESC;
GO