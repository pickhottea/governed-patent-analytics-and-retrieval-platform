/*
Purpose: Load raw publication-to-family mapping JSON records into bronze.raw_pub_to_family_id_v2_raw
Target: bronze.raw_pub_to_family_id_v2_raw
Grain: 1 row = 1 raw JSON record from raw_pub_to_family_id_v2.json
Warnings:
- This is raw landing storage.
- Do not interpret this table as canonical family truth by itself.
- Parsed / normalized use belongs in silver.raw_pub_to_family_id_v2.
*/

IF OBJECT_ID('bronze.raw_pub_to_family_id_v2_raw', 'U') IS NOT NULL
    DROP TABLE bronze.raw_pub_to_family_id_v2_raw;
GO

CREATE TABLE bronze.raw_pub_to_family_id_v2_raw (
    row_id INT IDENTITY(1,1) NOT NULL,
    json_payload NVARCHAR(MAX) NOT NULL,
    source_file_name VARCHAR(255) NOT NULL,
    ingested_at DATETIME2 NOT NULL
);
GO