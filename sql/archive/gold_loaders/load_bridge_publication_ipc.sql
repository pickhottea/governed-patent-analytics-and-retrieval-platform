TRUNCATE TABLE gold.bridge_publication_ipc;
GO

INSERT INTO gold.bridge_publication_ipc (
    publication_number,
    ipc_code
)
SELECT DISTINCT
    publication_number,
    ipc_token_clean AS ipc_code
FROM silver.publication_ipc;
GO