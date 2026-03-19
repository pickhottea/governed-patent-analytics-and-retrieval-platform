IF OBJECT_ID('gold.fact_publication_inventor', 'U') IS NULL
BEGIN
    CREATE TABLE gold.fact_publication_inventor (
        publication_number           VARCHAR(255) NOT NULL,
        inventor_seq                 INT          NOT NULL,
        inventor_name_raw            NVARCHAR(500) NULL,
        inventor_country_code_raw    VARCHAR(10)  NULL,
        CONSTRAINT PK_fact_publication_inventor
            PRIMARY KEY (publication_number, inventor_seq)
    );
END
GO