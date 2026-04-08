# IPC / CPC Data Contract (v1)

## 1. Status

This contract freezes the currently confirmed IPC path first.
Do not redesign repo structure.
Do not mix family-grain and expanded publication-grain.
Current mainline remains:

- `mart_publication_ipc_expanded`
- `mart_family_ipc_distribution`

## 2. Deprecated object

### `silver.publication_ipc`
- object type: view
- status: deprecated / broken legacy view
- reason: old definition references missing `ipc` column
- action: do not use as source
- preferred action: drop after confirming no downstream dependency

## 3. Active IPC relations

### 3.1 `silver.stg_publication_ipc`
Purpose:
- authoritative upstream normalized IPC relation

Grain:
- `1 row = 1 family_id x 1 publication_number x 1 ipc_raw_token`

Columns:
- `family_id`
- `publication_number`
- `ipc_raw_token`
- `ipc_token_clean`

Rules:
- `ipc_token_clean` is the normalized token used for downstream IPC joins
- source should replace legacy `silver.publication_ipc`

---

### 3.2 `dbo.stg_publication_ipc`
Purpose:
- warehouse/dbt-side staging mirror of upstream IPC staging relation

Grain:
- `1 row = 1 family_id x 1 publication_number x 1 ipc_raw_token`

Columns:
- `family_id`
- `publication_number`
- `ipc_raw_token`
- `ipc_token_clean`

Rules:
- contract must stay identical to `silver.stg_publication_ipc`
- downstream dbt models should use this relation or a dbt source pointing to the same contract

---

### 3.3 `gold.dim_ipc`
Purpose:
- canonical IPC dimension

Grain:
- `1 row = 1 ipc_code`

Columns:
- `ipc_code`
- `ipc_section`
- `ipc_class`
- `ipc_subclass`
- `ipc_group`
- `ipc_subgroup`

Rules:
- `ipc_code` is the canonical key
- taxonomy lookup and marts should align to this dimension
- do not rename these columns

---

### 3.4 `gold.v_ipc_taxonomy_lookup`
Purpose:
- serving lookup view for Streamlit / dashboard / explanation layer

Grain:
- `1 row = 1 ipc_code`

Columns:
- `ipc_code`
- `ipc_level`
- `parent_ipc_code`
- `governance_role`
- `is_current`
- `description`

Rules:
- `ipc_code` joins to `gold.dim_ipc.ipc_code`
- `parent_ipc_code` supports breadcrumb / tree navigation
- `description` is the first serving text field for IPC explanation

## 4. IPC marts (must-finish mainline)

### 4.1 `mart_publication_ipc_expanded`
Purpose:
- publication-grain IPC footprint

Grain:
- `1 row = 1 family_id x 1 publication_number x 1 ipc_code`

Minimum required columns:
- `family_id`
- `publication_number`
- `ipc_code`

Optional taxonomy columns, only if backed by `gold.dim_ipc`:
- `ipc_section`
- `ipc_class`
- `ipc_subclass`
- `ipc_group`
- `ipc_subgroup`

Rules:
- publication_number must follow current expanded-mart cleaning logic
- source path should use family-publication bridge + publication IPC relation
- do not mix family summary logic into this mart

---

### 4.2 `mart_family_ipc_distribution`
Purpose:
- family-level IPC distribution / ranking mart

Grain:
- `1 row = 1 family_id x 1 ipc_code`

Minimum required columns:
- `family_id`
- `ipc_code`

Optional taxonomy columns:
- `ipc_section`
- `ipc_class`
- `ipc_subclass`
- `ipc_group`
- `ipc_subgroup`

Optional metric columns:
- `publication_count_with_ipc`

Rules:
- derived from publication-level IPC expansion
- must remain family-grain
- used for Power BI family headline / ranking use cases

## 5. Join contract

### Source/staging join
- `dbo.stg_publication_ipc.ipc_token_clean`
  joins to
- `gold.dim_ipc.ipc_code`

### Lookup join
- `gold.v_ipc_taxonomy_lookup.ipc_code`
  joins to
- `gold.dim_ipc.ipc_code`

### Mart join
- `mart_publication_ipc_expanded.ipc_code`
  joins to
- `gold.dim_ipc.ipc_code`

- `mart_family_ipc_distribution.ipc_code`
  joins to
- `gold.dim_ipc.ipc_code`

## 6. CPC contract (target mirror of IPC)

CPC serving layer should mirror IPC naming as closely as possible.

### Target `gold.dim_cpc`
Grain:
- `1 row = 1 cpc_code`

Columns:
- `cpc_code`
- `cpc_section`
- `cpc_class`
- `cpc_subclass`
- `cpc_group`
- `cpc_subgroup`

### Target `gold.v_cpc_taxonomy_lookup`
Grain:
- `1 row = 1 cpc_code`

Columns:
- `cpc_code`
- `cpc_level`
- `parent_cpc_code`
- `governance_role`
- `is_current`
- `description`

### CPC validity source contract
Official validity source provides:
- `CPC Symbol`
- `Valid From Date`
- `Valid To Date`

Warehouse-normalized names should be:
- `cpc_code`
- `valid_from_date`
- `valid_to_date`
