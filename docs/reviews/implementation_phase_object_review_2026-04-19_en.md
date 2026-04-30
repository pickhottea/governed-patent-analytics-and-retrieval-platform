# Implementation Phase Object Review — English Version

**Repo:** `governed-patent-analytics-and-retrieval-platform`  
**Worktree:** `~/project3/patent_led_governance`  
**Branch:** `feature/tests-checks-boundary-cleanup`  
**Status:** Working memo for the POLICY implementation phase  
**Date:** 2026-04-19
**Last updated:** 2026-04-30


## Opening memo

When a project becomes large, supports multiple execution phases, and relies on many tools, **authority drift** becomes hard to avoid. Upstream and downstream references start to split, one function may be represented by too many tables or views, and grain mismatches begin to appear. This becomes even more visible when AI is used as a copilot, because partial context, stale references, and tool-specific behavior can amplify structural drift.

This document records the **typical patterns discovered during the POLICY implementation phase**. It is intended to be updated continuously until the POLICY execution phase is complete, while tracking and tagging every file, table, view, and script that should be **retired**, **consolidated**, **held**, or **kept**, so that the final solution remains minimal, explicit, and governable.

## Tag legend

- **[KEEP]** — core object with a stable functional role, contract-level responsibility, or unavoidable serving responsibility.
- **[CONSOLIDATE]** — function is still needed, but exposure, naming, duplication, or presentation layers should be reduced.
- **[RETIRE-CANDIDATE]** — object can be retired when **any one** listed retirement condition is satisfied.
- **[HOLD]** — do not touch yet; there is a live dependency, unresolved authority question, or missing consumer inventory.

## Review principles used in this memo

1. Do not optimize for “fewer files at any cost.”
2. Optimize for **one authoritative path per function**.
3. Do not merge objects that have different grain or lane responsibility.
4. Do not keep parallel dbt / warehouse / raw SQL construction paths unless one of them is clearly authoritative.
5. If an object is tagged **[HOLD]**, this memo must list the exact timing or trigger that allows touching it later.
6. If no credible “touch timing” can be stated, the object should not remain permanently as a vague hold object.

---

# 1. Functional lane map

## 1.1 BM25 retrieval lane

**Purpose:** publication-grain lexical retrieval and result hydration

**Source mapping:**

`bronze.rawdata_patents` / `silver.rawdata_patents`  
→ dbt source `rawdata_patents`  
→ `stg_rawdata_patents`  

`silver.publication_abstract_dedup` / `silver.stg_publication_abstract_dedup`  
→ dbt source `publication_abstract_dedup`  
→ `stg_publication_abstract_dedup`  

`models/marts/bm25_document.sql`  
→ `dbo.bm25_document` (current live dbt result, 150 after source-row backfill and model alignment)  
→ `gold.bm25_document` (serving truth candidate, 150)  
→ `search/elasticsearch/create_patent_bm25_index.py`  
→ `search/elasticsearch/load_bm25_document.py`  
→ Elasticsearch index  
→ Streamlit BM25 tab  
→ `gold.v_bm25_publication_metadata` / hydration layer

**Current status:** the earlier 149-vs-150 BM25 serving-lane gap is now closed.  
The practical root cause was a missing source row in the abstract/title path for `WO2021220141A1`, not BM25 text-construction logic alone.

## 1.2 Family / publication core lane

**Purpose:** family headline truth, family-to-publication expansion, publication identity, version parsing

`bronze.raw_pub_to_family_id_v2_raw`  
→ `silver.raw_pub_to_family_id_v2`  
→ dbt source `raw_pub_to_family_id_v2`  
→ `stg_raw_pub_to_family_id_v2`  

`silver.ops_family_members`  
→ dbt source `ops_family_members`  
→ `stg_ops_family_members`  
→ optional helper/intermediate canonical layer  

Core outputs:
- `bridge_family_ops_cluster`
- `bridge_family_publication`
- `dim_publication`
- `dim_family`
- `gold.v_family_search`

