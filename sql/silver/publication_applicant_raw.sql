DROP VIEW IF EXISTS silver.publication_applicant_raw;
GO

CREATE VIEW silver.publication_applicant_raw AS
WITH applicant_base AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM(applicants)) AS applicant_text
    FROM silver.rawdata_patents
    WHERE NULLIF(LTRIM(RTRIM(applicants)), '') IS NOT NULL
),
applicant_norm AS (
    SELECT
        family_id,
        publication_number,
        LTRIM(RTRIM(
            REPLACE(
                REPLACE(
                    REPLACE(applicant_text, CHAR(13), ' '),
                    CHAR(10), ' '
                ),
                '_x000D_', ' '
            )
        )) AS applicant_text
    FROM applicant_base
),
applicant_delimited AS (
    SELECT
        family_id,
        publication_number,
        REPLACE(applicant_text, '] ', ']|') AS applicant_text_delimited
    FROM applicant_norm
),
applicant_json AS (
    SELECT
        family_id,
        publication_number,
        '["' +
        REPLACE(
            REPLACE(applicant_text_delimited, '"', '\"'),
            '|',
            '","'
        ) +
        '"]' AS applicant_json_array
    FROM applicant_delimited
),
applicant_split AS (
    SELECT
        j.family_id,
        j.publication_number,
        CAST([key] AS INT) + 1 AS applicant_seq,
        LTRIM(RTRIM([value])) AS applicant_raw
    FROM applicant_json j
    CROSS APPLY OPENJSON(j.applicant_json_array)
)
SELECT
    family_id,
    publication_number,
    applicant_seq,
    applicant_raw,
    CASE
        WHEN RIGHT(applicant_raw, 1) = ']'
             AND CHARINDEX('[', REVERSE(applicant_raw)) > 0
        THEN LTRIM(RTRIM(
            LEFT(
                applicant_raw,
                LEN(applicant_raw) - CHARINDEX('[', REVERSE(applicant_raw))
            )
        ))
        ELSE applicant_raw
    END AS applicant_name_raw,
    CASE
        WHEN RIGHT(applicant_raw, 1) = ']'
             AND CHARINDEX('[', REVERSE(applicant_raw)) > 0
        THEN SUBSTRING(
            applicant_raw,
            LEN(applicant_raw) - CHARINDEX('[', REVERSE(applicant_raw)) + 2,
            2
        )
        ELSE NULL
    END AS applicant_country_code_raw
FROM applicant_split
WHERE NULLIF(LTRIM(RTRIM(applicant_raw)), '') IS NOT NULL;
GO