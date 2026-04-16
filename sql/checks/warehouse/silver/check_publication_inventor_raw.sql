SELECT TOP 30 *
FROM silver.publication_inventor_raw;
GO

SELECT publication_number, COUNT(*) AS inventor_cnt
FROM silver.publication_inventor_raw
GROUP BY publication_number
ORDER BY inventor_cnt DESC;
GO

SELECT inventor_country_code_raw, COUNT(*) AS cnt
FROM silver.publication_inventor_raw
GROUP BY inventor_country_code_raw
ORDER BY cnt DESC;
GO