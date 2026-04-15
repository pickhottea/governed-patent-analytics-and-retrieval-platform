# Naming Contract v2

Status: Canonical  
Owner: Repo owner / architecture owner  
Supersedes: `docs/architecture/naming_contract_v1.md`  
Last reviewed: 2026-04-14

## 1. Purpose

This document extends the naming contract for the governed patent analytics and retrieval platform.

It keeps the existing naming foundations from v1 and adds missing rules for:

- documentation file naming
- policy file naming
- README exceptions
- version and date suffix rules
- authority / superseded metadata
- test vs check folder responsibilities

This contract is intended to reduce ambiguity across:

- architecture docs
- governance policies
- handover notes
- incidents
- warehouse objects
- dbt models
- search-serving adapters

---

## 2. What remains unchanged from v1

The following v1 rules remain valid:

- all names use English
- all names use lowercase snake_case
- one concept should have one canonical name
- top-level responsibilities remain separated across folders such as `docs/`, `policies/`, `scripts/`, `search/`, `ui/`

This v2 document is an extension, not a repo-wide rename mandate.

---

## 3. Scope

This contract applies to:

- markdown documents
- architecture contracts
- policy documents
- handover notes
- incident notes
- checks and test files
- SQL files
- Python files
- warehouse object names
- dbt model files

This contract does **not** require immediate renaming of all historical files.
It defines the standard for all new files and for gradual cleanup.

---

## 4. Core naming principles

### 4.1 Language

All names must use English.

### 4.2 Case style

Use:

- `lowercase`
- `snake_case`

Do not use:

- spaces
- camelCase
- PascalCase
- mixed separators such as `landscape-push-checklist`
- mixed-case abbreviations unless technically required in file content

### 4.3 One concept = one canonical name

A business object, policy, or contract should have one canonical name.

Examples:

- `gold.bm25_document`
- `search/elasticsearch/load_bm25_document.py`
- `docs/architecture/ipc_cpc_contract.md`

Do not create multiple competing names for the same concept.

---

## 5. Markdown document naming rules

### 5.1 Canonical contracts and policies

Canonical documents must follow:

```text
<topic>_v<major>.md
```

Examples:

- `naming_contract_v2.md`
- `ipc_cpc_contract_v1.md`
- `retention_policy_v1.md`
- `documentation_governance_policy_v1.md`

Use this format when the document defines durable rules or boundaries.

### 5.2 Dated memos, truth corrections, and operational notes

Time-specific notes must follow:

```
<topic>_yyyy_mm_dd.md
```


Examples:

- `bm25_truth_correction_2026_04_07.md`
- `publication_version_candidate_benchmark_2026_04_05.md`

Use this format when the document records a dated event, correction, memo, or benchmark.

### 5.3 Handover and checklist notes

Handover and execution notes must follow:

```
<handover_or_checklist_topic>_yyyy_mm_dd.md
```

Examples:

- `landscape_push_checklist_2026_04_05.md`
- `taxonomy_handover_2026_04_13.md`

These files are operational notes, not long-lived canonical contracts.

### 5.4 Incident files

Incident files must follow:

```
<incident_topic>_yyyy_mm_dd.md
```

Examples:

- `publication_version_lock_blocking_2026_04_05.md`
- `family_collision_2026_04_05.md`

If needed, a suffix may be added:

```
<incident_topic>_yyyy_mm_dd_v2.md
```

---

## 6. README exception rule

`README.md` is the only approved uppercase markdown filename exception.

It is allowed only for:

- repository root overview
- folder-level index / navigation
- onboarding summary

A `README.md` must not silently override a canonical policy or contract.

If a folder contains both:

- `README.md`
- a canonical contract / policy

then:

- `README.md` explains the folder
- the contract / policy remains the governing document

---

## 7. Version and date suffix rules

### 7.1 Versioned rule documents

Use version suffixes when a document defines rules, gates, or architecture boundaries.

Pattern:

```
_v1
_v2
_v3
```

Do not use floating labels such as:

- `_final`
- `_latest`
- `_new`
- `_fixed`

Bad:

- `retention_policy_final.md`
- `naming_contract_latest.md`

Good:

- `retention_policy_v1.md`
- `naming_contract_v2.md`

