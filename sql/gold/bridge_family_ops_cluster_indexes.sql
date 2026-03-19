/*
Purpose: Add constraints and indexes to gold.bridge_family_ops_cluster.
Target: gold.bridge_family_ops_cluster
Grain: 1 row = 1 family_id x 1 ops_family_cluster_id
Warnings:
- Run bridge_family_ops_cluster.sql first.
*/

IF OBJECT_ID('gold.bridge_family_ops_cluster', 'U') IS NULL
BEGIN
    THROW 50002, 'gold.bridge_family_ops_cluster does not exist. Run bridge_family_ops_cluster.sql first.', 1;
END;
GO

ALTER TABLE gold.bridge_family_ops_cluster
ALTER COLUMN family_id VARCHAR(50) NOT NULL;
GO

ALTER TABLE gold.bridge_family_ops_cluster
ALTER COLUMN ops_family_cluster_id VARCHAR(100) NOT NULL;
GO

ALTER TABLE gold.bridge_family_ops_cluster
ALTER COLUMN mapping_method VARCHAR(50) NOT NULL;
GO

ALTER TABLE gold.bridge_family_ops_cluster
ALTER COLUMN mapping_confidence VARCHAR(20) NOT NULL;
GO

ALTER TABLE gold.bridge_family_ops_cluster
ALTER COLUMN record_source VARCHAR(100) NOT NULL;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_ops_cluster_pk'
      AND object_id = OBJECT_ID('gold.bridge_family_ops_cluster')
)
BEGIN
    CREATE UNIQUE CLUSTERED INDEX IX_bridge_family_ops_cluster_pk
        ON gold.bridge_family_ops_cluster (family_id, ops_family_cluster_id);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_ops_cluster_family_id'
      AND object_id = OBJECT_ID('gold.bridge_family_ops_cluster')
)
BEGIN
    CREATE INDEX IX_bridge_family_ops_cluster_family_id
        ON gold.bridge_family_ops_cluster (family_id);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_ops_cluster_ops_family_cluster_id'
      AND object_id = OBJECT_ID('gold.bridge_family_ops_cluster')
)
BEGIN
    CREATE INDEX IX_bridge_family_ops_cluster_ops_family_cluster_id
        ON gold.bridge_family_ops_cluster (ops_family_cluster_id);
END;
GO