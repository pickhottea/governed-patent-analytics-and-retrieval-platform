# Implementation Phase Retirement Execution Plan — English Version

**Repo:** `governed-patent-analytics-and-retrieval-platform`  
**Worktree:** `~/project3/patent_led_governance`  
**Branch:** `feature/tests-checks-boundary-cleanup`  
**Date:** 2026-04-19

## Opening memo

When a project becomes large, supports multiple execution phases, and relies on many tools, **authority drift** becomes hard to avoid. Upstream and downstream references start to split, one function may be represented by too many tables or views, and grain mismatches begin to appear. This becomes even more visible when AI is used as a copilot, because partial context, stale references, and tool-specific behavior can amplify structural drift.

This execution plan records the **retirement and simplification actions discovered during the POLICY implementation phase**. It should be updated continuously until the POLICY execution phase is complete, while tracking every file, table, view, or SQL script that should be deleted first, deleted later, kept forever, or held until a clear authority decision exists.

## Tag legend

- **[DELETE-WAVE-1]** — high-confidence first-wave deletion / retirement target
- **[DELETE-WAVE-2]** — delete later, after one specific alignment or authority condition is met
- **[KEEP-FOREVER]** — permanent functional core unless the architecture itself is redesigned
- **[HOLD-UNTIL]** — not yet safe to delete; this plan must list the trigger that unlocks action

## Governance rule for this plan

1. If an object is marked **[DELETE-WAVE-1]**, the team should not keep debating it indefinitely.
2. If an object is marked **[DELETE-WAVE-2]**, the blocking condition must be finite and explicit.
3. If an object is marked **[HOLD-UNTIL]**, the trigger must be concrete. If no touch trigger can be stated later, the object should be reconsidered for deletion.
4. If an object is marked **[KEEP-FOREVER]**, the burden of proof shifts to anyone who wants to remove it.

---

# 1. DELETE-WAVE-1 — delete / retire first

| Object | Type / location | Why it can go first | Trigger already satisfied? | Tag |
|---|---|---|---|---|
| `silver.publication_ipc` | warehouse legacy view | Canonical IPC contract already marks it deprecated / broken and says not to use it as source | Almost; delete after final downstream dependency confirmation | [DELETE-WAVE-1] |
| `sql/silver/publication_ipc.sql` | raw SQL build script | Old silver IPC build path conflicts with the now-aligned `stg_publication_ipc` contract | Yes, once final dependency confirmation is logged | [DELETE-WAVE-1] |
| `sql/archive/gold_loaders/load_bridge_publication_ipc.sql` | archived loader SQL | Archived historical loader, not current truth | Yes | [DELETE-WAVE-1] |
| `sql/archive/gold_loaders/load_dim_ipc.sql` | archived loader SQL | Archived historical loader, not current truth | Yes | [DELETE-WAVE-1] |
| `sql/archive/gold_loaders/load_bridge_publication_inventor_raw.sql` | archived loader SQL | Historical loader kept only for traceability | Yes | [DELETE-WAVE-1] |
| `sql/archive/gold_loaders/load_fact_publication_applicant.sql` | archived loader SQL | Historical loader kept only for traceability | Yes | [DELETE-WAVE-1] |
| `sql/archive/gold_loaders/load_fact_publication_inventor.sql` | archived loader SQL | Historical loader kept only for traceability | Yes | [DELETE-WAVE-1] |

**Wave-1 execution note:**
Delete Wave 1 should only be blocked if a real restore workflow still depends on these files. If no one can name that restore workflow, delete them from active use and mark them retired.

---

# 2. DELETE-WAVE-2 — delete later, after one finite blocker is cleared

