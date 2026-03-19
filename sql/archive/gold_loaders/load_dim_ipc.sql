TRUNCATE TABLE gold.bridge_publication_ipc;
GO

DELETE FROM gold.dim_ipc;
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