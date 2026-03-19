/*
Purpose: Validate gold.bridge_family_ops_cluster.
Target: gold.bridge_family_ops_cluster
Grain: 1 row = 1 family_id x 1 ops_family_cluster_id
Warnings:
- Run bridge_family_ops_cluster.sql first.
*/

IF OBJECT_ID('gold.bridge_family_ops_cluster', 'U') IS NULL
BEGIN
    THROW 50003, 'gold.bridge_family_ops_cluster does not exist. Run bridge_family_ops_cluster.sql first.', 1;
END;
GO

/* 1) row count */
SELECT COUNT(*) AS row_count
FROM gold.bridge_family_ops_cluster;
GO

/* 2) distinct families mapped */
SELECT COUNT(DISTINCT family_id) AS distinct_family_id
FROM gold.bridge_family_ops_cluster;
GO

/* 3) distinct OPS clusters mapped */
SELECT COUNT(DISTINCT ops_family_cluster_id) AS distinct_ops_family_cluster_id
FROM gold.bridge_family_ops_cluster;
GO

/* 4) duplicate grain check: should return 0 rows */
SELECT
    family_id,
    ops_family_cluster_id,
    COUNT(*) AS duplicate_count
FROM gold.bridge_family_ops_cluster
GROUP BY
    family_id,
    ops_family_cluster_id
HAVING COUNT(*) > 1;
GO

/* 5) family -> multiple OPS clusters */
SELECT
    family_id,
    COUNT(DISTINCT ops_family_cluster_id) AS ops_cluster_count
FROM gold.bridge_family_ops_cluster
GROUP BY family_id
HAVING COUNT(DISTINCT ops_family_cluster_id) > 1
ORDER BY ops_cluster_count DESC, family_id;
GO

/* 6) OPS cluster -> multiple families */
SELECT
    ops_family_cluster_id,
    COUNT(DISTINCT family_id) AS family_count
FROM gold.bridge_family_ops_cluster
GROUP BY ops_family_cluster_id
HAVING COUNT(DISTINCT family_id) > 1
ORDER BY family_count DESC, ops_family_cluster_id;
GO

/* 7) mapping method summary */
SELECT
    mapping_method,
    mapping_confidence,
    COUNT(*) AS row_count
FROM gold.bridge_family_ops_cluster
GROUP BY
    mapping_method,
    mapping_confidence
ORDER BY
    row_count DESC,
    mapping_method,
    mapping_confidence;
GO

/* 8) null checks */
SELECT
    SUM(CASE WHEN family_id IS NULL THEN 1 ELSE 0 END) AS null_family_id,
    SUM(CASE WHEN ops_family_cluster_id IS NULL THEN 1 ELSE 0 END) AS null_ops_family_cluster_id,
    SUM(CASE WHEN mapping_method IS NULL THEN 1 ELSE 0 END) AS null_mapping_method,
    SUM(CASE WHEN mapping_confidence IS NULL THEN 1 ELSE 0 END) AS null_mapping_confidence,
    SUM(CASE WHEN record_source IS NULL THEN 1 ELSE 0 END) AS null_record_source,
    SUM(CASE WHEN loaded_at IS NULL THEN 1 ELSE 0 END) AS null_loaded_at
FROM gold.bridge_family_ops_cluster;
GO