/*
Purpose:
- Build gold.bridge_family_publication
- Enforce a governed family-to-publication bridge
- Prevent uncontrolled OPS-family full expansion
- Normalize OPS-derived publication identifiers before attachment

Target:
- gold.bridge_family_publication

Grain:
- 1 row = 1 family_id x 1 publication_number

Governance rules:
- family headline truth stays at family_id
- anchor rows come from silver.rawdata_patents
- OPS family is a candidate expansion source, not canonical identity
- publication identifiers must be normalized before bridging
- expanded members must pass a boundary gate
- current conservative boundary gate:
    expanded member jurisdiction must match anchor jurisdiction
*/

IF OBJECT_ID('gold.bridge_family_publication', 'U') IS NOT NULL
BEGIN
    DROP TABLE gold.bridge_family_publication;
END;
GO

;WITH anchor_side AS (
    SELECT
        rp.family_id,
        rp.publication_number AS anchor_publication_number,
        UPPER(LEFT(rp.publication_number, 2)) AS anchor_jurisdiction,
        CAST('anchor' AS VARCHAR(30)) AS member_role,
        CAST(NULL AS VARCHAR(100)) AS ops_family_cluster_id,
        CAST(1 AS BIT) AS is_bm25_representative,
        CAST('anchor_rawdata_patents' AS VARCHAR(50)) AS record_source,
        CAST(NULL AS VARCHAR(100)) AS expansion_gate_rule
    FROM silver.rawdata_patents rp
    WHERE rp.family_id IS NOT NULL
      AND rp.publication_number IS NOT NULL
),

ops_members_normalized AS (
    SELECT
        ofm.ops_family_member_key,
        ofm.ops_family_member_row_id,
        ofm.ops_family_id,
        ofm.seed_publication_number,
        ofm.seed_publication_docdb,
        ofm.family_members_count,
        ofm.member_seq_within_ops_family,
        ofm.member_publication_number,
        ofm.member_publication_docdb,
        ofm.member_jurisdiction,
        ofm.member_kind,
        ofm.source_file_name,
        ofm.ingested_at,

        UPPER(NULLIF(ofm.member_jurisdiction, '')) AS member_jurisdiction_norm,
        UPPER(NULLIF(ofm.member_kind, '')) AS member_kind_norm,

        CASE
            WHEN PATINDEX('%[0-9]%', ofm.member_publication_number) > 0
            THEN SUBSTRING(
                ofm.member_publication_number,
                PATINDEX('%[0-9]%', ofm.member_publication_number),
                LEN(ofm.member_publication_number)
            )
            WHEN PATINDEX('%[0-9]%', ofm.member_publication_docdb) > 0
            THEN SUBSTRING(
                ofm.member_publication_docdb,
                PATINDEX('%[0-9]%', ofm.member_publication_docdb),
                LEN(ofm.member_publication_docdb)
            )
            ELSE NULL
        END AS publication_tail_raw
    FROM silver.ops_family_members ofm
),

ops_members_resolved AS (
    SELECT
        om.*,

        CASE
            WHEN om.publication_tail_raw IS NULL THEN NULL
            WHEN PATINDEX('%[^0-9]%', om.publication_tail_raw) = 0
                THEN om.publication_tail_raw
            ELSE LEFT(
                om.publication_tail_raw,
                PATINDEX('%[^0-9]%', om.publication_tail_raw) - 1
            )
        END AS publication_number_numeric_part,

        CASE
            WHEN om.member_jurisdiction_norm IS NOT NULL
             AND om.member_kind_norm IS NOT NULL
             AND (
                    CASE
                        WHEN om.publication_tail_raw IS NULL THEN NULL
                        WHEN PATINDEX('%[^0-9]%', om.publication_tail_raw) = 0
                            THEN om.publication_tail_raw
                        ELSE LEFT(
                            om.publication_tail_raw,
                            PATINDEX('%[^0-9]%', om.publication_tail_raw) - 1
                        )
                    END
                 ) IS NOT NULL
            THEN
                om.member_jurisdiction_norm +
                (
                    CASE
                        WHEN om.publication_tail_raw IS NULL THEN NULL
                        WHEN PATINDEX('%[^0-9]%', om.publication_tail_raw) = 0
                            THEN om.publication_tail_raw
                        ELSE LEFT(
                            om.publication_tail_raw,
                            PATINDEX('%[^0-9]%', om.publication_tail_raw) - 1
                        )
                    END
                ) +
                om.member_kind_norm
            ELSE NULL
        END AS member_publication_number_resolved,

        COALESCE(
            om.member_jurisdiction_norm,
            LEFT(om.seed_publication_number, 2)
        ) AS member_jurisdiction_resolved
    FROM ops_members_normalized om
),

