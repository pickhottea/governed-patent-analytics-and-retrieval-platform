/*
Purpose: Store raw OPS family member JSONL records.
Target: bronze.ops_family_members_raw
Grain: 1 row = 1 JSONL line = 1 seed publication family record
Warnings:
- Raw payload is preserved as-is.
- No parsing or normalization happens in Bronze.
*/

IF OBJECT_ID('bronze.ops_family_members_raw', 'U') IS NOT NULL
    DROP TABLE bronze.ops_family_members_raw;
GO

CREATE TABLE bronze.ops_family_members_raw (
    row_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_file_name NVARCHAR(260) NOT NULL,
    json_payload NVARCHAR(MAX) NOT NULL,
    ingested_at DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

SELECT TOP 10 *
FROM bronze.ops_family_members_raw
ORDER BY row_id;
GO