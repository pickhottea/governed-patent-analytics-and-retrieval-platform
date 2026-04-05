/*
File: sql/silver/rawdata_patents.sql

Purpose:
- parse bronze.patents_canonical_raw json payload
- expose cleaned publication_number for downstream joins
- preserve raw publication number for traceability
*/

CREATE OR ALTER VIEW silver.rawdata_patents AS
WITH source_data AS (
    SELECT
        row_id,
        source_file_name,
        json_payload,
        ingested_at
    FROM bronze.patents_canonical_raw
),
parsed AS (
    SELECT
        src.row_id,
        src.source_file_name,
        src.ingested_at,
        src.json_payload,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.family_id'),
            JSON_VALUE(src.json_payload, '$.dataset_family_id'),
            JSON_VALUE(src.json_payload, '$.familyId'),
            JSON_VALUE(src.json_payload, '$.datasetFamilyId')
        ) AS family_id,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.publication_number'),
            JSON_VALUE(src.json_payload, '$.selected_publication'),
            JSON_VALUE(src.json_payload, '$.seed_publication_number'),
            JSON_VALUE(src.json_payload, '$.publicationNumber'),
            JSON_VALUE(src.json_payload, '$.selectedPublication'),
            JSON_VALUE(src.json_payload, '$.seedPublicationNumber')
        ) AS publication_number_raw,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.grant_number'),
            JSON_VALUE(src.json_payload, '$.grantNumber')
        ) AS grant_number,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.title'),
            JSON_VALUE(src.json_payload, '$.patent_title'),
            JSON_VALUE(src.json_payload, '$.title_text'),
            JSON_VALUE(src.json_payload, '$.titleText')
        ) AS title,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.inventors'),
            JSON_QUERY(src.json_payload, '$.inventors'),
            JSON_VALUE(src.json_payload, '$.inventor'),
            JSON_QUERY(src.json_payload, '$.inventor_names')
        ) AS inventors,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.applicants'),
            JSON_QUERY(src.json_payload, '$.applicants'),
            JSON_VALUE(src.json_payload, '$.applicant'),
            JSON_QUERY(src.json_payload, '$.applicant_names')
        ) AS applicants,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.priority_date'),
            JSON_VALUE(src.json_payload, '$.priorityDate')
        ) AS priority_date_raw,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.application_date'),
            JSON_VALUE(src.json_payload, '$.applicationDate')
        ) AS application_date_raw,

        COALESCE(
            JSON_VALUE(src.json_payload, '$.publication_date'),
            JSON_VALUE(src.json_payload, '$.publicationDate')
        ) AS publication_date_raw
    FROM source_data src
)
SELECT
    p.family_id,

    p.publication_number_raw,

    UPPER(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                LTRIM(RTRIM(p.publication_number_raw)),
                                CHAR(9), ''
                            ),
                            CHAR(10), ''
                        ),
                        CHAR(13), ''
                    ),
                    NCHAR(160), ''
                ),
                '.',''
            ),
            ' ',''
        )
    ) AS publication_number,

    UPPER(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                LTRIM(RTRIM(p.publication_number_raw)),
                                CHAR(9), ''
                            ),
                            CHAR(10), ''
                        ),
                        CHAR(13), ''
                    ),
                    NCHAR(160), ''
                ),
                '.',''
            ),
            ' ',''
        )
    ) AS publication_number_norm,

    p.grant_number,
    p.title,
    p.inventors,
    p.applicants,

    TRY_CONVERT(date, p.priority_date_raw) AS priority_date,
    TRY_CONVERT(date, p.application_date_raw) AS application_date,
    TRY_CONVERT(date, p.publication_date_raw) AS publication_date,

    p.source_file_name,
    p.ingested_at,
    p.row_id,
    p.json_payload
FROM parsed p
WHERE p.family_id IS NOT NULL
  AND p.publication_number_raw IS NOT NULL;
GO