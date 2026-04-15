# Backup and Restore Policy v1

Status: Canonical  
Owner: Repo owner / platform owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines how backup and restore are handled for the governed patent analytics and retrieval platform.

It exists to answer the following questions clearly:

- what must be backed up
- what does not need full backup because it is rebuildable
- how restore priority is decided
- what is the recovery path for warehouse objects
- what is the recovery path for search-serving and semantic-serving assets
- which artifacts require snapshot-style recovery versus code-plus-rebuild recovery
- who owns recovery decisions

This policy is intended to reduce panic, unclear recovery expectations, and accidental loss of governed assets.

---

## 2. Scope

This policy applies to backup and restore planning for:

- repository governance documents
- SQL Server warehouse assets
- dbt project assets
- curated warehouse marts and serving source tables
- raw source snapshots retained for reproducibility
- Elasticsearch index definitions and live indices
- Chroma source artifacts and vector collections
- reviewer feedback and incident records
- selected benchmark and evaluation artifacts

This policy does not define retention windows in detail.
Retention timing is defined by:

- `policies/lifecycle/retention_policy_v1.md`

This policy does not define lifecycle states.
Lifecycle state rules are defined by:

- `policies/lifecycle/lifecycle_policy_v1.md`

---

## 3. Core backup principles

### 3.1 Backup follows recoverability needs

Not every artifact needs the same backup strategy.

Artifacts should be classified according to how they are recovered:

- direct restore from backup
- recreate from code and source
- rebuild from governed upstream assets
- archive-based historical recovery

### 3.2 Source of truth gets strongest recovery protection

The warehouse and its governed contracts deserve stronger recovery discipline than serving adapters.

### 3.3 Rebuildable serving assets do not always need deep backup

If an Elasticsearch index or Chroma collection can be rebuilt from governed upstream sources, rebuild may be preferred over full snapshot retention.

### 3.4 Definitions are often more valuable than live runtime state

Mappings, manifests, contracts, and source tables are often more important to preserve than ephemeral runtime products.

### 3.5 Restore priority must be explicit

Recovery should not start from whatever is easiest.
It should start from what re-establishes trusted system operation fastest.

---

## 4. Backup classes

This repository uses four backup classes.

### 4.1 Class A — Canonical source-of-truth assets

These are the most important to protect.

Typical examples:

- SQL Server curated warehouse assets
- stable marts
- dimensions and facts
- governance policies and contracts
- reviewer evidence records
- incident records
- source-of-truth manifests

Recovery expectation:
- direct restore preferred
- loss is high impact

### 4.2 Class B — Rebuildable but important governed assets

These are important, but can be reconstructed if inputs and definitions are intact.

Typical examples:

- dbt-generated warehouse outputs
- Elasticsearch source tables
- governed semantic input manifests
- selected benchmark packages

Recovery expectation:
- restore or rebuild depending on speed and trust needs

### 4.3 Class C — Serving adapter runtime assets

These are operationally useful but should be considered rebuildable if upstream governed assets remain intact.

Typical examples:

- Elasticsearch live indices
- Chroma vector collections
- temporary serving stores

Recovery expectation:
- rebuild usually preferred
- direct restore optional if rollback speed matters

### 4.4 Class D — Ephemeral technical artifacts

These have the weakest backup requirement.

Typical examples:

- scratch outputs
- temporary logs
- ad hoc exports
- local debugging files
- short-lived staging diagnostics

Recovery expectation:
- usually no formal backup
- rebuild or ignore

---

## 5. Backup policy by asset type

### 5.1 Repository governance documents

Artifacts:
- canonical policies
- contracts
- architecture docs
- source-of-truth manifest
- documentation governance artifacts

Backup policy:
- protected by Git history
- push to remote repository required
- important milestone branches should be preserved
- canonical document loss should be recoverable from Git, not only local disk

Restore policy:
- restore from Git first
- confirm latest canonical version
- confirm superseded status before reintroducing older file versions

### 5.2 SQL Server warehouse assets

Artifacts:
- curated marts
- dimensions
- facts
- bridge tables
- stable serving source tables
- important source/staging tables where rebuild cost is high

Backup policy:
- regular database-level backup is preferred
- pre-major-change snapshot recommended
- milestone or release-point backup strongly recommended
- critical serving source tables should not rely only on manual recreation

