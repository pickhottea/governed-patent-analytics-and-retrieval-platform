TRUNCATE TABLE gold.fact_publication_inventor;
GO

INSERT INTO gold.fact_publication_inventor (
    publication_number,
    inventor_seq,
    inventor_name_raw,
    inventor_country_code_raw
)
SELECT
    publication_number,
    inventor_seq,
    inventor_name_raw,
    inventor_country_code_raw
FROM silver.publication_inventor_raw;
GO