## 1.3 Applicant / inventor / country / publication-version lane

**Purpose:** long-table applicant/inventor facts, country coverage, publication version, family-level summaries

Inputs / staging:
- `stg_publication_applicant_raw`
- `stg_publication_inventor_raw`
- `stg_publication_country`
- `stg_publication_dates`

Core outputs:
- `fact_publication_applicant`
- `fact_publication_inventor`
- `dim_country`
- `dim_publication`

Derived marts:
- `mart_publication_applicant_expanded`
- `mart_publication_inventor_expanded`
- `mart_publication_country_expanded`
- `mart_family_applicant_summary`
- `mart_family_inventor_summary`
- `mart_family_country_distribution`
- `mart_family_publication_coverage`
- `mart_applicant_organization`
- `mart_inventor`

## 1.4 IPC / CPC lane

**IPC active path:**
- `silver.stg_publication_ipc`
- `dbo.stg_publication_ipc`
- `bridge_publication_ipc`
- `dim_ipc`
- `gold.v_ipc_taxonomy_lookup`
- `mart_publication_ipc_expanded`
- `mart_family_ipc_distribution`

**IPC deprecated path:**
- `silver.publication_ipc`

**CPC active path:**
- `stg_cpc_title_list`
- `stg_cpc_validity`
- `dim_cpc`
- `gold.v_cpc_taxonomy_lookup`

## 1.5 Semantic / Google lane

**Purpose:** semantic retrieval, chunk-oriented serving, RAG evidence trace

Artifacts:
- `gold.fact_semantic_chunk`
- `gold.semantic_inventory`
- `gold.v_semantic_inventory_summary`
- Chroma collections / semantic retrieval / RAG evidence trace

**Authority rule:** semantic text authority is Google-canonical and must not silently collapse into BM25 text authority.

---

# 2. Command log from the implementation phase

## 2.1 OPS family member cleanup

```bash
cd ~/project3/patent_led_governance/dbt_patent_led

dbt run --select stg_ops_family_members

dbt show --inline "
select
    sum(case when member_publication_docdb <> member_publication_docdb_clean then 1 else 0 end) as docdb_changed_rows,
    sum(case when member_publication_number <> member_publication_number_clean then 1 else 0 end) as number_changed_rows
from {{ ref('stg_ops_family_members') }}
"

dbt test --select stg_ops_family_members
```

**Observed:**
- model run succeeded
- 826 rows changed in each cleaned field
- dirt-exposure singular tests remained intentionally red on raw fields

## 2.2 IPC source alignment

```bash
cd ~/project3/patent_led_governance/dbt_patent_led

dbt run --select stg_publication_ipc

dbt show --select stg_publication_ipc --limit 5

dbt test --select stg_publication_ipc
```

**Observed:**
- `stg_publication_ipc` aligned successfully
- current contract-level columns confirmed:
  - `family_id`
  - `publication_number`
  - `ipc_raw_token`
  - `ipc_token_clean`


## 2.3 BM25 serving-gap investigation and closure

```bash
cd ~/project3/patent_led_governance/dbt_patent_led

dbt show --inline "
select
    count(distinct publication_number) as bm25_publication_count
from {{ ref('bm25_document') }}
"

dbt show --inline "
select count(distinct publication_number) as publication_count
from gold.bm25_document
"

dbt show --inline "
with gold_set as (
    select distinct publication_number
    from gold.bm25_document
),
dbt_set as (
    select distinct publication_number
    from {{ ref('bm25_document') }}
)
select
    g.publication_number
from gold_set g
left join dbt_set d
    on g.publication_number = d.publication_number
where d.publication_number is null
"

```


**Observed during investigation:**

- dbt `ref('bm25_document')` initially returned **149**
- `gold.bm25_document` returned **150**
- the missing publication was `WO2021220141A1`

Further verification showed:

- `bridge_family_publication` contained `WO2021220141A1`
- `stg_rawdata_patents` did **not** contain it
- `stg_publication_abstract_dedup` did **not** contain it
- `silver.publication_abstract_dedup` also did **not** contain it
- but `gold.bm25_document` did contain it

