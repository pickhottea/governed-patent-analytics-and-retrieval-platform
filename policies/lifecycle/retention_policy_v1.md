# Retention Policy v1

Status: Canonical  
Owner: Repo owner / governance owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines how long important artifacts should be retained in this repository and platform.

It exists to answer the following questions clearly:

- what should be kept during build and debugging
- what should be kept after build for governed serving
- what can be rebuilt and safely removed
- what must remain for traceability, reviewability, and auditability
- which artifacts are short-lived versus durable
- when an artifact should be archived instead of deleted

This policy is intended to reduce storage drift, unclear cleanup behavior, and accidental loss of evidence or reproducibility.

---

## 2. Scope

This policy applies to retention decisions for:

- raw source files
- staging and intermediate outputs
- dbt-generated warehouse assets
- marts and curated serving sources
- Elasticsearch source tables and indices
- Chroma source artifacts and vector stores
- logs and run artifacts
- reviewer feedback artifacts
- incident records
- benchmark and evaluation artifacts
- policy and contract documents where archival matters

This policy does not define lifecycle state names.
Lifecycle states are defined by:

- `policies/lifecycle/lifecycle_policy_v1.md`

This policy does not define platform tool boundaries.
Tool boundaries are defined by:

- `policies/platform/platform_boundary_and_operating_model_v1.md`

---

## 3. Retention principles

### 3.1 Retention follows function, not patent term

Artifacts are retained based on their operational, governance, and traceability role in the platform.

Patent legal duration is not the retention clock for platform artifacts.

### 3.2 Rebuildable is not the same as disposable

An artifact may be rebuildable, but still deserve temporary retention for:

- debugging
- reproducibility
- rollback
- incident analysis
- comparison across runs

### 3.3 Serving-critical objects must outlive build artifacts

Short-lived build outputs should not be retained as long as curated marts, governed serving sources, or review evidence.

### 3.4 Evidence must outlive convenience

Artifacts that support traceability, reviewability, incident handling, or governance decisions should generally be retained longer than temporary technical outputs.

### 3.5 Archive before purge when history matters

If an artifact may be useful for audit, investigation, benchmark comparison, or handover, prefer archival before deletion.

### 3.6 No silent retention drift

If a class of artifact is repeatedly accumulating without a retention reason, that class must be reviewed and governed explicitly.

---

## 4. Retention classes

This repository uses five retention classes.

### 4.1 Ephemeral

Short-lived technical artifacts used for immediate debugging or temporary reruns.

Typical examples:

- scratch outputs
- temporary local debug files
- transient notebook exports
- one-off comparison files

### 4.2 Short-term operational

Artifacts kept long enough to support reruns, troubleshooting, build comparison, and recent operational validation.

Typical examples:

- recent run logs
- recent raw snapshots
- recent benchmark outputs
- recent staging rebuild support files

### 4.3 Medium-term reproducibility

Artifacts kept to support reproducibility across milestones, releases, and controlled comparisons.

Typical examples:

- release candidate evaluation outputs
- governed source snapshots for a milestone
- reviewed benchmark results
- selected retrieval evaluation packages

### 4.4 Long-term governed serving

Artifacts that support stable platform use, business reporting, or governed retrieval.

Typical examples:

- curated marts
- dimensions and facts
- stable serving source tables
- controlled index-source definitions

### 4.5 Long-term evidence and auditability

Artifacts retained primarily for traceability, human review, governance defense, incident analysis, or portfolio demonstration credibility.

Typical examples:

- reviewer decisions
- incident records
- governance policies
- truth-correction notes
- release notes
- selected benchmark evidence

---

## 5. Build-stage retention table

Build-stage retention applies to artifacts created while developing, debugging, validating, or rerunning the platform.

| Artifact class | Examples | Why retain | Default retention | Default action after expiry |
| --- | --- | --- | --- | --- |
| Raw source snapshots used for active build | downloaded CPC/IPC files, source extracts, raw patent snapshots | rerun support, provenance, debugging | 30 days from successful downstream stabilization | archive or purge depending on trace value |
| Temporary build logs | local run logs, load logs, ad hoc troubleshooting logs | debug recent failures | 14 days | purge |
| Staging/intermediate debug outputs | temp CSVs, join diagnostics, investigation extracts | support recent troubleshooting | 14 days | purge |
| Benchmark candidate outputs | candidate comparisons, temporary scoring files | compare recent alternatives | 30 days | archive selected winners, purge the rest |
| Search-index rebuild support files | temporary JSON payloads, export batches, staging-to-index dumps | verify index load issues | 14 days | purge |
| Semantic experiment scratch outputs | temporary embedding runs, test result dumps | compare recent experiment behavior | 30 days | archive selected milestone outputs, purge the rest |
| Local notebook scratch artifacts | one-off screenshots, exploratory CSVs, draft notes | immediate exploration only | 7 days | purge |
| Failed run evidence with unresolved issue | logs, error snapshots, broken intermediate outputs | incident / debugging support | until issue closure plus 14 days | archive if important, otherwise purge |

