/*
Purpose: Build gold.bridge_family_publication
Target: gold.bridge_family_publication
Grain: 1 row = 1 family_id x 1 publication_number

Rules:
- family headline truth stays at family_id
- anchor rows come from rawdata_patents
- expanded member rows must attach through gold.bridge_family_ops_cluster
- do NOT use exact equality between anchor publication_number and seed_publication_number as the sole expansion alignment rule
*/

IF OBJECT_ID('gold.bridge_family_publication', 'U') IS NOT NULL
BEGIN
    DROP TABLE gold.bridge_family_publication;
END;
GO

;WITH anchor_side AS (
    SELECT
        rp.family_id,
        rp.publication_number,
        CAST('anchor' AS VARCHAR(30)) AS member_role,
        CAST(NULL AS VARCHAR(100)) AS ops_family_cluster_id,
        CAST(1 AS BIT) AS is_bm25_representative,
        CAST('anchor_rawdata_patents' AS VARCHAR(50)) AS record_source
    FROM silver.rawdata_patents rp
    WHERE rp.family_id IS NOT NULL
      AND rp.publication_number IS NOT NULL
),

expanded_side AS (
    SELECT
        bfo.family_id,
        COALESCE(ofm.member_publication_number, ofm.member_publication_docdb) AS publication_number,
        CAST('expanded_member' AS VARCHAR(30)) AS member_role,
        CAST(bfo.ops_family_cluster_id AS VARCHAR(100)) AS ops_family_cluster_id,
        CAST(0 AS BIT) AS is_bm25_representative,
        CAST('ops_family_members' AS VARCHAR(50)) AS record_source
    FROM gold.bridge_family_ops_cluster bfo
    INNER JOIN silver.ops_family_members ofm
        ON bfo.ops_family_cluster_id = ofm.ops_family_id
    WHERE bfo.family_id IS NOT NULL
      AND COALESCE(ofm.member_publication_number, ofm.member_publication_docdb) IS NOT NULL
),

unioned AS (
    SELECT
        family_id,
        publication_number,
        member_role,
        ops_family_cluster_id,
        is_bm25_representative,
        record_source
    FROM anchor_side

    UNION ALL

    SELECT
        family_id,
        publication_number,
        member_role,
        ops_family_cluster_id,
        is_bm25_representative,
        record_source
    FROM expanded_side
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
        CAST(MAX(CASE WHEN u.is_bm25_representative = 1 THEN 1 ELSE 0 END) AS BIT) AS is_bm25_representative,
        CASE
            WHEN COUNT(DISTINCT u.record_source) > 1 THEN 'anchor+ops_expansion'
            ELSE MAX(u.record_source)
        END AS record_source
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
    SYSUTCDATETIME() AS loaded_at
INTO gold.bridge_family_publication
FROM deduped d
LEFT JOIN publication_collision pc
    ON d.publication_number = pc.publication_number;
GO