Restore policy:
- direct database restore preferred for Class A assets
- if full database restore is not appropriate, restore affected objects from governed DDL and controlled exports
- after restore, row counts and key contracts must be revalidated

### 5.3 dbt project assets

Artifacts:
- dbt models
- tests
- seed configuration
- documentation YAML
- model logic
- macros

Backup policy:
- Git is primary backup mechanism
- major structural refactors should be committed in small logical units
- important branch-based refactors should be pushed to remote before risky changes

Restore policy:
- restore from Git
- re-run `dbt seed`, `dbt run`, and `dbt test` as needed
- dbt is recovered primarily by code restore plus warehouse rebuild, not by raw file copy alone

### 5.4 Raw source snapshots

Artifacts:
- official IPC/CPC source packages
- retained patent source dumps
- milestone source snapshots

Backup policy:
- keep only selected governed snapshots
- back up source packages that are difficult, slow, or version-sensitive to reacquire
- do not treat every temporary raw pull as backup-worthy

Restore policy:
- preferred recovery path is re-fetch if reliable and deterministic
- if not safely reacquirable, restore from archived snapshot

### 5.5 Elasticsearch assets

Artifacts:
- index mappings
- analyzer definitions
- index creation scripts
- live indices

Backup policy:
- mapping JSON and creation scripts are mandatory long-lived assets
- live indices are optional deep-backup targets if rebuild is fast and governed source remains intact
- keep at least one rollback-capable release path for important index versions

Restore policy:
- first restore mapping definition and governed source table path
- then recreate index
- then reload from governed source
- only use direct index restore if snapshot infrastructure exists and time-to-recovery requires it

### 5.6 Chroma assets

Artifacts:
- embedding manifests
- governed semantic source manifests
- active vector collections

Backup policy:
- manifests and governed semantic input definitions are the most important artifacts
- collections may be treated as rebuildable if embeddings can be reproduced
- store enough version information to recreate collections confidently

Restore policy:
- restore manifests and dataset scope first
- then rebuild embeddings / vector collections
- direct collection restore is optional, not mandatory

### 5.7 Reviewer feedback and incident records

Artifacts:
- adjudication outputs
- override records
- incident notes
- corrective action logs
- review summaries

Backup policy:
- strong protection required
- these are evidence-class assets
- backup should be treated similarly to canonical governance artifacts

Restore policy:
- restore directly from governed storage or Git-controlled records
- verify completeness and chronology after restore

---

## 6. Restore priority order

In a recovery event, restore in this order unless a specific incident requires otherwise:

### Priority 1 — Governance and source-of-truth control
Restore first:

- canonical repository documents
- source-of-truth manifest
- SQL Server source-of-truth warehouse layer
- critical marts / dimensions / facts
- reviewer and incident evidence

Reason:
- without these, the platform may run but cannot be trusted

### Priority 2 — Warehouse transformation capability
Restore next:

- dbt project
- seed files
- transformation logic
- tests
- warehouse build scripts

Reason:
- these re-establish governed rebuild capability

### Priority 3 — Serving source assets
Restore next:

- BM25 source tables
- taxonomy source tables
- semantic source manifests
- dashboard-facing marts

Reason:
- these are the bridge between truth and serving

### Priority 4 — Serving adapters
Restore next:

- Elasticsearch mappings and indices
- Chroma collections
- search smoke-test queries

Reason:
- these are important for user-facing capability, but should depend on recovered truth

### Priority 5 — Convenience artifacts
Restore last:

- temporary logs
- scratch outputs
- ephemeral exports
- local debug files

---

## 7. Backup and restore strategy by platform component

| Component | Backup strategy | Restore strategy | Preferred recovery mode |
| --- | --- | --- | --- |
| Git-tracked governance docs | remote Git + branch history | Git restore | direct restore |
| dbt project | remote Git | Git restore + rerun dbt | code plus rebuild |
| SQL Server curated assets | DB backup / snapshot | DB restore + validation | direct restore preferred |
| SQL Server rebuildable assets | DB backup optional if rebuild cheap | dbt or SQL rebuild | rebuild or restore |
| Elasticsearch mappings | Git-tracked JSON | recreate index with mapping | direct restore of definitions |
| Elasticsearch live indices | optional snapshot / rollback window | recreate and reload | rebuild preferred |
| Chroma manifests | Git or governed storage | restore manifests | direct restore of definitions |
| Chroma collections | optional runtime backup | rebuild from manifest and source | rebuild preferred |
| Reviewer / incident evidence | governed storage + Git if doc-based | direct restore | direct restore preferred |
| Scratch/debug outputs | none or local only | no formal restore | ignore or rebuild |

