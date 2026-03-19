# Naming Contract v1

## 1. Purpose

This document defines the official naming convention for:

- folders
- SQL scripts
- Python scripts
- database objects
- schemas
- tables
- columns
- stored procedures

The goal is to make file names, database object names, and execution responsibility consistent across Bronze, Silver, Gold, and Search layers.

This contract also prevents mixed responsibilities such as:

- Python scripts inside SQL naming logic
- search-engine scripts mixed with warehouse SQL
- one concept being stored under multiple competing names

---

## 2. Core Principles

### 2.1 Language

All names must use **English**.

### 2.2 Case Style

Use:

- `lowercase`
- `snake_case`

Do not use:

- spaces
- camelCase
- PascalCase
- mixed-case abbreviations

### 2.3 One concept = one canonical name

A business object must have **one canonical name** across:

- SQL file name
- database table name
- downstream loader reference
- documentation reference

Example:

- SQL file: `sql/gold/bm25_document.sql`
- table: `gold.bm25_document`
- loader: `search/elasticsearch/load_bm25_document.py`

These must refer to the same object.

---

## 3. Folder Structure Contract

## 3.1 Canonical top-level folders

```text
docs/
sql/
scripts/
search/
data/
notebooks/
logs/
policies/
ui/

## 3.2 Folder responsibilities

### `docs/`

Contains architecture, contracts, handover notes, and written documentation.

Examples:

- `docs/architecture/naming_contract_v1.md`
- `docs/architecture/family_identity_and_lane_contract_v1.md`

### `sql/`

Contains **SQL only**.

No Python files are allowed under `sql/`.

Subfolders:

sql/bronze/
sql/silver/
sql/gold/

### `scripts/`

Contains reusable utility scripts that are not tied to a specific search engine.

Examples:

- ingestion helpers
- export utilities
- reconciliation scripts
- validation helpers

### `search/`

Contains search-serving logic only.

This folder is separated from warehouse SQL because search-serving is not the same responsibility as warehouse modeling.

Subfolders must be engine-specific.

Example:

```
search/elasticsearch/
```

This is intentional.

`search/` = domain

`elasticsearch/` = implementation engine

So this structure is correct:

```
search/elasticsearch/create_patent_bm25_index.py
search/elasticsearch/load_bm25_document.py
search/elasticsearch/query_patent_bm25.py
```

If a second engine is introduced later, it can be isolated cleanly:

```
search/opensearch/
search/whoosh/
```

This avoids mixing engine-specific scripts together.

---

## 4. Database Object Naming

## 4.1 Database

Use a lowercase snake_case business-oriented name.

Example:

- `patent_analytics`

## 4.2 Schemas

Allowed warehouse schemas:

- `bronze`
- `silver`
- `gold`

Schema names must be lowercase.

---

## 5. Bronze and Silver Table Naming

## 5.1 Naming rule

Bronze and Silver tables must follow:

```
<source_system>_<entity>
```

Examples:

- `rawdata_patents`
- `ops_family_members`
- `patents_canonical`

If the table stores raw, line-level, or unparsed content, use:

```
<source_system>_<entity>_raw
```

Examples:

- `ops_family_members_raw`
- `patents_canonical_raw`

## 5.2 Bronze meaning

Bronze stores ingested source data with minimal transformation.

Typical patterns:

- raw line payloads
- source extracts
- file-ingested tables
- schema-preserving loads

Examples:

- `bronze.rawdata_patents`
- `bronze.ops_family_members_raw`
- `bronze.patents_canonical_raw`

## 5.3 Silver meaning

Silver stores parsed, typed, standardized, and validated source-aligned data.

Silver still follows the source-oriented naming convention:

```
<source_system>_<entity>
```

Examples:

- `silver.rawdata_patents`
- `silver.ops_family_members`
- `silver.patents_canonical`

Do **not** use `stg_` prefixes in table names if the layer is already expressed by the schema.

Bad:

- `silver.stg_family_publication`

Preferred:

- `silver.ops_family_publication`
- `silver.rawdata_patents`
- `silver.ops_family_members`

Reason:

- `silver` already expresses the layer
- `stg_` duplicates the staging concept unnecessarily

---

## 6. Gold Table Naming

## 6.1 Naming rule

Gold tables must follow:

```
<category>_<entity>
```

Where:

- `<category>` describes the table role
- `<entity>` describes the business object

## 6.2 Allowed category patterns

## 6.2 Allowed category patterns

| Prefix   | Meaning                                | Example                        |
|----------|----------------------------------------|--------------------------------|
| `dim_`   | dimension table                        | `dim_family`, `dim_publication` |
| `fact_`  | fact-like event / relationship table   | `fact_publication_inventor`    |
| `agg_`   | aggregated table                       | `agg_family_yearly`            |
| `bridge_`| bridge / many-to-many mapping table    | `bridge_family_publication`    |
| `mart_`  | presentation / serving mart            | `mart_search_document`         |

## 6.3 Current project-aligned examples

- `gold.dim_family`
- `gold.dim_publication`
- `gold.dim_ipc`
- `gold.fact_publication_applicant`
- `gold.fact_publication_inventor`
- `gold.bridge_publication_ipc`
- `gold.bridge_family_publication`
- `gold.bm25_document`

## 6.4 Exception: search-serving document table

`gold.bm25_document` is an approved exception.

Reason:

- it is a serving-oriented document table
- it is not a classical transaction fact
- naming it as `fact_bm25_document` creates ambiguity

Therefore the canonical name is:

- file: `sql/gold/bm25_document.sql`
- table: `gold.bm25_document`
- loader: `search/elasticsearch/load_bm25_document.py`

Do not create or maintain both:

- `gold.bm25_document`
- `gold.fact_bm25_document`

for the same concept.

Choose one canonical name only.

For this project, the canonical name is:

- `gold.bm25_document`

---

## 7. SQL Script Naming

## 7.1 Rule

SQL file names must match the database object they create or load.

### Bronze

```
sql/bronze/<source_system>_<entity>.sql
sql/bronze/<source_system>_<entity>_raw.sql
```

Examples:

- `sql/bronze/rawdata_patents.sql`
- `sql/bronze/ops_family_members_raw.sql`

### Silver

```
sql/silver/<source_system>_<entity>.sql
```

Examples:

- `sql/silver/rawdata_patents.sql`
- `sql/silver/ops_family_members.sql`
- `sql/silver/ops_family_publication.sql`

### Gold

```
sql/gold/<category>_<entity>.sql
```

Examples:

- `sql/gold/dim_family.sql`
- `sql/gold/dim_publication.sql`
- `sql/gold/bridge_family_publication.sql`
- `sql/gold/bm25_document.sql`

## 7.2 File name must match target object

If a script creates:

```
gold.bridge_family_publication
```

the file name must be:

```
sql/gold/bridge_family_publication.sql
```

If a script creates:

```
gold.bm25_document
```

the file name must be:

```
sql/gold/bm25_document.sql
```

Do not use a file name that points to a different target object.

Bad:

- `sql/gold/bm25_document.sql` creating `gold.fact_bm25_document`
- `sql/gold/fact_bm25_document.sql` creating `gold.bm25_document`

---

## 8. Python Script Naming

## 8.1 Rule

Python file names must describe the executable action.

Pattern:

```
<verb>_<object>.py
```

Examples:

- `load_bm25_document.py`
- `create_patent_bm25_index.py`
- `query_patent_bm25.py`

## 8.2 Python location rules

### Search engine scripts

Engine-specific search scripts must be placed under:

```
search/<engine>/
```

Example:

```
search/elasticsearch/create_patent_bm25_index.py
search/elasticsearch/load_bm25_document.py
search/elasticsearch/query_patent_bm25.py
```

### General utility scripts

Non-engine-specific reusable scripts must be placed under:

```
scripts/
```

Examples:

- `scripts/profile_ops_family_members.py`
- `scripts/export_gold_bm25_document.py`

## 8.3 Python scripts must not be placed under `sql/`

`sql/` is reserved for SQL only.

Bad:

- `sql/bronze/load_ops_family_members.py`
- `sql/gold/load_bm25_document.py`

Correct:

- `scripts/load_ops_family_members.py`
- `search/elasticsearch/load_bm25_document.py`

---

## 9. Search Naming Contract

## 9.1 Canonical BM25 naming

The official BM25 naming contract is:

- SQL file: `sql/gold/bm25_document.sql`
- warehouse table: `gold.bm25_document`
- ES loader: `search/elasticsearch/load_bm25_document.py`
- ES index creator: `search/elasticsearch/create_patent_bm25_index.py`
- ES query script: `search/elasticsearch/query_patent_bm25.py`
- ES index name: `patent_bm25_v1`

## 9.2 Why `search/elasticsearch/` is correct

This structure is required because:

- `search/` expresses the domain responsibility
- `elasticsearch/` expresses the technical adapter

This is not duplication.

It is separation of concern.

Bad alternative:

```
search/create_patent_bm25_index.py
search/load_bm25_document.py
search/query_patent_bm25.py
```

This becomes messy when multiple engines exist.

Preferred:

```
search/elasticsearch/create_patent_bm25_index.py
search/elasticsearch/load_bm25_document.py
search/elasticsearch/query_patent_bm25.py
```

---

## 10. Column Naming Convention

## 10.1 Surrogate keys

All surrogate keys in dimension tables must use the suffix `_key`.

Pattern:

```
<table_name>_key
```

Examples:

- `family_key`
- `publication_key`
- `country_key`

## 10.2 Natural identifiers

Business identifiers must use descriptive names.

Examples:

- `family_id`
- `publication_number`
- `publication_docdb`

Do not rename business IDs to `_key` unless they are true surrogate keys.

## 10.3 Technical metadata columns

All technical metadata columns must start with:

```
dwh_
```

Examples:

- `dwh_load_datetime`
- `dwh_source_file_name`
- `dwh_record_hash`

## 10.4 Boolean columns

Boolean columns should start with:

- `is_`
- `has_`

Examples:

- `is_anchor_publication`
- `is_bm25_representative`
- `has_publication_collision`

## 10.5 Timestamp columns

Preferred suffixes:

- `_at` for timestamps
- `_date` for dates

Examples:

- `loaded_at`
- `ingested_at`
- `publication_date`

### 10.6 Human-readable relationship keys

For relationship-style records that need to remain readable by humans, a descriptive business key is allowed instead of a hashed key.

This rule applies when the key should immediately communicate:

- the parent context
- the child category
- the sequence of the child within the parent context

#### Pattern

```text
<parent_id>_<child_category><3-digit-sequence>


