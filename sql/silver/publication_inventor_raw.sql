DROP VIEW IF EXISTS silver.publication_inventor_raw;
GO

CREATE VIEW silver.publication_inventor_raw AS
WITH inventor_base AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM(inventors)) AS inventor_text
    FROM silver.rawdata_patents
    WHERE NULLIF(LTRIM(RTRIM(inventors)), '') IS NOT NULL
),
inventor_norm AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM(
            REPLACE(
                REPLACE(
                    REPLACE(inventor_text, CHAR(13), ' '),
                    CHAR(10), ' '
                ),
                '_x000D_', ' '
            )
        )) AS inventor_text
    FROM inventor_base
),
inventor_delimited AS (
    SELECT
        family_id,
        publication_number,
        REPLACE(inventor_text, '] ', ']|') AS inventor_text_delimited
    FROM inventor_norm
),
inventor_json AS (
    SELECT
        family_id,
        publication_number,
        '["' +
        REPLACE(
            REPLACE(inventor_text_delimited, '"', '\"'),
            '|',
            '","'
        ) +
        '"]' AS inventor_json_array
    FROM inventor_delimited
),
inventor_split AS (
    SELECT
        j.family_id,
        j.publication_number,
        CAST([key] AS INT) + 1 AS inventor_seq,
        LTRIM(RTRIM([value])) AS inventor_raw
    FROM inventor_json j
    CROSS APPLY OPENJSON(j.inventor_json_array)
)
SELECT
    family_id,
    publication_number,
    inventor_seq,
    inventor_raw,
    CASE
        WHEN RIGHT(inventor_raw, 1) = ']'
             AND CHARINDEX('[', REVERSE(inventor_raw)) > 0
        THEN LTRIM(RTRIM(
            LEFT(
                inventor_raw,
                LEN(inventor_raw) - CHARINDEX('[', REVERSE(inventor_raw))
            )
        ))
        ELSE inventor_raw
    END AS inventor_name_raw,
    CASE
        WHEN RIGHT(inventor_raw, 1) = ']'
             AND CHARINDEX('[', REVERSE(inventor_raw)) > 0
        THEN SUBSTRING(
            inventor_raw,
            LEN(inventor_raw) - CHARINDEX('[', REVERSE(inventor_raw)) + 2,
            2
        )
        ELSE NULL
    END AS inventor_country_code_raw
FROM inventor_split
WHERE NULLIF(LTRIM(RTRIM(inventor_raw)), '') IS NOT NULL;
GO