expanded_candidates AS (
    SELECT
        a.family_id,
        omr.member_publication_number_resolved AS publication_number,
        CAST('expanded_member' AS VARCHAR(30)) AS member_role,
        CAST(bfo.ops_family_cluster_id AS VARCHAR(100)) AS ops_family_cluster_id,
        CAST(0 AS BIT) AS is_bm25_representative,
        CAST('ops_family_members' AS VARCHAR(50)) AS record_source,
        CAST('same_jurisdiction_as_anchor' AS VARCHAR(100)) AS expansion_gate_rule,
        a.anchor_jurisdiction,
        omr.member_jurisdiction_resolved
    FROM anchor_side a
    INNER JOIN gold.bridge_family_ops_cluster bfo
        ON a.family_id = bfo.family_id
    INNER JOIN ops_members_resolved omr
        ON bfo.ops_family_cluster_id = omr.ops_family_id
    WHERE omr.member_publication_number_resolved IS NOT NULL
),

expanded_side AS (
    SELECT
        ec.family_id,
        ec.publication_number,
        ec.member_role,
        ec.ops_family_cluster_id,
        ec.is_bm25_representative,
        ec.record_source,
        ec.expansion_gate_rule
    FROM expanded_candidates ec
    WHERE ec.member_jurisdiction_resolved = ec.anchor_jurisdiction
),

unioned AS (
    SELECT
        a.family_id,
        a.anchor_publication_number AS publication_number,
        a.member_role,
        a.ops_family_cluster_id,
        a.is_bm25_representative,
        a.record_source,
        a.expansion_gate_rule
    FROM anchor_side a

    UNION ALL

    SELECT
        e.family_id,
        e.publication_number,
        e.member_role,
        e.ops_family_cluster_id,
        e.is_bm25_representative,
        e.record_source,
        e.expansion_gate_rule
    FROM expanded_side e
),

deduped AS (
    SELECT
        u.family_id,
        u.publication_number,
        CASE
            WHEN MAX(CASE WHEN u.member_role = 'anchor' THEN 1 ELSE 0 END) = 1
                THEN 'anchor'
            ELSE 'expanded_member'
        END AS member_role,
        MAX(u.ops_family_cluster_id) AS ops_family_cluster_id,
        CAST(
            MAX(CASE WHEN u.is_bm25_representative = 1 THEN 1 ELSE 0 END)
            AS BIT
        ) AS is_bm25_representative,
        CASE
            WHEN COUNT(DISTINCT u.record_source) > 1 THEN 'anchor+ops_expansion'
            ELSE MAX(u.record_source)
        END AS record_source,
        CASE
            WHEN MAX(CASE WHEN u.member_role = 'anchor' THEN 1 ELSE 0 END) = 1
                THEN NULL
            ELSE MAX(u.expansion_gate_rule)
        END AS expansion_gate_rule
    FROM unioned u
    GROUP BY
        u.family_id,
        u.publication_number
),

publication_collision AS (
    SELECT
        d.publication_number,
        COUNT(DISTINCT d.family_id) AS publication_family_count
    FROM deduped d
    GROUP BY
        d.publication_number
)

SELECT
    d.family_id,
    d.publication_number,
    d.member_role,
    d.ops_family_cluster_id,
    d.is_bm25_representative,
    CAST(
        CASE
            WHEN ISNULL(pc.publication_family_count, 1) > 1 THEN 1
            ELSE 0
        END
        AS BIT
    ) AS has_publication_collision,
    CASE
        WHEN ISNULL(pc.publication_family_count, 1) > 1
            THEN 'FAMILY_TO_PUBLICATION_COLLISION'
        ELSE NULL
    END AS collision_flag,
    d.record_source,
    d.expansion_gate_rule,
    SYSUTCDATETIME() AS loaded_at
INTO gold.bridge_family_publication
FROM deduped d
LEFT JOIN publication_collision pc
    ON d.publication_number = pc.publication_number;
GO