### Example

```
69845166_EP001
69845166_EP002
69845166_WO003
```

### Current approved use case

`silver.ops_family_members.ops_family_member_key`

Definition:

- `<parent_id>` = `ops_family_id`
- `<child_category>` = `member_jurisdiction`
- `<3-digit-sequence>` = sequence of the member within the same `ops_family_id`

Example interpretation:

- `69845166_EP001`
    - `69845166` = OPS family id
    - `EP` = member jurisdiction
    - `001` = first member in that OPS family sequence

### Reason

A human-readable relationship key is preferred here because:

- the user should be able to identify the family context immediately
- the user should be able to identify the member jurisdiction immediately
- a hash-based key hides useful meaning
- the expected number of members per OPS family is far below 1000, so a 3-digit sequence is sufficient for the current project scope

### Rule

When a human-readable relationship key is used:

- it must remain stable for the same ordering rule
- the ordering rule must be documented
- the sequence width must be explicit
- the key must not be confused with a surrogate key

### Current ordering rule for `ops_family_member_key`

Within `silver.ops_family_members`, the sequence is assigned by:

1. `ops_family_id`
2. `member_jurisdiction`
3. `member_publication_docdb`
4. `member_publication_number`

### Important distinction

`ops_family_member_key` is a **business-readable relationship key**.

