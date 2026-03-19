TRUNCATE TABLE gold.bridge_publication_inventor_raw;
GO

INSERT INTO gold.bridge_publication_inventor_raw (
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