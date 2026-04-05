CREATE OR ALTER VIEW gold.v_family_search AS
WITH anchor_publication AS (
    SELECT
        family_id,
        MAX(CASE WHEN member_role = 'anchor' THEN publication_number END) AS selected_publication
    FROM gold.bridge_family_publication
    GROUP BY family_id
),
family_publication_agg AS (
    SELECT
        family_id,
        STRING_AGG(publication_number, ' | ') AS all_publications
    FROM gold.bridge_family_publication
    GROUP BY family_id
),
applicant_agg AS (
    SELECT
        publication_number,
        STRING_AGG(applicant_name_raw, ' | ') AS applicant
    FROM gold.fact_publication_applicant
    GROUP BY publication_number
),
inventor_agg AS (
    SELECT
        publication_number,
        STRING_AGG(inventor_name_raw, ' | ') AS inventor
    FROM gold.fact_publication_inventor
    GROUP BY publication_number
),
ipc_agg AS (
    SELECT
        publication_number,
        STRING_AGG(ipc_code, ' | ') AS ipc_codes
    FROM gold.bridge_publication_ipc
    GROUP BY publication_number
)
SELECT
    ap.family_id,
    ap.selected_publication,
    CAST(NULL AS VARCHAR(100)) AS application_number,
    aa.applicant,
    ia.inventor,
    ip.ipc_codes,
    CONVERT(VARCHAR(10), dp.earliest_priority_date, 23) AS priority_date,
    CAST(NULL AS VARCHAR(10)) AS filing_date,
    CONVERT(VARCHAR(10), dp.publication_date, 23) AS publication_date,
    fpa.all_publications
FROM anchor_publication ap
LEFT JOIN gold.dim_publication dp
    ON ap.selected_publication = dp.publication_number
LEFT JOIN applicant_agg aa
    ON ap.selected_publication = aa.publication_number
LEFT JOIN inventor_agg ia
    ON ap.selected_publication = ia.publication_number
LEFT JOIN ipc_agg ip
    ON ap.selected_publication = ip.publication_number
LEFT JOIN family_publication_agg fpa
    ON ap.family_id = fpa.family_id;
GO