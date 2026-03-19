DROP VIEW IF EXISTS silver.publication_ipc;
GO

CREATE VIEW silver.publication_ipc AS
WITH ipc_base AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM(
            REPLACE(REPLACE(REPLACE(REPLACE(ipc, CHAR(13), ' '), CHAR(10), ' '), ';', ' '), ',', ' ')
        )) AS ipc_text
    FROM silver.rawdata_patents
    WHERE ipc IS NOT NULL
),
ipc_json AS (
    SELECT
        family_id,
        publication_number,
        '["' +
        REPLACE(
            REPLACE(
                REPLACE(ipc_text, '"', '\"'),
                '  ', ' '
            ),
            ' ',
            '","'
        ) +
        '"]' AS ipc_json_array
    FROM ipc_base
),
ipc_split AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM([value])) AS ipc_raw_token
    FROM ipc_json
    CROSS APPLY OPENJSON(ipc_json_array)
)
SELECT
    family_id,
    publication_number,
    ipc_raw_token,
    UPPER(ipc_raw_token) AS ipc_token_clean
FROM ipc_split
WHERE NULLIF(LTRIM(RTRIM(ipc_raw_token)), '') IS NOT NULL;
GO