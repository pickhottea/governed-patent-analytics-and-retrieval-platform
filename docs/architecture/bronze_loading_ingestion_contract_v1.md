
---

# Bronze Loading / Ingestion Contract v1

## Purpose

Define the loading contract for the first bronze ingestion path:

`rawdata_patents.xlsx -> bronze.rawdata_patents`

This contract governs how the selected-publication anchor source is loaded into the warehouse bronze layer.

---

## Scope

This contract currently covers only:

- source file: `rawdata_patents.xlsx`
- target table: `bronze.rawdata_patents`

This contract does **not** yet cover:

- family-member expansion ingestion
- abstract enrichment ingestion
- semantic chunk ingestion
- BM25 serving model construction

---

## Role of this source

`rawdata_patents.xlsx` is the **selected-publication anchor source** for the current patent dataset.

Grain:

> 1 row = 1 selected publication representing 1 family

This source is valid for:

- family anchor loading
- selected publication loading
- title / inventors / applicants / IPC / CPC / key date loading
- downstream BM25 seed preparation

This source is **not** the full family-member universe.

---

## Target table

Target table:

`bronze.rawdata_patents`

Current target columns:

- `family_id`
- `publication_number`
- `grant_number`
- `title`
- `inventors`
- `applicants`
- `earliest_priority_date`
- `ipc`
- `cpc`
- `publication_date`
- `earliest_publication`

---

## Load method

Current load method is:

> Python notebook ingestion from Excel into SQL Server

Current implementation pattern:

1. read `rawdata_patents.xlsx` in Jupyter / pandas
2. strip source column names
3. exclude non-contract column `No`
4. coerce selected fields into load-safe SQL-compatible values
5. load into `bronze.rawdata_patents` via `to_sql(...)`

This is currently an accepted project-stage ingestion method.

---

## Pre-load transformations

Allowed pre-load transformations are limited to ingestion-safe handling only.

Allowed:

- trim source column names
- drop `No`
- map `grant_number ` -> `grant_number`
- convert `family_id` to string
- convert date-like fields into stable string form for bronze loading
- preserve nulls

Not allowed in this bronze load step:

- IPC explosion / normalization
- applicant normalization
- inventor normalization
- semantic cleaning as business logic
- publication-family bridge derivation
- family-member expansion logic

---

## Grain and key expectations

Expected source grain:

> 1 row = 1 selected publication anchor = 1 family

Expected checks for current dataset:

- row count = 150
- distinct `family_id` = 150
- distinct `publication_number` = 150
- null `family_id` = 0
- null `publication_number` = 0

For this source version, both conditions should hold:

- `family_id` is unique
- `publication_number` is unique

---

## Bronze-layer contract stance

Bronze is a raw landing layer.

Therefore the following are acceptable in bronze:

- multi-valued IPC in a single field
- multi-valued inventors in a single field
- multi-valued applicants in a single field
- Excel control artifacts / formatting residue
- non-normalized textual fields

Bronze does **not** require 3NF or analytical usability.

Normalization is deferred to silver / gold.

---

## Load validation

Minimum validation after each load:

```sql
SELECT COUNT(*) AS row_count
FROM bronze.rawdata_patents;

SELECT COUNT(DISTINCT family_id) AS family_cnt,
       COUNT(DISTINCT publication_number) AS pub_cnt
FROM bronze.rawdata_patents;

Expected result for current dataset version:

- `row_count = 150`
- `family_cnt = 150`
- `pub_cnt = 150`

---

## Failure conditions

Load should be treated as failed if any of the following happen:

- target table not created
- row count mismatch
- null `family_id` introduced
- null `publication_number` introduced
- duplicate `family_id` introduced for this source version
- duplicate `publication_number` introduced for this source version
- source columns required by contract are missing

---

## Known limitations

Current source does not provide:

- full family-member publication coverage
- guaranteed abstract field
- publication-text completeness for semantic use
- normalized IPC / party structure

Therefore this bronze load is only the first ingestion segment, not full ingestion.

---

## Next planned ingestion contracts

Planned next source contracts:

- family-member expansion raw ingestion contract
- abstract enrichment ingestion contract
- BM25 document build contract

