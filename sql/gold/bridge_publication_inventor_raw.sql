IF OBJECT_ID('gold.bridge_publication_inventor_raw', 'U') IS NULL
BEGIN
    CREATE TABLE gold.bridge_publication_inventor_raw (
        publication_number           VARCHAR(255) NOT NULL,
        inventor_seq                 INT          NOT NULL,
        inventor_name_raw            NVARCHAR(500) NULL,
        inventor_country_code_raw    VARCHAR(10)  NULL,
        CONSTRAINT PK_bridge_publication_inventor_raw
            PRIMARY KEY (publication_number, inventor_seq)
    );
END
GO