A tactical source backfill was then added for:

- `publication_number = WO2021220141A1`
- `family_id = 78373363`

After rerun:

- dbt `ref('bm25_document')` returned **150**
- `test_serving_lane_gap` passed

**Findings:**

The practical root cause was a **missing source row in the abstract/title path**, combined with constructor-path misalignment between dbt BM25 and the warehouse serving path.


## 2.4 Known dbt/SQL Server preview caveat

`dbt show --inline` may fail on SQL Server when the inline query uses `TOP`, or when set operators such as `UNION` / `EXCEPT` interact badly with preview-time wrapping and ordering.

---

## 2.5 Publication metadata lane false-completeness finding

A focused implementation review around `WO2021220141A1` showed that the remaining publication-date gap was not caused by date parsing alone.

Verified during review:

- `bridge_family_publication` contained `WO2021220141A1`
- `stg_raw_pub_to_family_id_v2` contained `WO2021220141A1`
- `stg_ops_family_members_canonical` also resolved `WO2021220141A1`
- but `stg_rawdata_patents` did not contain a real publication-metadata row for it

This proved that family/publication identity coverage existed, while publication-level metadata coverage did not.

The previous `stg_rawdata_patents_backfill_gap` and `stg_rawdata_patents_effective` path created a shell-based fallback row that preserved existence only, not real publication metadata. That shell path could carry:

- `family_id`
- `publication_number`

but still left core publication metadata null, including:

- `publication_date`
- `grant_number`
- `title`
- `inventors`
- `applicants`

After restoring `stg_publication_dates` to read directly from `stg_rawdata_patents`, the date lane stabilized at:

- 149 total rows
- 149 rows with non-null `publication_date`
- 149 rows with `date_quality_status = ok`

Interpretation:

- the earlier 150-row appearance in this lane was false completeness
- the real problem is upstream publication-metadata coverage
- shell-based reaction measures are not acceptable as a long-term solution for the governed publication metadata lane

Decision:

- keep the authoritative raw publication metadata lane
- keep OPS member canonicalization for identity cleanup
- retire shell-based publication backfill from this lane
- recover missing publication metadata from the real upstream source (for example, by re-pulling from EPO), rather than fabricating downstream shell rows

---

# 3. Master object review table