| Object | Type / location | Why it should go later | Finite blocker | Tag |
|---|---|---|---|---|
| `dbo.bm25_document` | warehouse view | Drift source versus `gold.bm25_document`; currently part of the 149/150 mismatch story | BM25 authority decision + consumer repoint plan | [DELETE-WAVE-2] |
| `sql/gold/bm25_document.sql` | raw SQL build script | Likely duplicate deploy path if dbt or gold becomes authoritative | BM25 build ownership must be frozen | [DELETE-WAVE-2] |
| `dbo.bridge_family_publication` | warehouse mirror view | Strong mirror candidate if `gold.bridge_family_publication` is authoritative | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `dbo.bridge_publication_ipc` | warehouse mirror view | Strong mirror candidate if gold/dbt path is authoritative | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `dbo.dim_ipc` | warehouse mirror view | Likely mirror if `gold.dim_ipc` remains the canonical dim | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `dbo.dim_publication` | warehouse mirror view | Publication version path has already moved to gold/mainline | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `dbo.fact_publication_applicant` | warehouse mirror view | Likely mirror of gold/dbt fact path | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `dbo.fact_publication_inventor` | warehouse mirror view | Likely mirror of gold/dbt fact path | Consumer inventory + repoint plan | [DELETE-WAVE-2] |
| `sql/gold/bridge_family_publication.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `sql/gold/bridge_family_ops_cluster.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `sql/gold/bridge_publication_ipc.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `sql/gold/dim_ipc.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `sql/gold/fact_publication_applicant.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `sql/gold/fact_publication_inventor.sql` | raw SQL build script | Duplicate object-builder if dbt is authoritative | Per-object build ownership freeze | [DELETE-WAVE-2] |
| `gold.v_ipc_taxonomy_lookup_display` | display view | Display-layer duplication candidate | IPC display consumer inventory | [DELETE-WAVE-2] |
| `gold.v_cpc_taxonomy_lookup_display` | display view | Display-layer duplication candidate | CPC display consumer inventory | [DELETE-WAVE-2] |
| `gold.v_cpc_taxonomy_lookup_display_enriched` | display view | Display-layer duplication candidate | CPC display consumer inventory | [DELETE-WAVE-2] |
| `models/intermediate/stg_ops_family_members_canonical.sql` | dbt helper | Helper may be folded into one stable raw/clean path later | OPS raw/clean contract must freeze first | [DELETE-WAVE-2] |

---

# 3. KEEP-FOREVER — permanent core unless architecture is redesigned

| Object | Type / location | Why it must remain | Tag |
|---|---|---|---|
| `bridge_family_ops_cluster` | dbt/gold core bridge | Family expansion identity core | [KEEP-FOREVER] |
| `bridge_family_publication` | dbt/gold core bridge | Family-to-publication core expansion path | [KEEP-FOREVER] |
| `dim_publication` | dbt/gold core dim | Canonical publication identity, including country/number/version | [KEEP-FOREVER] |
| `gold.dim_family` | warehouse family dim | Family-grain headline truth | [KEEP-FOREVER] |
| `stg_publication_ipc` | dbt/warehouse staging | Active IPC staging contract | [KEEP-FOREVER] |
| `bridge_publication_ipc` | dbt/gold bridge | Core publication-to-IPC relation | [KEEP-FOREVER] |
| `dim_ipc` | dbt/gold dim | Canonical IPC dimension | [KEEP-FOREVER] |
| `gold.v_ipc_taxonomy_lookup` | warehouse lookup view | Explanation/popup lookup layer | [KEEP-FOREVER] |
| `mart_publication_ipc_expanded` | dbt mart | Publication-grain IPC footprint | [KEEP-FOREVER] |
| `mart_family_ipc_distribution` | dbt mart | Family-grain IPC distribution/ranking | [KEEP-FOREVER] |
| `fact_publication_applicant` | dbt/gold fact | Long-table applicant fact | [KEEP-FOREVER] |
| `fact_publication_inventor` | dbt/gold fact | Long-table inventor fact | [KEEP-FOREVER] |
| `dim_country` | dbt/gold dim | Country/geo lane foundation | [KEEP-FOREVER] |
| `stg_publication_dates` | dbt staging | Date semantics lane foundation | [KEEP-FOREVER] |
| `mart_family_publication_coverage` | dbt mart | Family coverage headline / Power BI-facing mart | [KEEP-FOREVER] |
| `gold.bm25_document` | warehouse serving table | BM25 serving truth candidate / search index source | [KEEP-FOREVER] |
| `gold.v_family_search` | warehouse search view | Field tab / landscape serving path | [KEEP-FOREVER] |
| `gold.fact_semantic_chunk` | warehouse semantic fact | Semantic lane core artifact | [KEEP-FOREVER] |
| `gold.semantic_inventory` | warehouse inventory | Semantic lineage / observability core | [KEEP-FOREVER] |
| `sql/checks/warehouse/*` | manual checks | Explicitly separated from dbt singular tests | [KEEP-FOREVER] |
| `sql/utility/create_or_alter_fn_normalize_publication_number.sql` | DB utility | Legitimate DB utility responsibility | [KEEP-FOREVER] |
| `sql/00_create_schemas.sql` | bootstrap SQL | Environment bootstrap responsibility | [KEEP-FOREVER] |

---

# 4. HOLD-UNTIL — do not touch yet, but the timing is explicit

| Object | Why not now | Touch timing / exact trigger | Tag |
|---|---|---|---|
| `models/marts/bm25_document.sql` | Live dbt BM25 path still returns 149 and is part of the unresolved authority story | Touch after BM25 authority is decided and the missing-publication root cause is written down | [HOLD-UNTIL] |
| `stg_rawdata_patents_effective` | Intermediate helper may still support publication-version path | Touch after full dependency map for `dim_publication` is documented | [HOLD-UNTIL] |
| `stg_rawdata_patents_backfill_gap` | Likely incident/gap helper | Touch after date/version path is frozen and no backfill recovery workflow depends on it | [HOLD-UNTIL] |
| `gold.ipc_description_reference` / `gold.cpc_description_reference` | Lookup/reference semantics may still be consumed | Touch after lookup dependency map is documented | [HOLD-UNTIL] |
| `silver.rawdata_patents` / `sql/silver/rawdata_patents.sql` | Still part of active source registry | Touch after source registry freeze | [HOLD-UNTIL] |
| `silver.publication_applicant_raw`, `silver.publication_inventor_raw`, `silver.stg_*` mirrors | Mirror authority still ambiguous | Touch after applicant/inventor source registry freeze | [HOLD-UNTIL] |
| `dbo.stg_*` mirror views | Some are still in active dbt/warehouse paths | Touch after source registry and replacement path are explicit | [HOLD-UNTIL] |
| `gold.v_taxonomy_scope_root_resolved` | Helper still lacks a complete consumer review | Touch after IPC/CPC consumer inventory is finished | [HOLD-UNTIL] |
| specialized queue / serving SQL (`create_or_alter_v_family_search.sql`, `create_or_alter_v_ipc_taxonomy_lookup.sql`, `create_publication_version_review_queue.sql`, `load_publication_version_review_queue.sql`, `semantic_inventory_ddl.sql`) | May still be the only deploy path for special objects | Touch after every file has an owner and a replacement decision | [HOLD-UNTIL] |

---

# 5. Functional simplification view

## 5.1 What should remain as distinct functions

These should **not** be collapsed into one table:

1. Family/publication identity core
2. Applicant/inventor/country expansion
3. IPC/CPC taxonomy and distribution
4. BM25 lexical serving
5. Semantic / Google serving

## 5.2 What should be simplified

The simplification target is **not** “fewer tables no matter what.”

The simplification target is:

- fewer duplicate authorities
- fewer mirror views without explicit ownership
- fewer display-only variants
- fewer raw SQL build scripts once dbt or a governed warehouse path clearly owns the function

---

# 6. Execution order

## Step 1
Retire Wave 1 candidates first.

## Step 2
Freeze per-object build ownership for BM25, family/publication core, and IPC core.

## Step 3
Inventory consumers of `dbo.*` mirror views.

## Step 4
Repoint consumers to the chosen authoritative gold/dbt path.

## Step 5
Retire Wave 2 candidates.

---

# 7. Final principle

This plan is intentionally stricter than a neutral inventory.

If an object is not core, not uniquely useful, and not protected by a real dependency, it should not survive forever as drift residue.

The target of the POLICY implementation phase is not only correctness.
It is also **structural simplification with traceable authority**.
