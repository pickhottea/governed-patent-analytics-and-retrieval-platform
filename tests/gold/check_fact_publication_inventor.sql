SELECT TOP 30 *
FROM gold.fact_publication_inventor;
GO

SELECT publication_number, COUNT(*) AS inventor_cnt
FROM gold.fact_publication_inventor
GROUP BY publication_number
ORDER BY inventor_cnt DESC;
GO

SELECT inventor_country_code_raw, COUNT(*) AS cnt
FROM gold.fact_publication_inventor
GROUP BY inventor_country_code_raw
ORDER BY cnt DESC;
GO