---

## 8. Pre-change backup rule

Before any major architectural or serving change, perform a recovery-minded checkpoint.

Examples:

- renaming or restructuring governance folders
- replacing a serving source object
- changing BM25 source logic materially
- changing analyzer mappings materially
- replacing taxonomy source joins
- refactoring dbt build paths
- replacing a view with a table for an active consumer

Minimum checkpoint actions:

1. commit current repo state
2. push branch if work matters
3. capture affected warehouse object definitions
4. confirm current serving source row counts if relevant
5. preserve current mapping / manifest definitions

---

## 9. Restore validation rule

A restore is not complete merely because files or tables reappear.

After restore, validate at least the following where relevant:

- object existence
- row counts
- key uniqueness or expected cardinality
- source-to-serving alignment
- dbt test status
- smoke query success
- search index loadability
- semantic manifest consistency
- reviewer / incident record completeness

### 9.1 Rule

Recovery without validation is incomplete recovery.

---

## 10. Repository-specific interpretations

### 10.1 Patent warehouse is the primary trust anchor

This repository treats the warehouse and its governed contracts as the trust anchor.

Therefore:

- warehouse recovery has higher priority than serving engine recovery
- serving engines may be rebuilt from warehouse truth
- warehouse plus Git is more critical than live adapter runtime state

### 10.2 Search analyzers and mappings are backup-worthy

Analyzer and mapping definitions are part of system behavior.
They must be preserved even if indices themselves are rebuildable.

### 10.3 Semantic collections are secondary to manifests

For semantic-serving, the most important thing to preserve is:

- scope
- manifest
- model/version references
- governed input definition

The collection itself is important, but generally less important than the ability to reproduce it.

---

## 11. Ownership

### 11.1 Repo owner / platform owner

Owns the overall backup and restore policy and approves major recovery decisions.

### 11.2 Architecture owner

Owns recovery strategy for:

- major warehouse contracts
- serving source changes
- replacement path integrity

### 11.3 Data platform owner

Owns backup and restore planning for:

- SQL Server
- dbt recovery
- warehouse object rebuild path
- validation after restore

### 11.4 Search / semantic owner

Owns backup and restore planning for:

- Elasticsearch mappings and release paths
- Chroma manifests and rebuild procedures

### 11.5 Governance / review owner

Owns evidence preservation for:

- reviewer decisions
- incident records
- corrective action materials

---

## 12. Backup review cadence

Backup and restore readiness should be reviewed:

- before major repo restructures
- before major serving changes
- before demo milestones
- after important incidents
- when introducing a new serving adapter
- when changing canonical source paths
- when replacing key warehouse assets

Minimum recommendation:

- milestone-based review for active project changes
- quarterly review for core governed assets

---

## 13. Immediate repository decisions

The following decisions are now adopted:

1. Git is the primary backup for repository code and governance documents
2. SQL Server is the primary recovery priority for governed platform truth
3. dbt is recovered by code restore plus warehouse rebuild capability
4. Elasticsearch indices are generally rebuildable and do not automatically require deep backup
5. Elasticsearch mappings and analyzer definitions must be preserved
6. Chroma collections are generally rebuildable, but manifests and governed input definitions must be preserved
7. reviewer and incident evidence are high-value recovery targets
8. restore is incomplete until validation succeeds

---

## 14. Relationship to other policies

This policy should be read together with:

- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/lifecycle/retention_policy_v1.md`
- `policies/lifecycle/materialization_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`

Together these policies explain:

- what the asset is
- what state it is in
- how long it stays
- whether it is thin or materialized
- whether it should be restored or rebuilt

---

## 15. Final principle

A governed platform should always be able to answer two different questions:

1. "Can we restore this?"
2. "Should we restore this, or should we rebuild it from governed truth?"

The best backup strategy is not the one that saves everything.
It is the one that preserves trust, recoverability, and clarity.