# HANDOVER — Landscape Push Checklist

## Current decision
Do **not** jump to semantic / RAG as the main next lane yet.

Current preferred order remains:
1. date modeling
2. country / geo dimension
3. applicant / inventor dbt marts
4. dbt tests
5. Power BI-facing marts
6. BM25 / serving follow-up only after landscape base is stable

Semantic / RAG should wait until landscape + BM25 are stable enough to freeze.

---

## What was completed in this sprint

### Date modeling
- `stg_publication_dates` was added as a publication helper for date profiling
- date helper currently uses the actually available raw fields:
  - `priority_date`
  - `application_date`
  - `publication_date`
  - `grant_number`
- dbt model build passed
- dbt tests passed:
  - `not_null`
  - `unique`
  - `accepted_values`

### Country dimension
- `country_authority_lookup` seed was added
- `dim_country` was created as a minimal authority / country lookup dimension
- `stg_publication_country` was created from publication prefix parsing
- dbt build and tests passed for the new country models

### Serving-lane gap fix
- `WO2021220141A1` was confirmed missing from `stg_rawdata_patents`
  while still existing in `stg_raw_pub_to_family_id_v2`
- a repair path was added:
  - `stg_rawdata_patents_backfill_gap`
  - `stg_rawdata_patents_effective`
- `stg_publication_dates` was switched to the effective path
- `test_serving_lane_gap` was added and passed
- current working publication set is restored to **150**

---

## Current working warehouse truth

### Landscape lane
- family headline truth = `150`
- expanded members = `826`
- `gold.bridge_family_publication` total = `976`

### Current selected corpus
- current working selected corpus = `150`
- this corpus is currently **family-anchored**
- operationally it is implemented with representative `publication_number` keys
- it should not be confused with the expanded family-publication universe

### Important interpretation
Keep these distinctions:

- **family headline / landscape reporting**
  - family-oriented analysis
  - de-duplicated summary views
  - family-level KPI and ranking

- **expanded family-publication universe**
  - member publication footprint
  - country / jurisdiction spread
  - expanded publication coverage
  - drill-down views

Do **not** collapse the expanded publication universe into the selected 150-row family-anchored corpus.

---

## What NOT to do next

- do not reopen `asset_id`
- do not switch naming away from `bronze / silver / gold`
- do not reopen big repo reorganization
- do not treat semantic / RAG as the immediate next main task
- do not confuse family headline views with expanded publication footprint views
- do not point Power BI directly at raw bridge / fact tables if marts can be defined instead

---

## Recommended next work order

### Step 1 — Applicant / inventor dbt marts
Move applicant / inventor fully into dbt.

Target staging:
- `stg_publication_applicant_raw`
- `stg_publication_inventor_raw`

Target marts:
- `fact_publication_applicant`
- `fact_publication_inventor`

Important rule:
- keep long-table grain
- do not infer inventor country from applicant country

### Step 2 — Country marts for family vs expanded views
The current `stg_publication_country` helper is only a selected-publication helper.

Need next:
- `mart_publication_country_expanded`
- `mart_family_country_distribution`

This allows:
- expanded jurisdiction footprint
- family-level country summary
- Power BI map and coverage views without mixing grains

### Step 3 — Family vs expanded marts for applicant / inventor / IPC
For dashboarding and analysis, use:
- family summary marts for headline KPI and ranking
- expanded publication marts for coverage / footprint / drill-down

Recommended pairs:
- `mart_family_applicant_summary`
- `mart_publication_applicant_expanded`
- `mart_family_inventor_summary`
- `mart_publication_inventor_expanded`
- `mart_family_ipc_distribution`
- `mart_publication_ipc_expanded`

### Step 4 — Power BI-facing marts
Do not point Power BI directly at raw bridge / fact tables.

First marts worth defining:
- family-publication coverage mart
- family country distribution mart
- applicant / organization mart
- inventor mart
- IPC distribution mart
- selected-corpus publication metadata mart

### Step 5 — Additional dbt tests
Keep expanding:
- `relationships`
- row-count reconciliation
- family collision checks
- serving-lane gap checks on critical paths

---

## Practical stop condition for the next sprint
You can call the next sprint successful if:
- applicant / inventor marts are advanced
- family vs expanded country marts exist
- at least one family summary mart exists
- at least one expanded footprint mart exists
- Power BI-facing marts are explicitly named and queryable

That is enough to say:
> landscape lane is under control, the main serving gap is sealed, and the next sprint can focus on analytics marts rather than patch recovery
