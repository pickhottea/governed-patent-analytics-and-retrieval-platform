IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'gold'
)
BEGIN
    EXEC('CREATE SCHEMA gold');
END
GO

DROP TABLE IF EXISTS gold.dim_ipc;
GO

CREATE TABLE gold.dim_ipc (
    ipc_code        VARCHAR(50)   NOT NULL,
    ipc_section     VARCHAR(5)    NULL,
    ipc_class       VARCHAR(10)   NULL,
    ipc_subclass    VARCHAR(10)   NULL,
    ipc_group       VARCHAR(20)   NULL,
    ipc_subgroup    VARCHAR(20)   NULL,
    CONSTRAINT PK_dim_ipc PRIMARY KEY (ipc_code)
);
GO

INSERT INTO gold.dim_ipc (
    ipc_code,
    ipc_section,
    ipc_class,
    ipc_subclass,
    ipc_group,
    ipc_subgroup
)
SELECT DISTINCT
    ipc_token_clean AS ipc_code,
    LEFT(ipc_token_clean, 1) AS ipc_section,
    LEFT(ipc_token_clean, 3) AS ipc_class,
    LEFT(ipc_token_clean, 4) AS ipc_subclass,
    CASE
        WHEN CHARINDEX('/', ipc_token_clean) > 0
        THEN LEFT(ipc_token_clean, CHARINDEX('/', ipc_token_clean) - 1)
        ELSE NULL
    END AS ipc_group,
    CASE
        WHEN CHARINDEX('/', ipc_token_clean) > 0
        THEN SUBSTRING(
            ipc_token_clean,
            CHARINDEX('/', ipc_token_clean) + 1,
            LEN(ipc_token_clean)
        )
        ELSE NULL
    END AS ipc_subgroup
FROM silver.publication_ipc;
GO