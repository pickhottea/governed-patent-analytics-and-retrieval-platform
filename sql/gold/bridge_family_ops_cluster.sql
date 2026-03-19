/*
Purpose: Build gold.bridge_family_ops_cluster as the family-to-OPS mapping layer.
Target: gold.bridge_family_ops_cluster
Grain: 1 row = 1 family_id x 1 ops_family_cluster_id
Warnings:
- This is a mapping layer, not a canonical identity table.
- ops_family_cluster_id must not replace family_id.
- This script assumes a parsed family mapping source exists from raw_pub_to_family_id_v2.
- Do not use exact equality between anchor publication_number and seed_publication_number as the sole mapping contract here.
*/

IF OBJECT_ID('gold.bridge_family_ops_cluster', 'U') IS NOT NULL
BEGIN
    DROP TABLE gold.bridge_family_ops_cluster;
END;
GO

;WITH family_mapping_source AS (
    /* ---------------------------------------------------------
       Replace this source table name if your parsed mapping
       table uses a different actual name.

       Expected minimum columns from parsed mapping source:
       - family_id
       - publication_number

       Recommended source:
       - silver.raw_pub_to_family_id_v2
       --------------------------------------------------------- */
    SELECT DISTINCT
        m.family_id,
        m.seed_publication_number
    FROM silver.raw_pub_to_family_id_v2 m
    WHERE m.family_id IS NOT NULL
    AND m.seed_publication_number IS NOT NULL
),

ops_seed_cluster AS (
    SELECT DISTINCT
        ofm.ops_family_id AS ops_family_cluster_id,
        ofm.seed_publication_number
    FROM silver.ops_family_members ofm
    WHERE ofm.ops_family_id IS NOT NULL
      AND ofm.seed_publication_number IS NOT NULL
),

mapped_family_ops_cluster AS (
    SELECT DISTINCT
        fms.family_id,
        osc.ops_family_cluster_id,
        CAST('source_attached' AS VARCHAR(50)) AS mapping_method,
        CAST('high' AS VARCHAR(20)) AS mapping_confidence,
        CAST('raw_pub_to_family_id_v2+ops_family_members' AS VARCHAR(100)) AS record_source
    FROM family_mapping_source fms
    INNER JOIN ops_seed_cluster osc
        ON fms.seed_publication_number = osc.seed_publication_number
)

SELECT
    m.family_id,
    m.ops_family_cluster_id,
    m.mapping_method,
    m.mapping_confidence,
    m.record_source,
    SYSUTCDATETIME() AS loaded_at
INTO gold.bridge_family_ops_cluster
FROM mapped_family_ops_cluster m;
GO