### 5.1 Build-stage rule

Build-stage artifacts are kept because they help explain recent work.
They should not silently become permanent platform assets.

### 5.2 Build-stage release rule

Once a build path is stabilized and a governed replacement exists, temporary artifacts should be reviewed and either:

- promoted into a governed class
- archived selectively
- purged

---

## 6. Post-build lifecycle retention table

Post-build retention applies to stable, governed, or externally consumable artifacts.

| Artifact class | Examples | Why retain | Default retention | Default action after expiry |
| --- | --- | --- | --- | --- |
| Curated warehouse marts | Power BI-facing marts, governed retrieval marts, dimensions, facts | stable analytical and serving use | retain while active plus 12 months after replacement | archive metadata, purge only when safe |
| Stable serving source tables | BM25 source tables, taxonomy serving sources, curated search export tables | rebuild search-serving systems and preserve traceability | retain while active plus 12 months after replacement | archive contract and lineage reference, then review purge |
| Elasticsearch index definitions | mapping JSON, analyzer definitions, release versions | rebuildability and search traceability | retain indefinitely while referenced by active or historical releases | archive old versions, do not silently remove |
| Active Elasticsearch indices | live search indices | search-serving operations | retain while active; remove replaced indices after 30 days if rebuildable and not needed for rollback | purge replaced index |
| Chroma governed source artifacts | embedding manifests, dataset scope manifests, governed semantic input sets | semantic reproducibility and evaluation traceability | retain while active plus 6 months after replacement | archive selected milestone artifacts |
| Chroma vector stores | active vector collections | semantic-serving operations | retain while active; replaced collections retained 30 days for rollback unless stronger evidence need exists | purge replaced store |
| Query logs and retrieval traces | retrieval logs, trace evidence records, query outcome logs | quality analysis, reviewer loop, incident analysis | 12 months | archive summarized trends, purge raw logs if allowed |
| Reviewer feedback artifacts | adjudication results, override decisions, review comments | reviewability and governance evidence | 24 months | archive |
| Incident records | incident notes, root cause records, corrective action logs | auditability and learning | 36 months | archive |
| Benchmark and evaluation packages | milestone retrieval comparisons, approved benchmark evidence | reproducibility and portfolio credibility | 24 months for milestone packages; temporary candidates shorter | archive selected milestone packages |
| Policies and contracts | canonical governance docs, superseded policies, architecture contracts | authority, traceability, handover | active canonical docs retained indefinitely; superseded docs archived indefinitely unless explicitly cleaned under authority control | archive, do not casually purge |
| README and navigation docs | repo overview, folder index docs | onboarding and orientation | retain while relevant | update or supersede, not silent purge |

---

## 7. Minimum retention guidance by object type

### 7.1 Raw source files

Raw source files should usually be retained long enough to support:

- reruns
- provenance checks
- incident investigation
- regeneration of staging outputs

Default guidance:

- keep recent active-source snapshots for 30 days
- retain milestone or release-significant source packages longer if they support reproducibility
- archive official source packages that are hard to reacquire or important for evidence

### 7.2 Staging and intermediate outputs

Staging and intermediate artifacts should usually be retained only while they are operationally useful.

Default guidance:

- short-lived
- recent debugging only
- purge when replaced and no incident or rerun need remains

Staging should not become a long-term archive category by accident.

### 7.3 Curated warehouse objects

Curated warehouse objects are core governed assets.

Default guidance:

- retain while active
- after replacement, retain at least until transition risk is gone
- do not purge immediately after replacement if Power BI, Streamlit, or serving adapters may still depend on them

### 7.4 Search-serving objects

Search-serving definitions deserve longer retention than live indices.

Default guidance:

- keep mapping and analyzer definitions as long-term reproducibility assets
- keep live indices only as long as operationally needed
- allow replaced indices short rollback windows before purge

### 7.5 Semantic-serving artifacts

Semantic artifacts should be retained according to whether they support:

- active serving
- evaluation reproducibility
- milestone comparison

Keep manifests and governed scope references longer than temporary vector collections.

### 7.6 Logs, traces, and reviewer signals

These artifacts often matter more than people expect.

Default guidance:

- keep enough recent history to identify patterns
- keep governance-relevant review artifacts longer than raw operational logs
- prefer summarization plus controlled archival when raw logs become too large