It is not the same as:

- `ops_family_member_row_id`, which is only a technical row sequence
- a surrogate key such as `<entity>_key`
- a dataset family identity such as `family_id`

### Naming example in this project

- table: `silver.ops_family_members`
- column: `ops_family_member_key`
- format: `<ops_family_id>_<member_jurisdiction><3-digit-sequence>`

---

## 11. Stored Procedure Naming

Stored procedures for loading must follow:

```
load_<layer>
```

Examples:

- `load_bronze`
- `load_silver`
- `load_gold`

If more specificity is needed:

```
load_<layer>_<entity>
```

Examples:

- `load_bronze_ops_family_members`
- `load_gold_bm25_document`

Stored procedures must include:

- `try/catch`
- issue logging
- load duration tracking
- row count logging

---

## 12. Script Header Contract

Every SQL script and Python script must begin with a short header comment containing:

- purpose
- target object
- grain
- warnings / assumptions

### SQL example

```
/*
Purpose: Build gold.bm25_document for BM25 serving.
Target: gold.bm25_document
Grain: 1 row = 1 publication_number
Warnings:
- BM25 document count is not the official family headline count.
- Uses title + abstract only.
*/
```

### Python example

```
"""
Purpose: Load gold.bm25_document into Elasticsearch index patent_bm25_v1.
Target: patent_bm25_v1
Grain: 1 row = 1 publication_number
Warnings:
- Requires SQLSERVER_SA_PASSWORD environment variable.
- Requires Elasticsearch running on localhost:9200.
"""
```