| Functional group | Object | Type / location | Provided function | Tag | Reason | Consolidation conditions | Retirement conditions (any one is enough) | Touch timing / trigger |
|---|---|---|---|---|---|---|---|---|
| BM25 | `models/marts/bm25_document.sql` | dbt model | Builds publication-grain BM25 text from title + abstract | [KEEP] | Active dbt BM25 constructor is now aligned with the abstract-dedup path and returns 150 after source-row backfill | — | — | — |
| BM25 | `gold.bm25_document` | warehouse table | Intended BM25 serving truth / Elasticsearch source | [KEEP] | Core BM25 serving artifact | — | — | — |
| BM25 | `dbo.bm25_document` | warehouse view | BM25 mirror / alternate serving path | [HOLD] | The earlier count gap is now closed, but this object still requires final consumer audit before retirement | — | — | Touch only after consumer inventory and repoint plan are completed |
| BM25 | `sql/gold/bm25_document.sql` | raw SQL build script | Direct warehouse build path for BM25 object | [RETIRE-CANDIDATE] | Still useful as evidence of the earlier warehouse serving path, but likely redundant once deploy ownership is frozen | — | dbt is sole deploy path; no manual deployment still uses this file; BM25 deploy ownership is explicitly documented | After BM25 deploy ownership is frozen |
| BM25 | `models/marts/mart_bm25_publication_metadata.sql` | dbt mart | Hydration metadata for BM25 result cards | [CONSOLIDATE] | Useful function, but may be overexposed as a separate mart if one presentation path is enough | same fields already exist in `gold.v_bm25_publication_metadata`; only one stable hydration layer is needed; consumer can be repointed cleanly | — | After BM25 authority is frozen |
| BM25 | `gold.v_bm25_publication_metadata` | warehouse view | Presentation/hydration view for BM25 results | [CONSOLIDATE] | Presentation layer is useful, but should not coexist with too many equivalent shapes | fields match the dbt metadata mart; Streamlit only needs one stable presentation object; no separate SLA exists | — | After BM25 presentation consumers are inventoried |
| Family / publication | `models/marts/bridge_family_ops_cluster.sql` | dbt model | Maps governed family identity to OPS cluster identity | [KEEP] | Core family expansion bridge | — | — | — |
| Family / publication | `models/marts/bridge_family_publication.sql` | dbt model | Family-to-publication expansion bridge | [KEEP] | Core identity bridge for Field, IPC, coverage, and landscape | — | — | — |
| Family / publication | `models/marts/dim_publication.sql` | dbt model | Publication master, including parsed publication identity | [KEEP] | Canonical place for country / number / version | — | — | — |
| Family / publication | `gold.dim_family` | warehouse table | Family headline truth | [KEEP] | Family-grain truth must remain distinct from publication-grain serving | — | — | — |
| Family / publication | `models/staging/stg_raw_pub_to_family_id_v2.sql` | dbt staging | Publication-to-family staging mirror | [KEEP] | Required source for family/publication bridge | — | — | — |
| Family / publication | `models/staging/stg_ops_family_members.sql` | dbt staging | Raw OPS family-member expansion staging | [KEEP] | Explicit raw area with useful dirt-exposure tests | — | — | — |
| Family / publication | `models/intermediate/stg_ops_family_members_canonical.sql` | dbt intermediate | Canonicalized helper for OPS family members | [CONSOLIDATE] | Helper is valid, but should not automatically become another permanent public lane | same canonical fields can live in one stable staging path; no external consumer reads it directly; raw/clean boundary remains explicit | — | After OPS raw/clean contract is frozen |
| Family / publication | `models/intermediate/stg_rawdata_patents_effective.sql` | dbt intermediate | Shell-plus-authoritative consolidation helper for publication rows | [RETIRE-CANDIDATE] | Created a false-completeness path by unioning real publication rows with shell-only fallback rows; no longer acceptable for the governed publication metadata lane | — | `stg_publication_dates` and downstream publication-metadata checks are stable on the authoritative raw path alone; no active downstream dependency remains on shell-union behavior | Now |
| Family / publication | `models/intermediate/stg_rawdata_patents_backfill_gap.sql` | dbt intermediate | Shell-only coverage rescue for missing publication rows | [RETIRE-CANDIDATE] | Preserved existence without real publication metadata and masked upstream source incompleteness | — | authoritative publication lane is restored; missing publication rows must be recovered from upstream source rather than fabricated downstream | Now |
| Applicant / inventor | `models/staging/stg_publication_applicant_raw.sql` | dbt staging | Applicant raw staging | [KEEP] | Required staging for applicant facts | — | — | — |
| Applicant / inventor | `models/staging/stg_publication_inventor_raw.sql` | dbt staging | Inventor raw staging | [KEEP] | Required staging for inventor facts | — | — | — |
| Applicant / inventor | `models/marts/fact_publication_applicant.sql` | dbt model | Publication-applicant long-table fact | [KEEP] | Canonical long-table fact | — | — | — |
| Applicant / inventor | `models/marts/fact_publication_inventor.sql` | dbt model | Publication-inventor long-table fact | [KEEP] | Canonical long-table fact | — | — | — |
| Applicant / inventor | `models/marts/mart_publication_applicant_expanded.sql` | dbt mart | Publication-grain applicant expansion | [CONSOLIDATE] | Useful for BI/display, but not a core identity object | can be absorbed into one Power BI-facing layer; no unique SLA; not used as a canonical source by other models | — | After Power BI-facing marts are frozen |
| Applicant / inventor | `models/marts/mart_publication_inventor_expanded.sql` | dbt mart | Publication-grain inventor expansion | [CONSOLIDATE] | Same reasoning as applicant expanded mart | same display fields can be served from fewer marts; no unique SLA; not an identity anchor | — | After Power BI-facing marts are frozen |
| Applicant / inventor | `models/marts/mart_family_applicant_summary.sql` | dbt mart | Family-level applicant summary | [CONSOLIDATE] | Useful BI summary, but summary marts can proliferate | family-facing BI marts are explicitly redesigned; no unique consumer contract; summary can be folded into a smaller BI layer | — | After family BI contract is documented |
| Applicant / inventor | `models/marts/mart_family_inventor_summary.sql` | dbt mart | Family-level inventor summary | [CONSOLIDATE] | Same as family applicant summary | same as above | — | After family BI contract is documented |
| Applicant / inventor | `models/marts/mart_applicant_organization.sql` | dbt mart | Applicant organization helper mart | [CONSOLIDATE] | Candidate for BI-layer consolidation | same organization view can be served from fewer marts; no unique upstream contract; BI consumers can be repointed | — | After applicant marts are frozen |
| Applicant / inventor | `models/marts/mart_inventor.sql` | dbt mart | Inventor-facing convenience mart | [CONSOLIDATE] | Convenience mart, not a core contract object | same fields can be served from inventor fact plus one BI mart; no unique SLA; not a serving identity anchor | — | After inventor BI consumers are inventoried |
| Country / version | `models/staging/stg_publication_country.sql` | dbt staging | Publication country helper | [KEEP] | Supports country dim and map use cases | — | — | — |
| Country / version | `models/staging/stg_publication_dates.sql` | dbt staging | Publication/date helper | [KEEP] | Checklist explicitly prioritizes date semantics | — | — | — |
| Country / version | `models/marts/dim_country.sql` | dbt model | Country dimension for landscape and mapping | [KEEP] | Required for country / geo lane | — | — | — |
| Country / version | `models/marts/mart_publication_country_expanded.sql` | dbt mart | Publication-grain country expansion | [CONSOLIDATE] | BI-facing expanded mart, not a core identity object | can be absorbed into a smaller BI layer; no unique SLA; no model depends on it as canonical source | — | After country BI usage is frozen |
| Country / version | `models/marts/mart_family_country_distribution.sql` | dbt mart | Family-level country distribution | [CONSOLIDATE] | BI-facing distribution mart, not a core identity bridge | can be folded into consolidated family BI marts; not a canonical upstream source; no unique SLA | — | After family-country dashboard needs are frozen |
| Country / version | `models/marts/mart_family_publication_coverage.sql` | dbt mart | Family-level publication coverage / coverage headline | [KEEP] | Explicitly recommended Power BI-facing mart | — | — | — |
| IPC / CPC | `models/staging/stg_publication_ipc.sql` | dbt staging | Warehouse/dbt-side IPC staging mirror | [KEEP] | Active, aligned IPC source path | — | — | — |
| IPC / CPC | `silver.stg_publication_ipc` | warehouse view | Upstream IPC normalized relation | [KEEP] | Canonical active IPC source relation | — | — | — |
| IPC / CPC | `dbo.stg_publication_ipc` | warehouse view | dbt-side IPC staging mirror | [KEEP] | Matches the active IPC contract | — | — | — |
| IPC / CPC | `silver.publication_ipc` | warehouse legacy view | Old IPC relation | [RETIRE-CANDIDATE] | Canonical contract explicitly marks this object as deprecated / broken | — | replacement path is active; no downstream dependency remains; legacy source name is removed from dbt | As soon as consumer inventory confirms no active dependency |
| IPC / CPC | `sql/silver/publication_ipc.sql` | raw SQL build script | Old silver IPC build SQL | [RETIRE-CANDIDATE] | Conflicts with aligned `stg_publication_ipc` path | — | no manual deployment uses it; replacement is documented; legacy object is retired | After legacy IPC object is retired |
| IPC / CPC | `models/marts/bridge_publication_ipc.sql` | dbt model | Publication-to-IPC canonical bridge | [KEEP] | Core IPC relation | — | — | — |
| IPC / CPC | `models/marts/dim_ipc.sql` | dbt model | Canonical IPC dimension | [KEEP] | Canonical `ipc_code` key and hierarchy attrs | — | — | — |
| IPC / CPC | `gold.v_ipc_taxonomy_lookup` | warehouse view | IPC explanation / lookup / popup layer | [KEEP] | Contract-level lookup responsibility | — | — | — |
| IPC / CPC | `models/marts/mart_publication_ipc_expanded.sql` | dbt mart | Publication-grain IPC footprint | [KEEP] | Contract requires this publication-grain mart | — | — | — |
| IPC / CPC | `models/marts/mart_family_ipc_distribution.sql` | dbt mart | Family-level IPC distribution / ranking | [KEEP] | Contract requires this family-grain mart | — | — | — |
| IPC / CPC | `models/staging/stg_ipc_title_list.sql` | dbt staging | Official IPC title staging | [KEEP] | Needed to build taxonomy dimension | — | — | — |
| IPC / CPC | `models/staging/stg_cpc_title_list.sql` | dbt staging | Official CPC title staging | [KEEP] | Needed for CPC path | — | — | — |
| IPC / CPC | `models/staging/stg_cpc_validity.sql` | dbt staging | Official CPC validity staging | [KEEP] | Needed for CPC validity | — | — | — |
| IPC / CPC | `gold.dim_cpc` | warehouse table | Canonical CPC dimension | [KEEP] | Mirrors the IPC lane cleanly | — | — | — |
| IPC / CPC | `gold.v_cpc_taxonomy_lookup` | warehouse view | CPC explanation / popup lookup | [KEEP] | Explanation layer, distinct from `dim_cpc` | — | — | — |
| IPC / CPC | `gold.v_ipc_taxonomy_lookup_display` | warehouse display view | Display-oriented IPC lookup variant | [CONSOLIDATE] | Presentation variants are drifting into too many shapes | one base lookup can cover display needs; downstream can be repointed; no unique SLA exists | — | After IPC display consumers are inventoried |
| IPC / CPC | `gold.v_cpc_taxonomy_lookup_display` | warehouse display view | Display-oriented CPC lookup variant | [CONSOLIDATE] | Same as IPC display variant | one base lookup can cover display needs; no unique SLA; no unique consumer contract | — | After CPC display consumers are inventoried |
| IPC / CPC | `gold.v_cpc_taxonomy_lookup_display_enriched` | warehouse display view | Enriched CPC display variant | [CONSOLIDATE] | Enrichment should not automatically mean another permanent object | enrichment can be folded into one stable view; downstream can be repointed; no unique SLA | — | After CPC display consumers are inventoried |
| IPC / CPC | `gold.ipc_description_reference` / `gold.cpc_description_reference` | warehouse tables | Official description references | [HOLD] | Reference semantics may still be used by lookup views | — | — | Touch only after lookup/view dependency map is documented |
| Semantic | `gold.fact_semantic_chunk` | warehouse table | Semantic chunk artifact | [KEEP] | Core semantic lane artifact | — | — | — |
| Semantic | `gold.semantic_inventory` | warehouse table | Semantic inventory / lineage tracking | [KEEP] | Supports semantic observability and lineage | — | — | — |
| Semantic | `gold.v_semantic_inventory_summary` | warehouse view | Semantic summary / hydration view | [CONSOLIDATE] | Summary layer may be overexposed if multiple summaries appear | same metrics can be served from one semantic summary; no unique consumer contract; no separate SLA | — | After semantic lane is stabilized |
| Source provenance | `bronze.ops_family_members_raw` / `sql/bronze/ops_family_members_raw.sql` | warehouse raw + raw SQL | Raw OPS family-member ingestion | [KEEP] | Raw lineage input must remain visible | — | — | — |
| Source provenance | `bronze.patents_canonical_raw` / `sql/bronze/patents_canonical_raw.sql` | warehouse raw + raw SQL | Raw canonical patent anchor | [KEEP] | Core raw anchor source | — | — | — |
| Source provenance | `bronze.raw_pub_to_family_id_v2_raw` / `sql/bronze/raw_pub_to_family_id_v2_raw.sql` | warehouse raw + raw SQL | Raw publication-to-family anchor | [KEEP] | Core family/publication lineage input | — | — | — |
| Source provenance | `silver.rawdata_patents` / `sql/silver/rawdata_patents.sql` | warehouse relation + raw SQL | Active rawdata path into dbt | [HOLD] | Still part of active source registry | — | — | Touch only after source registry is fully frozen |
| Source provenance | `silver.publication_abstract_dedup` / `sql/silver/publication_abstract_dedup.sql` | warehouse relation + raw SQL | Deduplicated abstract relation | [KEEP] | BM25 depends on this function | — | — | — |
| Source provenance | `silver.publication_applicant_raw`, `silver.publication_inventor_raw`, `silver.stg_publication_applicant_raw`, `silver.stg_publication_inventor_raw` | warehouse mirrors | Applicant/inventor warehouse mirrors | [HOLD] | Mirror pattern exists, but authority between old and `stg_` names still needs inventory | — | — | Touch only after applicant/inventor source registry is frozen |
| Utility | `sql/utility/create_or_alter_fn_normalize_publication_number.sql` | raw SQL utility | DB utility for publication normalization | [KEEP] | Legitimate DB utility responsibility outside dbt | — | — | — |
| Utility | `sql/00_create_schemas.sql` | raw SQL bootstrap | Environment bootstrap / schema creation | [KEEP] | Bootstrap responsibility, not a model duplicate | — | — | — |
| Manual checks | `sql/checks/warehouse/gold/*` | manual check SQL | Manual gold-layer checks | [KEEP] | Explicitly separated from dbt tests by branch policy | — | — | — |
| Manual checks | `sql/checks/warehouse/silver/*` | manual check SQL | Manual silver-layer checks | [KEEP] | Explicitly separated from dbt tests by branch policy | — | — | — |
| Legacy / archive | `sql/archive/gold_loaders/*` | archived raw SQL | Historical gold loader scripts | [RETIRE-CANDIDATE] | Already archived; should not remain in the active mental model | — | corresponding dbt path is authoritative; no restore workflow depends on them; replacement is named clearly | After restore fallback decision is documented |
| Mirror layer | `dbo.bridge_family_publication`, `dbo.bridge_publication_ipc`, `dbo.dim_ipc`, `dbo.dim_publication`, `dbo.fact_publication_applicant`, `dbo.fact_publication_inventor` | warehouse views | dbo mirror views for gold/dbt objects | [HOLD] | High drift risk, but cannot be retired blindly before consumer inventory exists | — | — | Touch only after each object has an authority decision, consumer inventory, and repoint plan |
| Mirror layer | `dbo.stg_publication_dates`, `dbo.stg_publication_country`, `dbo.stg_publication_applicant_raw`, `dbo.stg_publication_inventor_raw`, `dbo.stg_rawdata_patents`, `dbo.stg_raw_pub_to_family_id_v2`, `dbo.stg_ops_family_members`, `dbo.stg_ops_family_members_canonical` | warehouse views | dbo-side staging mirrors | [HOLD] | Some are still in the active aligned path; cannot guess retirement safely | — | — | Touch only after source registry is frozen and the replacement schema/object is explicit |
| Search / display | `gold.v_family_search` | warehouse view | Streamlit Field / landscape serving view | [KEEP] | Explicit serving view for Field tab | — | — | — |
| Search / display | `gold.v_taxonomy_scope_root_resolved` | warehouse view | Taxonomy scope helper | [HOLD] | Useful helper, but not yet fully reviewed against actual consumers | — | — | Touch only after IPC/CPC consumer map is frozen |
| Warehouse scripts | `sql/gold/bridge_family_publication.sql`, `sql/gold/bridge_family_ops_cluster.sql`, `sql/gold/bridge_publication_ipc.sql`, `sql/gold/dim_ipc.sql`, `sql/gold/fact_publication_applicant.sql`, `sql/gold/fact_publication_inventor.sql` | raw SQL build scripts | Direct warehouse build scripts duplicating dbt-named objects | [RETIRE-CANDIDATE] | High duplication risk if dbt becomes the authoritative build path | — | dbt model is authoritative and reproducible; no deploy step still uses raw SQL file; same object contract is documented elsewhere | After per-object deploy ownership is frozen |
| Warehouse scripts | `sql/gold/create_or_alter_v_family_search.sql`, `sql/gold/create_or_alter_v_ipc_taxonomy_lookup.sql`, `sql/gold/create_publication_version_review_queue.sql`, `sql/gold/load_publication_version_review_queue.sql`, `sql/gold/semantic_inventory_ddl.sql` | specialized raw SQL | Specialized serving / queue / DDL scripts | [HOLD] | May still be the only deploy path for special-purpose objects | — | — | Touch only after each file has an explicit owner and replacement decision |

