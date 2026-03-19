IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'silver'
)
BEGIN
    EXEC('CREATE SCHEMA silver');
END
GO

DROP VIEW IF EXISTS silver.rawdata_patents;
GO

CREATE VIEW silver.rawdata_patents AS
SELECT
    CAST(family_id AS VARCHAR(255)) AS family_id,
    NULLIF(LTRIM(RTRIM(publication_number)), '') AS publication_number,
    NULLIF(LTRIM(RTRIM(grant_number)), '') AS grant_number,
    NULLIF(LTRIM(RTRIM(title)), '') AS title,

    NULLIF(
        LTRIM(RTRIM(
            REPLACE(REPLACE(REPLACE(inventors, '_x000D_', ' '), CHAR(13), ' '), CHAR(10), ' ')
        )),
        ''
    ) AS inventors,

    NULLIF(
        LTRIM(RTRIM(
            REPLACE(REPLACE(REPLACE(applicants, '_x000D_', ' '), CHAR(13), ' '), CHAR(10), ' ')
        )),
        ''
    ) AS applicants,

    TRY_CONVERT(DATE, earliest_priority_date) AS earliest_priority_date,

    NULLIF(
        LTRIM(RTRIM(
            REPLACE(REPLACE(REPLACE(ipc, '_x000D_', ' '), CHAR(13), ' '), CHAR(10), ' ')
        )),
        ''
    ) AS ipc,

    NULLIF(
        LTRIM(RTRIM(
            REPLACE(REPLACE(REPLACE(cpc, '_x000D_', ' '), CHAR(13), ' '), CHAR(10), ' ')
        )),
        ''
    ) AS cpc,

    TRY_CONVERT(DATE, publication_date) AS publication_date,
    TRY_CONVERT(DATE, earliest_publication) AS earliest_publication
FROM bronze.rawdata_patents;
GO





