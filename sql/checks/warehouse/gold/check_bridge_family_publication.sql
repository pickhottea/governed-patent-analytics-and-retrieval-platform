/*
File: sql/gold/bridge_family_publication_checks.sql

Purpose:
- validate gold.bridge_family_publication build result
- confirm family headline universe stays stable
- detect grain duplication
- expose publication collision
- support BM25/publication reconciliation

Prerequisite:
- gold.bridge_family_publication must already exist
*/

IF OBJECT_ID('gold.bridge_family_publication', 'U') IS NULL
BEGIN
    THROW 50001, 'gold.bridge_family_publication does not exist. Run bridge_family_publication.sql first.', 1;
END;
GO

/* =========================================================
   1) Core row count
   ========================================================= */
SELECT
    COUNT(*) AS row_count
FROM gold.bridge_family_publication;
GO

/* =========================================================
   2) Family headline universe
   Expected: 150
   This must remain family truth, independent of BM25 collapse
   ========================================================= */
SELECT
    COUNT(DISTINCT family_id) AS distinct_family_id
FROM gold.bridge_family_publication;
GO

/* =========================================================
   3) Publication universe after family expansion
   This may be greater than anchor publication count
   ========================================================= */
SELECT
    COUNT(DISTINCT publication_number) AS distinct_publication_number
FROM gold.bridge_family_publication;
GO

/* =========================================================
   4) Grain duplicate check
   Grain = 1 row = 1 family_id x 1 publication_number
   Expected: 0 rows returned
   ========================================================= */
SELECT
    family_id,
    publication_number,
    COUNT(*) AS duplicate_count
FROM gold.bridge_family_publication
GROUP BY
    family_id,
    publication_number
HAVING COUNT(*) > 1;
GO

/* =========================================================
   5) BM25 representative summary
   Expected:
   - representative families should align to anchor family universe
   - representative publications may later collapse in BM25 serving
   ========================================================= */
SELECT
    COUNT(*) AS representative_rows,
    COUNT(DISTINCT family_id) AS representative_family_count,
    COUNT(DISTINCT publication_number) AS representative_publication_count
FROM gold.bridge_family_publication
WHERE is_bm25_representative = 1;
GO

/* =========================================================
   6) Check for multiple BM25 representatives inside one family
   Expected: 0 rows returned
   ========================================================= */
SELECT
    family_id,
    COUNT(*) AS representative_count
FROM gold.bridge_family_publication
WHERE is_bm25_representative = 1
GROUP BY family_id
HAVING COUNT(*) > 1;
GO

/* =========================================================
   7) Collision summary
   ========================================================= */
SELECT
    has_publication_collision,
    COUNT(*) AS row_count
FROM gold.bridge_family_publication
GROUP BY has_publication_collision
ORDER BY has_publication_collision DESC;
GO

/* =========================================================
   8) Collision detail
   Detect publications mapped to multiple family_id
   ========================================================= */
SELECT
    publication_number,
    COUNT(DISTINCT family_id) AS family_count
FROM gold.bridge_family_publication
GROUP BY publication_number
HAVING COUNT(DISTINCT family_id) > 1
ORDER BY family_count DESC, publication_number;
GO

/* =========================================================
   9) Collision detail with family list
   SQL Server 2017+ supports STRING_AGG
   ========================================================= */
SELECT
    publication_number,
    COUNT(DISTINCT family_id) AS family_count,
    STRING_AGG(CAST(family_id AS VARCHAR(50)), ', ') AS family_id_list
FROM (
    SELECT DISTINCT
        publication_number,
        family_id
    FROM gold.bridge_family_publication
) d
GROUP BY publication_number
HAVING COUNT(DISTINCT family_id) > 1
ORDER BY family_count DESC, publication_number;
GO

/* =========================================================
   10) Member role distribution
   Useful for checking anchor vs expanded footprint
   ========================================================= */
SELECT
    member_role,
    COUNT(*) AS row_count
FROM gold.bridge_family_publication
GROUP BY member_role
ORDER BY row_count DESC;
GO

/* =========================================================
   11) Record source distribution
   Useful for checking anchor / ops merge pattern
   ========================================================= */
SELECT
    record_source,
    COUNT(*) AS row_count
FROM gold.bridge_family_publication
GROUP BY record_source
ORDER BY row_count DESC;
GO

/* =========================================================
   12) Families with no expanded members beyond anchor
   Useful for coverage review
   ========================================================= */
SELECT
    family_id,
    COUNT(*) AS publication_count
FROM gold.bridge_family_publication
GROUP BY family_id
HAVING COUNT(*) = 1
ORDER BY family_id;
GO

/* =========================================================
   13) Families with largest expanded footprint
   Useful for landscape / coverage profiling
   ========================================================= */
SELECT TOP (20)
    family_id,
    COUNT(*) AS publication_count
FROM gold.bridge_family_publication
GROUP BY family_id
ORDER BY publication_count DESC, family_id;
GO

/* =========================================================
   14) Compare bridge family universe vs anchor universe
   ========================================================= */
SELECT
    'bridge_family_publication' AS object_name,
    COUNT(DISTINCT family_id) AS distinct_family_id,
    COUNT(DISTINCT publication_number) AS distinct_publication_number
FROM gold.bridge_family_publication

UNION ALL

SELECT
    'silver_stg_rawdata_patents' AS object_name,
    COUNT(DISTINCT family_id) AS distinct_family_id,
    COUNT(DISTINCT publication_number) AS distinct_publication_number
FROM silver.stg_rawdata_patents;
GO

/* =========================================================
   15) Compare OPS seed coverage vs bridge representative coverage
   ========================================================= */
SELECT
    'silver_ops_family_members_seed' AS object_name,
    COUNT(DISTINCT seed_publication_number) AS distinct_publication_number
FROM silver.ops_family_members

UNION ALL

SELECT
    'bridge_bm25_representative' AS object_name,
    COUNT(DISTINCT publication_number) AS distinct_publication_number
FROM gold.bridge_family_publication
WHERE is_bm25_representative = 1;
GO

/* =========================================================
   16) Null checks on required columns
   Expected: all zero
   ========================================================= */
SELECT
    SUM(CASE WHEN family_id IS NULL THEN 1 ELSE 0 END) AS null_family_id,
    SUM(CASE WHEN publication_number IS NULL THEN 1 ELSE 0 END) AS null_publication_number,
    SUM(CASE WHEN member_role IS NULL THEN 1 ELSE 0 END) AS null_member_role,
    SUM(CASE WHEN is_bm25_representative IS NULL THEN 1 ELSE 0 END) AS null_is_bm25_representative,
    SUM(CASE WHEN has_publication_collision IS NULL THEN 1 ELSE 0 END) AS null_has_publication_collision,
    SUM(CASE WHEN record_source IS NULL THEN 1 ELSE 0 END) AS null_record_source,
    SUM(CASE WHEN loaded_at IS NULL THEN 1 ELSE 0 END) AS null_loaded_at
FROM gold.bridge_family_publication;
GO