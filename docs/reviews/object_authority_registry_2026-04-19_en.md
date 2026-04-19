# Object Authority Registry — 2026-04-19

## Memo

When a project becomes large, spans multiple execution phases, and uses many tools, some degree of **authority drift** is hard to avoid. Upstream and downstream references can drift apart, a single function can fragment into too many tables/views, and objects can end up misaligned in both purpose and grain. This pattern becomes even more visible when AI is used as an implementation copilot.

This memo was written during the policy-execution phase to capture these typical patterns, keep the review updated while implementation is still moving, and continuously mark retirement candidates until the policy-execution phase is complete and the solution is materially simplified.

## Scope

This registry pins a single authoritative owner for major objects appearing in:
- dbt models
- warehouse schemas (`bronze`, `silver`, `gold`, `dbo`)
- repo SQL build scripts
- manual warehouse checks
- archive loaders

## Status tags

- `[AUTHORITATIVE]` = current preferred owner / active path
- `[MIRROR]` = duplicate mirror path; not preferred
- `[LEGACY]` = deprecated / broken / should not guide new work
- `[DERIVED]` = valid derived mart / serving helper
- `[UTILITY]` = deployment helper / function / index helper
- `[ARCHIVE]` = historical only
- `[HOLD]` = do not retire yet; unresolved dependency or authority question remains

## Authority rules used

1. Canonical policies / contracts / authority docs outrank handovers, checklists, and README notes.
2. Archived and superseded material must not drive new implementation.
3. BM25, landscape/core warehouse, and semantic are separate lanes and must not silently inherit each other's authority.
4. Publication-grain and family-grain marts must not be collapsed into a single grain-ambiguous object.
5. During this branch, reduction is allowed only when justified by reference hygiene and dependency review.

---

## A. Family / publication core

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `models/marts/bridge_family_publication.sql` | dbt definition of family-publication bridge | dbt model source-of-build | `[AUTHORITATIVE]` | Core bridge definition; keep as the modeling source. |
| `gold.bridge_family_publication` | warehouse table used by field / landscape | gold serving/warehouse table | `[AUTHORITATIVE]` | Field/landscape route depends on this bridge. |
| `dbo.bridge_family_publication` | mirror view of bridge | `gold.bridge_family_publication` | `[MIRROR]` | Candidate for later retirement after consumer audit. |
| `models/marts/dim_publication.sql` | dbt definition of publication master | dbt model source-of-build | `[AUTHORITATIVE]` | Publication version / parsed fields belong here. |
| `gold.dim_publication` | warehouse publication master | gold serving/warehouse table | `[AUTHORITATIVE]` | Current publication-version working path should point here. |
| `dbo.dim_publication` | mirror view of publication master | `gold.dim_publication` | `[MIRROR]` | Later retirement candidate after dependency confirmation. |
| `gold.dim_family` | family master | gold serving/warehouse table | `[AUTHORITATIVE]` | Core family headline truth. |
| `models/intermediate/stg_rawdata_patents_effective.sql` | helper / reconciliation path | unresolved | `[HOLD]` | Keep until raw/backfill authority is fully reviewed. |
| `models/intermediate/stg_rawdata_patents_backfill_gap.sql` | backfill-gap helper | unresolved | `[HOLD]` | Keep until date / raw authority cleanup is complete. |

---