### 7.2 Dated documents

Use date suffixes for event-like, temporary, operational, or memo-style files.

Date format must be:

```
yyyy_mm_dd
```

Do not mix:

- `2026-04-05`
- `20260405`
- `04_05_2026`

One repo should use one date format in filenames.

For this repo, the standard is:

```
yyyy_mm_dd
```

---

## 8. Authority metadata rule

All canonical contracts and policies should begin with a short metadata block.

Required fields:

- `Status`
- `Owner`
- `Supersedes` or `Superseded by`
- `Last reviewed`

Recommended example:

```
Status: Canonical
Owner: Repo owner / architecture owner
Supersedes: docs/architecture/naming_contract_v1.md
Last reviewed: 2026-04-14
```

Allowed `Status` values:

- `Canonical`
- `Working`
- `Draft`
- `Archived`
- `Superseded`

### 8.1 Meaning of status values

- `Canonical` = current governing document
- `Working` = active but not yet authoritative
- `Draft` = incomplete and not enforceable
- `Archived` = kept for history only
- `Superseded` = replaced by a newer governing document

---

## 9. Superseded document rule

A document may remain in the repo after replacement, but it must not continue acting as current truth.

When a document is replaced:

1. mark the old file as `Superseded` or move it to archive
2. identify the replacement file explicitly
3. avoid citing the old file as current truth in new docs

This rule is especially important for:

- handover notes
- truth corrections
- checklist documents
- outdated benchmarks
- stale architecture assumptions

---

## 10. Folder responsibility clarification

### 10.1 `docs/`

`docs/` contains descriptive and explanatory material, such as:

- architecture
- contracts
- handover notes
- incidents
- diagrams
- reference documentation

`docs/` explains and records.

### 10.2 `policies/`

`policies/` contains normative rules and decision gates, such as:

- lifecycle rules
- retention rules
- documentation governance
- platform boundaries
- materialization rules
- semantic execution constraints

`policies/` constrains and governs.

### 10.3 `docs/authority/`

`docs/authority/` is reserved for repository truth-ordering documents, such as:

- source-of-truth manifest
- precedence rules
- canonical doc inventory

### 10.4 `tests/` inside dbt project

`dbt_patent_led/tests/` is reserved for dbt singular tests and dbt-executed SQL test assets.

### 10.5 root-level checks

Repository-level manual checks must not compete with dbt tests under the same ambiguous label.

Preferred future locations:

- `checks/warehouse/`
- `checks/search/`
- or `sql/checks/`

This separation should distinguish:

- dbt-executed tests
- manual or operational verification checks

---

## 11. Naming rules for checks and tests

### 11.1 dbt singular tests

Pattern:

```
test_<assertion>.sql
```

Examples:

- `test_family_collision.sql`
- `test_serving_lane_gap.sql`
- `test_publication_number_no_control_chars.sql`

### 11.2 Manual checks

Pattern:

```
check_<object_or_assertion>.sql
```

Examples:

- `check_publication_ipc.sql`
- `check_rawdata_patents.sql`
- `check_fact_publication_applicant.sql`

Use `test_` only when the artifact is part of a formal test mechanism.

Use `check_` for manual inspection or smoke validation.

---

## 12. Transition and cleanup rule

This contract does not require immediate mass renaming.

Cleanup should be gradual and only done when at least one of the following is true:

- a file is actively being edited
- a stale file is being replaced
- a directory is being reorganized under an approved policy
- a superseded file creates real confusion

Do **not** trigger repo-wide renaming just because a better naming rule now exists.

---

## 13. Immediate alignment decisions

The following are now adopted:

- canonical policy files should use `_v<major>.md`
- dated operational files should use `_yyyy_mm_dd.md`
- `README.md` remains the only uppercase markdown exception
- canonical files should carry `Status / Owner / Supersedes / Last reviewed`
- `docs/` and `policies/` must remain separate in responsibility
- dbt tests and manual checks should be distinguished by naming and folder role

---

## 14. Final principle

A good name should make three things obvious:

1. what the artifact is
2. whether it is explanatory or governing
3. whether it is current, historical, or replaced

If a name does not communicate role, scope, and status, it should be improved.