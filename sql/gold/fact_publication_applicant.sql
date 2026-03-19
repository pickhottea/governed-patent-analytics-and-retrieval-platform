IF OBJECT_ID('gold.fact_publication_applicant', 'U') IS NULL
BEGIN
    CREATE TABLE gold.fact_publication_applicant (
        publication_number           VARCHAR(255) NOT NULL,
        applicant_seq                INT          NOT NULL,
        applicant_name_raw           NVARCHAR(500) NULL,
        applicant_country_code_raw   VARCHAR(10)  NULL,
        CONSTRAINT PK_fact_publication_applicant
            PRIMARY KEY (publication_number, applicant_seq)
    );
END
GO