CREATE OR ALTER VIEW gold.v_bm25_publication_metadata AS
WITH applicant_agg AS (
    SELECT
        publication_number,
        STRING_AGG(applicant_name_raw, ' | ') AS applicant
    FROM gold.fact_publication_applicant
    GROUP BY publication_number
),
ipc_agg AS (
    SELECT
        publication_number,
        STRING_AGG(ipc_code, ' | ') AS ipc_codes
    FROM gold.bridge_publication_ipc
    GROUP BY publication_number
),
title_lookup AS (
    SELECT
        publication_number,
        MAX(title_jsonl) AS title
    FROM silver.publication_abstract_dedup
    GROUP BY publication_number
)
SELECT
    b.publication_number,
    b.family_id,
    aa.applicant,
    ip.ipc_codes,
    tl.title
FROM gold.bm25_document b
LEFT JOIN applicant_agg aa
    ON b.publication_number = aa.publication_number
LEFT JOIN ipc_agg ip
    ON b.publication_number = ip.publication_number
LEFT JOIN title_lookup tl
    ON b.publication_number = tl.publication_number;
GO