## B. IPC / CPC path

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `silver.stg_publication_ipc` | upstream normalized IPC relation | silver upstream contract | `[AUTHORITATIVE]` | Active upstream IPC relation. |
| `models/staging/stg_publication_ipc.sql` | dbt source-aligned staging mirror | dbt model source-of-build | `[AUTHORITATIVE]` | Already aligned to `stg_publication_ipc`. |
| `dbo.stg_publication_ipc` | warehouse/dbt-side mirror of staging IPC | `silver.stg_publication_ipc` contract mirrored via dbt | `[AUTHORITATIVE]` | Active staging relation for downstream dbt joins. |
| `silver.publication_ipc` | old IPC view | none; replaced by `silver.stg_publication_ipc` | `[LEGACY]` | Broken / deprecated legacy object. Do not use as source. |
| `sql/silver/publication_ipc.sql` | old build script for legacy IPC path | none; replaced by active `stg_publication_ipc` contract | `[LEGACY]` | Retirement candidate after final dependency confirmation. |
| `models/marts/bridge_publication_ipc.sql` | dbt publication-to-IPC bridge definition | dbt model source-of-build | `[AUTHORITATIVE]` | Canonical publication-to-IPC relation. |
| `gold.bridge_publication_ipc` | warehouse publication IPC bridge | gold serving/warehouse table | `[AUTHORITATIVE]` | Used by field and IPC marts. |
| `dbo.bridge_publication_ipc` | mirror view of publication IPC bridge | `gold.bridge_publication_ipc` | `[MIRROR]` | Later retirement candidate after dependency audit. |
| `models/marts/dim_ipc.sql` | dbt IPC dimension definition | dbt model source-of-build | `[AUTHORITATIVE]` | Canonical IPC dimension. |
| `gold.dim_ipc` | canonical IPC dimension table | gold serving/warehouse table | `[AUTHORITATIVE]` | Keep. |
| `dbo.dim_ipc` | mirror view of IPC dimension | `gold.dim_ipc` | `[MIRROR]` | Later retirement candidate after dependency audit. |
| `gold.v_ipc_taxonomy_lookup` | serving IPC explanation/lookup view | gold lookup view | `[AUTHORITATIVE]` | Explanation / popup layer; do not merge into `dim_ipc`. |
| `gold.v_ipc_taxonomy_lookup_display` | display-only variant | `gold.v_ipc_taxonomy_lookup` | `[DERIVED]` | Consolidate later if no separate consumer contract remains. |
| `models/marts/mart_publication_ipc_expanded.sql` | publication-grain IPC mart | dbt model source-of-build | `[AUTHORITATIVE]` | Must remain publication-grain. |
| `models/marts/mart_family_ipc_distribution.sql` | family-grain IPC mart | dbt model source-of-build | `[AUTHORITATIVE]` | Must remain family-grain. |
| `models/staging/stg_ipc_title_list.sql` | official IPC taxonomy staging | dbt model source-of-build | `[AUTHORITATIVE]` | Upstream structured taxonomy slice. |
| `models/staging/stg_cpc_title_list.sql` | official CPC taxonomy staging | dbt model source-of-build | `[AUTHORITATIVE]` | Keep. |
| `models/staging/stg_cpc_validity.sql` | CPC validity staging | dbt model source-of-build | `[AUTHORITATIVE]` | Keep. |
| `gold.dim_cpc` | CPC dimension | gold serving/warehouse table | `[AUTHORITATIVE]` | Keep. |
| `gold.v_cpc_taxonomy_lookup` | CPC explanation/lookup | gold lookup view | `[AUTHORITATIVE]` | Keep. |
| `gold.v_cpc_taxonomy_lookup_display` | display-only CPC variant | `gold.v_cpc_taxonomy_lookup` | `[DERIVED]` | Consolidate later if no unique downstream requirement exists. |

---

## C. Applicant / inventor / country / publication metadata

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `models/staging/stg_publication_applicant_raw.sql` | applicant raw staging | dbt model source-of-build | `[AUTHORITATIVE]` | Long-table raw staging. |
| `models/staging/stg_publication_inventor_raw.sql` | inventor raw staging | dbt model source-of-build | `[AUTHORITATIVE]` | Long-table raw staging. |
| `models/marts/fact_publication_applicant.sql` | applicant fact definition | dbt model source-of-build | `[AUTHORITATIVE]` | Keep as publication-applicant long table. |
| `gold.fact_publication_applicant` | applicant fact table | gold serving/warehouse table | `[AUTHORITATIVE]` | Keep. |
| `dbo.fact_publication_applicant` | mirror view | `gold.fact_publication_applicant` | `[MIRROR]` | Later retirement candidate after consumer audit. |
| `models/marts/fact_publication_inventor.sql` | inventor fact definition | dbt model source-of-build | `[AUTHORITATIVE]` | Keep as publication-inventor long table. |
| `gold.fact_publication_inventor` | inventor fact table | gold serving/warehouse table | `[AUTHORITATIVE]` | Keep. |
| `dbo.fact_publication_inventor` | mirror view | `gold.fact_publication_inventor` | `[MIRROR]` | Later retirement candidate after consumer audit. |
| `models/staging/stg_publication_country.sql` | country helper staging | dbt model source-of-build | `[AUTHORITATIVE]` | Keep for authority/country logic. |
| `models/marts/dim_country.sql` | country dimension definition | dbt model source-of-build | `[AUTHORITATIVE]` | Minimal current country dimension. |
| `gold.dim_country` | warehouse country dimension | gold serving/warehouse table | `[AUTHORITATIVE]` | Keep. |
| `models/staging/stg_publication_dates.sql` | publication date helper | dbt model source-of-build | `[AUTHORITATIVE]` | Active date-modeling path. |
| `models/marts/mart_family_country_distribution.sql` | BI-facing family country mart | derived mart | `[DERIVED]` | Possible consolidation candidate later. |
| `models/marts/mart_publication_country_expanded.sql` | publication country expansion mart | derived mart | `[DERIVED]` | Possible consolidation candidate later. |
| `models/marts/mart_family_applicant_summary.sql` | family applicant summary | derived mart | `[DERIVED]` | Possible consolidation candidate later. |
| `models/marts/mart_family_inventor_summary.sql` | family inventor summary | derived mart | `[DERIVED]` | Possible consolidation candidate later. |
| `models/marts/mart_applicant_organization.sql` | organization-facing derived mart | derived mart | `[DERIVED]` | Keep for now; later consolidation candidate. |
| `models/marts/mart_inventor.sql` | inventor-facing derived mart | derived mart | `[DERIVED]` | Keep for now; later consolidation candidate. |
| `models/marts/mart_publication_applicant_expanded.sql` | expanded applicant mart | derived mart | `[DERIVED]` | Keep for field/BI use until consumer map is simplified. |
| `models/marts/mart_publication_inventor_expanded.sql` | expanded inventor mart | derived mart | `[DERIVED]` | Keep for field/BI use until consumer map is simplified. |
| `models/marts/mart_family_publication_coverage.sql` | family-publication coverage mart | derived mart | `[DERIVED]` | Keep; explicit Power BI-facing mart. |

