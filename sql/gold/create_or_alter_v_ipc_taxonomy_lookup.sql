CREATE OR ALTER VIEW gold.v_ipc_taxonomy_lookup AS
SELECT
    d.ipc_code,
    CAST(
        CASE
            WHEN d.ipc_subgroup IS NOT NULL AND d.ipc_subgroup <> '00' THEN 'subgroup'
            WHEN d.ipc_group IS NOT NULL THEN 'main_group'
            WHEN d.ipc_subclass IS NOT NULL AND d.ipc_code = d.ipc_subclass THEN 'subclass'
            WHEN d.ipc_class IS NOT NULL AND d.ipc_code = d.ipc_class THEN 'class'
            WHEN d.ipc_section IS NOT NULL AND d.ipc_code = d.ipc_section THEN 'section'
            ELSE 'unknown'
        END
        AS VARCHAR(20)
    ) AS ipc_level,
    CAST(
        CASE
            WHEN d.ipc_subgroup IS NOT NULL AND d.ipc_subgroup <> '00'
                THEN CONCAT(d.ipc_group, '/00')
            WHEN d.ipc_group IS NOT NULL
                THEN d.ipc_subclass
            WHEN d.ipc_subclass IS NOT NULL AND d.ipc_code = d.ipc_subclass
                THEN d.ipc_class
            WHEN d.ipc_class IS NOT NULL AND d.ipc_code = d.ipc_class
                THEN d.ipc_section
            ELSE NULL
        END
        AS VARCHAR(50)
    ) AS parent_ipc_code,
    CAST(
        CASE
            WHEN d.ipc_subclass = 'F21V' THEN 'anchor'
            WHEN d.ipc_subclass = 'F21K' THEN 'module_layer'
            WHEN d.ipc_subclass = 'H01L33' THEN 'chip_layer'
            ELSE NULL
        END
        AS VARCHAR(50)
    ) AS governance_role,
    CAST(1 AS BIT) AS is_current,
    COALESCE(
        r.ipc_description,
        CAST(
            CASE
                WHEN d.ipc_subgroup IS NOT NULL AND d.ipc_subgroup <> '00'
                    THEN CONCAT('IPC subgroup ', d.ipc_group, '/', d.ipc_subgroup)
                WHEN d.ipc_group IS NOT NULL
                    THEN CONCAT('IPC main group ', d.ipc_group, '/00')
                WHEN d.ipc_subclass IS NOT NULL AND d.ipc_code = d.ipc_subclass
                    THEN CONCAT('IPC subclass ', d.ipc_subclass)
                WHEN d.ipc_class IS NOT NULL AND d.ipc_code = d.ipc_class
                    THEN CONCAT('IPC class ', d.ipc_class)
                WHEN d.ipc_section IS NOT NULL AND d.ipc_code = d.ipc_section
                    THEN CONCAT('IPC section ', d.ipc_section)
                ELSE CONCAT('IPC code ', d.ipc_code)
            END
            AS NVARCHAR(2000)
        )
    ) AS description
FROM gold.dim_ipc d
LEFT JOIN gold.ipc_description_reference r
    ON d.ipc_code = r.ipc_code;
GO
