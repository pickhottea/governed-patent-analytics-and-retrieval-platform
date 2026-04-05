USE patent_analytics;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'gold'
)
BEGIN
    EXEC('CREATE SCHEMA gold');
END
GO

IF OBJECT_ID('gold.semantic_inventory', 'U') IS NULL
BEGIN
    CREATE TABLE gold.semantic_inventory (
        semantic_inventory_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        run_id NVARCHAR(100) NOT NULL,
        collection_name NVARCHAR(100) NOT NULL,
        family_id NVARCHAR(50) NOT NULL,
        selected_publication NVARCHAR(50) NULL,
        chunk_type NVARCHAR(30) NOT NULL,
        vector_id NVARCHAR(150) NOT NULL,
        embedding_model NVARCHAR(100) NOT NULL,
        embedding_version_id NVARCHAR(100) NOT NULL,
        source NVARCHAR(30) NULL,
        claims_lang_hint NVARCHAR(50) NULL,
        claim1_extraction_quality NVARCHAR(20) NULL,
        claim1_reason_code NVARCHAR(100) NULL,
        claims_parse_method NVARCHAR(50) NULL,
        chunk_policy_version NVARCHAR(20) NULL,
        spec_policy NVARCHAR(50) NULL,
        embedded_at DATETIME2 NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_semantic_inventory_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_semantic_inventory_vector UNIQUE (vector_id)
    );
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_semantic_inventory_run_chunk_family'
      AND object_id = OBJECT_ID('gold.semantic_inventory')
)
BEGIN
    CREATE INDEX IX_semantic_inventory_run_chunk_family
        ON gold.semantic_inventory (run_id, chunk_type, family_id);
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_semantic_inventory_pub'
      AND object_id = OBJECT_ID('gold.semantic_inventory')
)
BEGIN
    CREATE INDEX IX_semantic_inventory_pub
        ON gold.semantic_inventory (selected_publication);
END
GO
