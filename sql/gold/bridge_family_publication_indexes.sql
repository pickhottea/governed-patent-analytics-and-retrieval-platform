/*
File: sql/gold/bridge_family_publication_indexes.sql

Purpose:
- enforce basic nullability on gold.bridge_family_publication
- add primary access indexes for family/publication bridge usage

Prerequisite:
- gold.bridge_family_publication must already exist
*/

IF OBJECT_ID('gold.bridge_family_publication', 'U') IS NULL
BEGIN
    THROW 50000, 'gold.bridge_family_publication does not exist. Run bridge_family_publication.sql first.', 1;
END;
GO

/* -----------------------------------------------------------------
   Enforce NOT NULL on business key columns
   ----------------------------------------------------------------- */
ALTER TABLE gold.bridge_family_publication
ALTER COLUMN family_id VARCHAR(50) NOT NULL;
GO

ALTER TABLE gold.bridge_family_publication
ALTER COLUMN publication_number VARCHAR(50) NOT NULL;
GO

/* -----------------------------------------------------------------
   Unique grain protection
   Grain = 1 row = 1 family_id x 1 publication_number
   ----------------------------------------------------------------- */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_publication_pk'
      AND object_id = OBJECT_ID('gold.bridge_family_publication')
)
BEGIN
    CREATE UNIQUE CLUSTERED INDEX IX_bridge_family_publication_pk
        ON gold.bridge_family_publication (family_id, publication_number);
END;
GO

/* -----------------------------------------------------------------
   Publication lookup
   Useful for:
   - publication-centric serving
   - collision review
   - BM25 reconciliation
   ----------------------------------------------------------------- */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_publication_publication_number'
      AND object_id = OBJECT_ID('gold.bridge_family_publication')
)
BEGIN
    CREATE INDEX IX_bridge_family_publication_publication_number
        ON gold.bridge_family_publication (publication_number);
END;
GO

/* -----------------------------------------------------------------
   Family lookup
   Useful for:
   - family landscape reporting
   - expansion coverage tracing
   ----------------------------------------------------------------- */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_publication_family_id'
      AND object_id = OBJECT_ID('gold.bridge_family_publication')
)
BEGIN
    CREATE INDEX IX_bridge_family_publication_family_id
        ON gold.bridge_family_publication (family_id);
END;
GO

/* -----------------------------------------------------------------
   Collision-focused lookup
   Useful for:
   - publication collision diagnostics
   - governance checks
   ----------------------------------------------------------------- */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_bridge_family_publication_collision'
      AND object_id = OBJECT_ID('gold.bridge_family_publication')
)
BEGIN
    CREATE INDEX IX_bridge_family_publication_collision
        ON gold.bridge_family_publication (has_publication_collision, publication_number);
END;
GO