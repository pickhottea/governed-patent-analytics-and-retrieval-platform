SELECT 'bronze.ops_family_members_raw' AS table_name, COUNT(*) AS row_count FROM bronze.ops_family_members_raw
UNION ALL
SELECT 'bronze.raw_pub_to_family_id_v2_raw', COUNT(*) FROM bronze.raw_pub_to_family_id_v2_raw
UNION ALL
SELECT 'silver.publication_abstract', COUNT(*) FROM silver.publication_abstract;
GO