---

## 13. Layer-Specific Rules

## 13.1 Bronze

Primary responsibility:

- ingestion
- completeness checks
- schema checks
- raw source preservation

Bronze SQL file names must reflect source ownership.

Examples:

- `sql/bronze/rawdata_patents.sql`
- `sql/bronze/ops_family_members_raw.sql`

## 13.2 Silver

Primary responsibility:

- parsing
- typing
- normalization
- source-aligned standardization

Silver SQL file names must reflect source-aligned entities.

Examples:

- `sql/silver/ops_family_members.sql`
- `sql/silver/ops_family_publication.sql`

## 13.3 Gold

Primary responsibility:

- analytics-ready modeling
- serving-ready business objects
- bridges, dimensions, facts, and marts

Gold file names must reflect table role.

Examples:

- `sql/gold/dim_family.sql`
- `sql/gold/bridge_family_publication.sql`
- `sql/gold/bm25_document.sql`

---

## 14. Naming Anti-Patterns

The following are not allowed:

- one concept with multiple competing table names
- Python scripts inside `sql/`
- file name and target object name mismatch
- mixed naming styles across layers
- duplicate layer markers such as `silver.stg_*` when schema already expresses layer
- ambiguous names such as `temp_table_final_v2`
- using `fact_` for every gold table regardless of actual role

---

## 15. Immediate Alignment Decisions

The following names are officially adopted now.

### BM25

- `sql/gold/bm25_document.sql`
- `gold.bm25_document`
- `search/elasticsearch/load_bm25_document.py`
- `search/elasticsearch/create_patent_bm25_index.py`
- `search/elasticsearch/query_patent_bm25.py`
- `patent_bm25_v1`

### Family bridge

- `sql/gold/bridge_family_publication.sql`
- `gold.bridge_family_publication`

### OPS expansion raw

- `sql/bronze/ops_family_members_raw.sql`
- `bronze.ops_family_members_raw`

### OPS expansion parsed

- `sql/silver/ops_family_members.sql`
- `silver.ops_family_members`

---

## 16. Final Principle

Naming must communicate:

- layer responsibility
- object role
- execution ownership
- downstream alignment

A correct name should make it obvious:

- where the file belongs
- what object it creates or loads
- what layer it serves
- whether it is SQL, Python, warehouse, or search

If a name creates ambiguity, it must be changed.