IF OBJECT_ID('bronze.patents_canonical_raw', 'U') IS NOT NULL
    DROP TABLE bronze.patents_canonical_raw;
GO

CREATE TABLE bronze.patents_canonical_raw (
    row_id            BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_file_name  NVARCHAR(260) NOT NULL,
    json_payload      NVARCHAR(MAX) NOT NULL,
    ingested_at       DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

SELECT TOP 20 *
FROM bronze.patents_canonical_raw
ORDER BY row_id;
GO