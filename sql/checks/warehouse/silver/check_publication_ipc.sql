SELECT TOP 50 *
FROM silver.publication_ipc;
GO

SELECT COUNT(*) AS row_count
FROM silver.publication_ipc;
GO

SELECT publication_number, COUNT(*) AS ipc_cnt
FROM silver.publication_ipc
GROUP BY publication_number
ORDER BY ipc_cnt DESC;
GO