---
## Implementation finding — BM25 authority closure

A concrete implementation case showed that the earlier BM25 count mismatch was not caused primarily by BM25 text-construction logic.

The missing publication was:

- `publication_number = WO2021220141A1`
- `family_id = 78373363`

Verified during implementation:
- `bridge_family_publication` contained the publication
- `stg_rawdata_patents` did not contain it
- `stg_publication_abstract_dedup` did not contain it
- `silver.publication_abstract_dedup` also did not contain it
- but `gold.bm25_document` did contain it

A tactical backfill was added to the abstract/title source path.
After rerun:
- dbt `ref('bm25_document')` returned 150
- `test_serving_lane_gap` passed

Interpretation:
- the practical root cause was a **missing source row**, plus constructor-path misalignment
- the main remaining BM25 simplification question is now mirror retirement and deploy ownership

## D. BM25 path

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `models/marts/bm25_document.sql` | dbt BM25 model definition | dbt model source-of-build | `[AUTHORITATIVE]` | Active dbt BM25 path now returns 150 after abstract-path backfill and model alignment. |
| `gold.bm25_document` | intended BM25 serving table / ES source | gold serving table | `[AUTHORITATIVE]` | Current serving path is reconciled to 150 and remains the preferred warehouse serving artifact. |
| `dbo.bm25_document` | BM25 mirror view | `gold.bm25_document` / dbt BM25 path | `[MIRROR]` | The count gap is closed. Remaining action is consumer audit and later retirement decision. |
| `models/marts/mart_bm25_publication_metadata.sql` | BM25 hydration metadata mart | dbt model source-of-build | `[AUTHORITATIVE]` | Keep as presentation metadata source for now. |
| `gold.v_bm25_publication_metadata` | BM25 hydrated result view | gold lookup/presentation view | `[DERIVED]` | Keep; may later be consolidated with dbt-side metadata if duplicate path persists. |
| `sql/gold/bm25_document.sql` | warehouse build script | unresolved until bm25 authority is frozen | `[HOLD]` | Do not retire before confirming deployment path. |
| `sql/gold/create_or_alter_v_bm25_publication_metadata.sql` | BM25 metadata view DDL | unresolved until view ownership is frozen | `[HOLD]` | Keep for now. |

---

## E. Semantic / serving path

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `gold.fact_semantic_chunk` | semantic serving fact | semantic lane warehouse artifact | `[AUTHORITATIVE]` | Keep. |
| `gold.semantic_inventory` | semantic inventory | semantic lane warehouse artifact | `[AUTHORITATIVE]` | Keep. |
| `gold.v_semantic_inventory_summary` | semantic serving summary | serving/presentation view | `[AUTHORITATIVE]` | Keep. |
| Chroma collections / semantic index | semantic retrieval store | semantic lane serving system | `[AUTHORITATIVE]` | Separate lane; do not merge with BM25. |

---

