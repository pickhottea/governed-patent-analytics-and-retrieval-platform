/*
Purpose:
- Provide publication-level version parsing candidates for version review.
- Current source intentionally uses dbo.dim_publication because it is populated,
  while gold.dim_publication is currently empty in the user's environment.
- Do not silently switch this source until gold.dim_publication is loaded and verified.
*/
CREATE OR ALTER VIEW gold.v_publication_version_candidate AS
WITH base AS (
    SELECT
        p.publication_number,
        UPPER(LTRIM(RTRIM(p.publication_number))) AS publication_number_norm
    FROM dbo.dim_publication p
    WHERE p.publication_number IS NOT NULL
      AND LTRIM(RTRIM(p.publication_number)) <> ''
),
finalized AS (
    SELECT
        publication_number,
        publication_number_norm,
        LEFT(publication_number_norm, 2) AS authority_code,
        CASE
            WHEN RIGHT(publication_number_norm, 2) LIKE '[A-Z][0-9]'
                THEN RIGHT(publication_number_norm, 2)
            WHEN RIGHT(publication_number_norm, 1) LIKE '[A-Z]'
                THEN RIGHT(publication_number_norm, 1)
            ELSE NULL
        END AS kind_code,
        CASE
            WHEN RIGHT(publication_number_norm, 2) LIKE '[A-Z][0-9]'
                THEN SUBSTRING(publication_number_norm, 3, LEN(publication_number_norm) - 4)
            WHEN RIGHT(publication_number_norm, 1) LIKE '[A-Z]'
                THEN SUBSTRING(publication_number_norm, 3, LEN(publication_number_norm) - 3)
            ELSE NULL
        END AS base_number
    FROM base
)
SELECT
    publication_number,
    publication_number_norm,
    authority_code,
    base_number,
    kind_code,
    LEFT(kind_code, 1) AS kind_prefix
FROM finalized;
