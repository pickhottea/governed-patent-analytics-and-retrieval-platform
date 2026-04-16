SELECT TOP 30 *
FROM silver.publication_applicant_raw;
GO

SELECT publication_number, COUNT(*) AS applicant_cnt
FROM silver.publication_applicant_raw
GROUP BY publication_number
ORDER BY applicant_cnt DESC;
GO

SELECT applicant_country_code_raw, COUNT(*) AS cnt
FROM silver.publication_applicant_raw
GROUP BY applicant_country_code_raw
ORDER BY cnt DESC;
GO