---

## 8. Retention rules by lifecycle state

### 8.1 `ingested`

Usually short-term operational unless source provenance or reproducibility requires longer retention.

### 8.2 `normalized`

Usually short-term to medium-term, depending on debugging and rerun needs.

### 8.3 `resolved`

May justify medium-term retention if it serves as a stable transition layer or reusable canonical join layer.

### 8.4 `curated`

Usually long-term governed serving retention.

### 8.5 `reviewed`

Usually medium-term to long-term evidence retention.

### 8.6 `monitored`

Retain as long as active use and observability matter.

### 8.7 `deprecated`

Retain long enough for transition clarity, rollback, and safe consumer migration.

### 8.8 `archived`

Retain intentionally for traceability or evidence; do not treat as active.

### 8.9 `purged`

No longer retained in active storage or active repo presence.

---

## 9. Archive versus purge decision rule

When deciding whether to archive or purge, apply this sequence:

### 9.1 Archive if any are true

- the artifact supports auditability
- the artifact supports portfolio credibility or interview reproducibility
- the artifact records an important incident or correction
- the artifact represents a released milestone
- the artifact may be needed to explain why a later design exists
- the artifact is referenced by another canonical document

### 9.2 Purge if all are true

- the artifact is rebuildable
- the artifact has no active dependency
- the artifact has no remaining audit or incident value
- the retention window has expired
- no milestone or release depends on it
- its absence will not create ambiguity

---

## 10. Repository-specific interpretations

### 10.1 Patent warehouse outputs

The following generally deserve long-term governed retention while active:

- dimensions
- facts
- marts
- curated taxonomy lookup layers
- stable BM25 source tables
- dashboard-facing aggregates

### 10.2 IPC/CPC source and mapping assets

The following often deserve medium-term to long-term retention:

- official source packages
- parsed seed files that are hard to regenerate casually
- index mapping definitions
- curated code description references

### 10.3 Search assets

Retain longer:

- analyzer and mapping JSON
- release notes for index definitions
- chosen smoke-test examples

Retain shorter:

- temporary export batches
- transient index build payloads
- local one-off debugging artifacts

### 10.4 Documentation artifacts

Retain longer:

- canonical policies
- canonical contracts
- truth-correction notes with governance impact
- incident files with architectural impact

Retain shorter or archive selectively:

- ad hoc scratch notes
- temporary checklist variants
- duplicate draft documents

---

## 11. Retention ownership

Retention responsibility follows artifact function.

### 11.1 Repo owner / governance owner

Owns retention policy, archive discipline, and decisions for canonical governance documents.

### 11.2 Architecture owner

Owns retention decisions for architecture contracts, major replacement paths, and serving-critical definitions.

### 11.3 Data platform owner

Owns retention decisions for warehouse outputs, staging support artifacts, and serving source tables.

### 11.4 Search / semantic owner

Owns retention decisions for Elasticsearch and Chroma operational artifacts, subject to platform governance.

### 11.5 Reviewer / governance workflow owner

Owns retention decisions for adjudication outputs, reviewer notes, and evidence-like trace artifacts.

---

## 12. Review cadence

Retention classes should be reviewed:

- at major milestones
- before handover
- before large cleanup
- when introducing a new serving lane
- when replacing a major warehouse asset
- when storage growth becomes noticeable
- when an incident reveals that too little or too much was retained

Minimum recommendation:

- quarterly review for active governed assets
- milestone review for search / semantic release assets
- pre-demo review for evidence and benchmark artifacts

---

## 13. Immediate repository decisions

The following decisions are now adopted:

1. retention follows function, not patent duration
2. build-stage outputs are usually short-lived unless they support reproducibility or incident analysis
3. curated marts and serving source tables are long-lived governed assets
4. search and semantic live stores may be shorter-lived than the governed source artifacts that feed them
5. analyzer and mapping definitions are long-lived reproducibility assets
6. reviewer feedback, incident records, and truth-correction materials should outlive short-term technical convenience
7. archival is preferred over silent accumulation or casual deletion
8. purge is allowed only after dependency, evidence, and retention checks are satisfied

---

## 14. Relationship to other policies

This policy should be read together with:

- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`
- `policies/documentation/documentation_governance_policy_v1.md`

These documents together explain:

- what an artifact is
- what state it is in
- what role it plays
- how long it should remain
- when it should transition out of active use

---

## 15. Final principle

A governed platform should be able to explain not only how an artifact was created, but also:

- why it is still being kept
- why it can be removed
- why it must remain for traceability
- why a temporary file should not become permanent by accident

If retention cannot be justified, it should be reviewed.
If deletion cannot be justified, it should also be reviewed.