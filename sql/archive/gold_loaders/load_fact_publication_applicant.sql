TRUNCATE TABLE gold.fact_publication_applicant;
GO

INSERT INTO gold.fact_publication_applicant (
    publication_number,
    applicant_seq,
    applicant_name_raw,
    applicant_country_code_raw
)
SELECT
    publication_number,
    applicant_seq,
    applicant_name_raw,
    applicant_country_code_raw
FROM silver.publication_applicant_raw;
GO