## F. Raw / bronze / silver ingestion path

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `sql/bronze/ops_family_members_raw.sql` | bronze raw build script | bronze raw layer | `[AUTHORITATIVE]` | Keep. |
| `sql/bronze/patents_canonical_raw.sql` | bronze raw build script | bronze raw layer | `[AUTHORITATIVE]` | Keep. |
| `sql/bronze/raw_pub_to_family_id_v2_raw.sql` | bronze raw build script | bronze raw layer | `[AUTHORITATIVE]` | Keep. |
| `sql/silver/ops_family_members.sql` | upstream silver build script | silver upstream relation | `[AUTHORITATIVE]` | Keep for now. |
| `sql/silver/rawdata_patents.sql` | upstream silver build script | silver upstream relation | `[AUTHORITATIVE]` | Keep for now. |
| `sql/silver/raw_pub_to_family_id_v2.sql` | upstream silver build script | silver upstream relation | `[AUTHORITATIVE]` | Keep for now. |
| `sql/silver/publication_applicant_raw.sql` | upstream silver build script | silver upstream relation | `[AUTHORITATIVE]` | Keep. |
| `sql/silver/publication_inventor_raw.sql` | upstream silver build script | silver upstream relation | `[AUTHORITATIVE]` | Keep. |
| `sql/silver/publication_abstract.sql` | upstream abstract path | unresolved; may be superseded by dedup path for active use | `[HOLD]` | Keep until abstract authority is explicitly frozen. |
| `sql/silver/publication_abstract_dedup.sql` | active abstract dedup path | silver upstream relation | `[AUTHORITATIVE]` | Keep. |
| `models/staging/stg_rawdata_patents.sql` | dbt staging mirror | dbt model source-of-build | `[AUTHORITATIVE]` | Keep. |
| `models/staging/stg_raw_pub_to_family_id_v2.sql` | dbt staging mirror | dbt model source-of-build | `[AUTHORITATIVE]` | Keep. |
| `models/staging/stg_ops_family_members.sql` | dbt staging raw+clean boundary model | dbt model source-of-build | `[AUTHORITATIVE]` | Already moved toward clean/raw separation. |
| `models/intermediate/stg_ops_family_members_canonical.sql` | intermediate canonicalization step | unresolved; depends on actual downstream adoption | `[HOLD]` | Keep until consumer map is explicit. |

---

## G. Utilities / indexes / checks / archive

| Object | Current role | Unique authoritative owner | Status | Notes |
|---|---|---|---|---|
| `sql/utility/create_or_alter_fn_normalize_publication_number.sql` | database utility function | utility layer | `[UTILITY]` | Keep. |
| `sql/gold/bridge_family_publication_indexes.sql` | index helper | utility/deployment helper | `[UTILITY]` | Keep if still used in deployment. |
| `sql/gold/bridge_family_ops_cluster_indexes.sql` | index helper | utility/deployment helper | `[UTILITY]` | Keep if still used in deployment. |
| `sql/checks/warehouse/gold/*` | manual warehouse checks | check layer | `[UTILITY]` | Keep; intentionally separated from dbt tests. |
| `sql/checks/warehouse/silver/*` | manual warehouse checks | check layer | `[UTILITY]` | Keep; intentionally separated from dbt tests. |
| `sql/archive/gold_loaders/*` | old loader scripts | none; historical only | `[ARCHIVE]` | Already historical. Safe to keep in archive or remove from active path. |
| stray root `implementation_phase_object_review_2026-04-19.md` | duplicate standalone doc outside final docs path | none; duplicate doc copy | `[LEGACY]` | Safe retirement candidate. |

---

## Files that already satisfy retirement conditions

These are already safe to retire from active use now:

1. `sql/archive/gold_loaders/load_bridge_publication_inventor_raw.sql`
2. `sql/archive/gold_loaders/load_bridge_publication_ipc.sql`
3. `sql/archive/gold_loaders/load_dim_ipc.sql`
4. `sql/archive/gold_loaders/load_fact_publication_applicant.sql`
5. `sql/archive/gold_loaders/load_fact_publication_inventor.sql`
6. stray root copy `implementation_phase_object_review_2026-04-19.md`

Reason:
- they are already archive-class or duplicate-doc class
- archived and superseded material must not act as current truth
- their active replacements already exist in current dbt / docs paths

## Not yet safe to retire, but very likely next-wave candidates

These still need one final dependency check or authority closure:

- `silver.publication_ipc`
- `sql/silver/publication_ipc.sql`
- `dbo.bridge_family_publication`
- `dbo.bridge_publication_ipc`
- `dbo.dim_ipc`
- `dbo.dim_publication`
- `dbo.fact_publication_applicant`
- `dbo.fact_publication_inventor`
- `dbo.bm25_document`
- some `sql/gold/*.sql` build scripts once dbt-vs-warehouse deployment ownership is frozen

## Immediate practical rule

Retire in this order:
1. archived loaders / duplicate stray docs
2. clearly deprecated legacy objects with no remaining downstream dependency
3. mirror `dbo.*` paths only after all consuming code and dashboards are confirmed to point at `gold.*`
4. BM25 mirror retirement only after consumer audit and deploy ownership freeze, now that the count-gap closure is complete

## Final note

The purpose of this registry is not to defend object proliferation. The purpose is to reduce drift by pinning one owner per function, one preferred path per lane, and one explicit reason for anything that still survives.
