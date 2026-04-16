SELECT TOP 30 *
FROM gold.fact_publication_applicant;
GO

SELECT publication_number, COUNT(*) AS applicant_cnt
FROM gold.fact_publication_applicant
GROUP BY publication_number
ORDER BY applicant_cnt DESC;
GO

SELECT applicant_country_code_raw, COUNT(*) AS cnt
FROM gold.fact_publication_applicant
GROUP BY applicant_country_code_raw
ORDER BY cnt DESC;
GO