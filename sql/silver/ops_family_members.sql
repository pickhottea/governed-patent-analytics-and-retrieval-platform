/*
Purpose: Parse bronze.ops_family_members_raw into publication-level OPS family member rows.
Target: silver.ops_family_members
Grain: 1 row = 1 seed_publication_number x 1 member_publication_docdb
Warnings:
- This is OPS expansion lineage, not dataset-family truth.
- ops_family_member_key format:
  <ops_family_id>_<member_jurisdiction><3-digit sequence within ops_family_id>
  Example: 69845166_EP001
*/

IF OBJECT_ID('silver.ops_family_members', 'U') IS NOT NULL
    DROP TABLE silver.ops_family_members;
GO

WITH parsed AS (
    SELECT
        b.row_id AS bronze_row_id,
        JSON_VALUE(b.json_payload, '$.ops_family_id') AS ops_family_id,
        JSON_VALUE(b.json_payload, '$.seed_publication_number') AS seed_publication_number,
        JSON_VALUE(b.json_payload, '$.seed_publication_docdb') AS seed_publication_docdb,
        TRY_CAST(JSON_VALUE(b.json_payload, '$.family_members_count') AS INT) AS family_members_count,
        b.source_file_name,
        b.ingested_at,
        j.publication_docdb,
        j.publication_number,
        j.jurisdiction,
        j.kind
    FROM bronze.ops_family_members_raw b
    CROSS APPLY OPENJSON(b.json_payload, '$.family_members')
    WITH (
        publication_docdb NVARCHAR(255) '$.publication_docdb',
        publication_number NVARCHAR(255) '$.publication_number',
        jurisdiction NVARCHAR(50) '$.jurisdiction."$"',
        kind NVARCHAR(50) '$.kind."$"'
    ) j
),
numbered AS (
    SELECT
        bronze_row_id,
        ops_family_id,
        seed_publication_number,
        seed_publication_docdb,
        family_members_count,
        publication_docdb AS member_publication_docdb,
        publication_number AS member_publication_number,
        jurisdiction AS member_jurisdiction,
        kind AS member_kind,
        source_file_name,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY ops_family_id
            ORDER BY jurisdiction, publication_docdb, publication_number
        ) AS member_seq_within_ops_family,
        ROW_NUMBER() OVER (
            ORDER BY ops_family_id, seed_publication_number, publication_docdb, publication_number
        ) AS ops_family_member_row_id
    FROM parsed
)
SELECT
    CONCAT(
        ISNULL(ops_family_id, 'OPS_UNKNOWN'),
        '_',
        ISNULL(member_jurisdiction, 'XX'),
        RIGHT('000' + CAST(member_seq_within_ops_family AS VARCHAR(3)), 3)
    ) AS ops_family_member_key,
    ops_family_member_row_id,
    ops_family_id,
    seed_publication_number,
    seed_publication_docdb,
    family_members_count,
    member_seq_within_ops_family,
    member_publication_docdb,
    member_publication_number,
    member_jurisdiction,
    member_kind,
    source_file_name,
    ingested_at
INTO silver.ops_family_members
FROM numbered;
GO

ALTER TABLE silver.ops_family_members
ALTER COLUMN ops_family_member_key VARCHAR(100) NOT NULL;
GO

ALTER TABLE silver.ops_family_members
ADD CONSTRAINT UQ_silver_ops_family_members_key
UNIQUE (ops_family_member_key);
GO

SELECT COUNT(*) AS row_count
FROM silver.ops_family_members;
GO

SELECT COUNT(DISTINCT seed_publication_number) AS distinct_seed_publication_number
FROM silver.ops_family_members;
GO

SELECT TOP 20
    ops_family_member_key,
    ops_family_id,
    member_seq_within_ops_family,
    member_jurisdiction,
    member_publication_number,
    member_publication_docdb
FROM silver.ops_family_members
ORDER BY ops_family_id, member_seq_within_ops_family;
GO