---

# 4. High-confidence immediate checklist

## 4.1 Keep now

Keep these as current functional core:

- `bridge_family_ops_cluster`
- `bridge_family_publication`
- `dim_publication`
- `gold.dim_family`
- `stg_publication_ipc`
- `bridge_publication_ipc`
- `dim_ipc`
- `gold.v_ipc_taxonomy_lookup`
- `mart_publication_ipc_expanded`
- `mart_family_ipc_distribution`
- `fact_publication_applicant`
- `fact_publication_inventor`
- `dim_country`
- `stg_publication_dates`
- `mart_family_publication_coverage`
- `gold.bm25_document`
- `gold.v_family_search`
- `sql/checks/warehouse/*`
- `sql/utility/create_or_alter_fn_normalize_publication_number.sql`
- `sql/00_create_schemas.sql`

## 4.2 Consolidation targets

Highest-value consolidation targets:

1. BM25 metadata presentation layer
   - `mart_bm25_publication_metadata`
   - `gold.v_bm25_publication_metadata`

2. IPC/CPC display variants
   - `gold.v_ipc_taxonomy_lookup_display`
   - `gold.v_cpc_taxonomy_lookup_display`
   - `gold.v_cpc_taxonomy_lookup_display_enriched`

3. BI-facing expansion / summary marts
   - `mart_family_applicant_summary`
   - `mart_family_inventor_summary`
   - `mart_family_country_distribution`
   - `mart_publication_applicant_expanded`
   - `mart_publication_inventor_expanded`
   - `mart_publication_country_expanded`
   - `mart_applicant_organization`
   - `mart_inventor`

## 4.3 Retirement candidates

Highest-confidence retirement candidates:

- `silver.publication_ipc`
- `sql/silver/publication_ipc.sql`
- `sql/archive/gold_loaders/*`
- duplicate `sql/gold/*.sql` object builders **after** dbt build ownership is frozen per object

- `dbo.bm25_document` remains a next-wave mirror retirement candidate, but no longer because of an unresolved 149-vs-150 mismatch. The current blocker is consumer inventory and repoint planning.

- `models/intermediate/stg_rawdata_patents_backfill_gap.sql`
- `models/intermediate/stg_rawdata_patents_effective.sql`


## 4.4 Hold zone

Do not touch these casually:

- `dbo.bm25_document`
- most `dbo.*` mirror views
- specialized serving/queue SQL

---

# 5. Final note

This memo is not trying to prove that “the fewer objects, the better.”

It is trying to prove something stricter:

- one function should not be allowed to drift into too many authorities
- one lane should not silently impersonate another lane
- one helper should not become a permanent public surface without justification
- and one project should not force future maintainers to guess which object is real

That is the actual target of the current POLICY implementation phase.
