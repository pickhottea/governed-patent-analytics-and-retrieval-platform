# Lifecycle Policy v1

Status: Canonical  
Owner: Repo owner / governance owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines the lifecycle states used in this repository for governed data products, serving assets, and governance-relevant artifacts.

It exists to make the following things explicit:

- when an object has only been captured
- when it has been normalized
- when it has been resolved into canonical form
- when it is considered curated and serving-ready
- when it is under review or monitoring
- when it has been deprecated
- when it should be archived or removed

This policy is intended to reduce ambiguity around "what stage something is in" and to prevent unstable objects from being treated as production-valid.

---

## 2. Scope

This policy applies to lifecycle handling for:

- raw source snapshots
- warehouse source tables
- staging models
- normalized and resolved warehouse objects
- marts and curated serving tables
- Elasticsearch source tables and indices
- Chroma source artifacts and vector stores
- reviewer feedback artifacts
- logs, incident records, and governance evidence
- benchmark and evaluation artifacts where lifecycle matters

This policy does not define exact storage durations.
Retention timing is handled separately by:

- `policies/lifecycle/retention_policy_v1.md`

This policy does not define tool ownership boundaries.
Tool boundaries are handled separately by:

- `policies/platform/platform_boundary_and_operating_model_v1.md`

---

## 3. Lifecycle principles

### 3.1 Lifecycle follows function

Objects are managed according to what they do in the platform, not simply by where they live.

### 3.2 Lifecycle is state-based

An object should have a known state, not just a folder location.

### 3.3 Not all objects are long-lived

Some objects are transitional and rebuildable.
Others are durable and serving-critical.

### 3.4 Curated does not mean permanent

An object may be curated today and deprecated tomorrow if a better governed replacement exists.

### 3.5 Historical material is allowed, but must be marked

A historical object may remain in the repo or warehouse for traceability, but it must not silently act as current truth.

---

## 4. Lifecycle state model

This repository adopts the following lifecycle states:

1. `ingested`
2. `normalized`
3. `resolved`
4. `curated`
5. `reviewed`
6. `monitored`
7. `deprecated`
8. `archived`
9. `purged`

These states do not require every object to pass through every stage.
However, they define the approved lifecycle vocabulary for the project.

---

## 5. State definitions

### 5.1 `ingested`

An object is `ingested` when source material has been captured into the governed environment.

Typical examples:

- raw downloaded source files
- warehouse source loads
- raw API results saved for processing
- source snapshots used for reproducibility

Conditions:

- source provenance is known
- the object has been captured successfully
- no claim is yet made that the object is normalized or serving-ready

`ingested` objects may still be messy, duplicated, incomplete, or source-shaped.

---

### 5.2 `normalized`

An object is `normalized` when raw structural variability has been controlled enough for downstream use.

Typical normalization actions:

- trimming
- standard casing
- type casting
- date normalization
- null handling
- controlled code cleanup
- basic column renaming
- source field alignment

Conditions:

- the object has a stable enough shape for repeatable downstream processing
- obvious formatting conflicts have been resolved
- the object is not yet necessarily canonical across sources

A normalized object is cleaner than ingested data, but not yet fully resolved.

---

### 5.3 `resolved`

An object is `resolved` when canonical identities, joins, or structural mappings have been stabilized.

Typical examples:

- canonical publication identity
- family identity resolution
- canonical IPC/CPC code alignment
- cross-source reconciliation outputs
- stable relationship bridges

Conditions:

- grain is known
- identity rules are enforced
- major reconciliation logic is in place
- the object can be reliably joined downstream

A resolved object is structurally dependable, even if it is not yet packaged for direct serving.

---

### 5.4 `curated`

An object is `curated` when it is stable enough for direct analytical, serving, or user-facing use.

Typical examples:

- dimensions
- facts
- marts
- governed serving views
- Elasticsearch source tables
- dashboard-facing outputs

Conditions:

- grain is explicit
- business meaning is clear
- downstream purpose is known
- quality is sufficient for governed usage
- the object is intentionally exposed or consumed

Curated means serving-ready within governed scope.
It does not guarantee that the object is immutable forever.

---

### 5.5 `reviewed`

An object is `reviewed` when a meaningful human or governance review step has been completed and recorded.

Typical examples:

- reviewer feedback artifacts
- approved benchmark results
- manually verified release candidates
- adjudicated retrieval results
- human-checked incident resolutions

Conditions:

- review scope is known
- reviewer action is recorded
- review outcome is traceable

Not every object requires a reviewed state.
This state is used when human judgment matters.

---

### 5.6 `monitored`

An object is `monitored` when it is active and under ongoing operational or governance observation.

Typical examples:

- production-like marts used by dashboards
- active Elasticsearch indices
- semantic serving artifacts under evaluation
- query logs
- data quality metrics
- freshness metrics
- retrieval quality signals

Conditions:

- the object is actively used
- health or quality signals exist
- issues can be detected through logs, metrics, or review loops

A monitored object is not necessarily canonical, but it is operationally live enough to observe.

---

### 5.7 `deprecated`

An object is `deprecated` when it should no longer be treated as the preferred current path.

Typical reasons:

- a better replacement exists
- the contract is outdated
- the logic is broken or legacy-shaped
- the object remains only for transition support

Conditions:

- a replacement exists or deprecation rationale is explicit
- contributors are expected not to build new dependencies on it
- continued existence is transitional, not preferred

Deprecated objects may still be readable, but should not attract new downstream consumers.

---

### 5.8 `archived`

An object is `archived` when it is retained for history, auditability, or traceability, but is not part of the active path.

Typical examples:

- old incident notes
- superseded policies
- retired benchmarks
- replaced mapping definitions
- old run artifacts kept for evidence

Conditions:

- the object is no longer active
- the object still has reference or audit value
- it is clearly historical

Archived objects are allowed to remain, but must not silently behave like active truth.

---

### 5.9 `purged`

An object is `purged` when it has been removed from active storage or active repo presence because it no longer justifies retention.

Typical reasons:

- rebuildable and expired
- superseded and no longer needed
- debug-only and obsolete
- no audit or rollback value remains

Conditions:

- retention requirements are satisfied
- no active dependency remains
- removal is intentional

`purged` is an end-of-life state.

---

## 6. Lifecycle transitions

### 6.1 Standard transition path

A common path is:

```text id="nuk9g9"
ingested
-> normalized
-> resolved
-> curated
-> monitored
-> deprecated
-> archived
-> purged
```
### 6.2 Optional review path

When human review matters:

```
curated
-> reviewed
-> monitored
```

### 6.3 Important note

Not every object must pass through every state.

Examples:

- a raw source snapshot may go from `ingested` to `archived`
- a temporary debug output may go from `normalized` to `purged`
- a benchmark artifact may go from `reviewed` to `archived`
- a serving object may go from `curated` to `monitored` without a separate human review step

---

## 7. Lifecycle rules by object type

### 7.1 Raw source files

Expected states:

```
ingested -> archived -> purged
```

Raw source files are primarily for provenance, rerun support, and auditability.

They should not be treated as directly serving-ready.

---

### 7.2 Warehouse staging objects

Expected states:

```
ingested -> normalized -> resolved
```

Staging objects exist to shape and stabilize raw data for downstream use.

They should not be treated as final business-serving outputs unless explicitly elevated.

---

### 7.3 Dimensions, facts, and marts

Expected states:

```
resolved -> curated -> monitored
```

These objects are usually the core warehouse serving layer.

When replaced, they may become:

```
deprecated -> archived
```

---

### 7.4 Elasticsearch source tables and indices

Expected states:

```
curated -> monitored -> deprecated -> archived or purged
```

The warehouse source table and the index do not need identical timelines, but both must remain governable.

The index must always be rebuildable from governed upstream sources.

---

### 7.5 Chroma source artifacts and vector stores

Expected states:

```
curated -> monitored -> deprecated -> archived or purged
```

Version control and dataset scope must be clear before vector-serving artifacts are treated as meaningful.

---

### 7.6 Policy and contract documents

Expected states:

```
draft -> canonical -> superseded/deprecated -> archived
```

A contract or policy should never remain "implicitly current" after being replaced.

---

### 7.7 Incident and benchmark notes

Expected states:

```
working/reviewed -> archived
```

These are evidence-like documents, not default governing truth.

---

## 8. Release readiness and lifecycle

An object must not be treated as release-ready merely because it exists.

### 8.1 Minimum release readiness signals for curated objects

A curated object should generally have:

- explicit grain
- stable naming
- known owner
- defined downstream role
- known source path
- acceptable quality
- no hidden dependency on unstable manual logic

### 8.2 Additional signals for monitored objects

A monitored object should also have:

- freshness visibility
- failure visibility
- traceability to source and transformation path
- a known replacement path if later deprecated

---

## 9. Deprecation rules

An object should be marked `deprecated` when any of the following are true:

- a governed replacement exists
- the old path is legacy-shaped
- the object causes confusion
- the contract is known to be wrong or outdated
- new consumers should no longer depend on it

### 9.1 Deprecation requirements

When deprecating an object, document:

- why it is deprecated
- what replaces it
- whether downstream users must migrate
- whether rollback is possible

### 9.2 Rule

Do not silently deprecate objects.

Deprecation must be explicit.

---

## 10. Archival rules

An object should be archived when:

- it is no longer active
- it still has trace or evidence value
- it has historical or audit relevance
- deletion is not yet appropriate

Archive does not mean "maybe current."

Archive means "kept intentionally, but not active."

---

## 11. Purge rules

An object may be purged when all are true:

1. it has no active downstream dependency
2. it is no longer current
3. retention requirements are satisfied
4. audit or trace value is no longer needed
5. rebuildability or safe removal has been confirmed where relevant

Objects should not be purged merely because they are inconvenient.

---

## 12. Lifecycle state documentation rule

For important assets, lifecycle state should be inferable from one or more of the following:

- document metadata
- folder placement
- release note
- deprecation note
- source-of-truth manifest
- warehouse documentation
- policy registry

If nobody can tell whether something is current, deprecated, or historical, lifecycle governance is insufficient.

---

## 13. Current repository interpretations

### 13.1 Bronze-like materials

Typically correspond to:

- `ingested`

Examples:

- raw captures
- raw snapshots
- downloaded source files

### 13.2 Silver-like materials

Typically correspond to:

- `normalized`
- `resolved`

Examples:

- staging outputs
- canonical identity resolution layers
- cleaned relational shaping layers

### 13.3 Gold-like materials

Typically correspond to:

- `curated`
- `monitored`

Examples:

- dimensions
- marts
- serving-facing tables and views
- search source tables

### 13.4 Notes on staging

`staging` is a modeling role, not a full lifecycle state by itself.

A staging model may represent `normalized` or `resolved` lifecycle states depending on its function.

---

## 14. Review cadence

Lifecycle assignments should be revisited when:

- a view becomes a table
- a source becomes deprecated
- a new serving layer is introduced
- a dashboard begins to depend on an object
- a search index becomes operationally important
- a semantic artifact becomes review-relevant
- a policy or contract supersedes an old path

Minimum recommendation:

- review lifecycle classification at major milestones
- review again before demo, handover, or merge of major architectural changes

---

## 15. Immediate repository decisions

The following decisions are now adopted:

1. lifecycle states in this repo use the vocabulary defined in this policy
2. not every object is automatically curated just because it exists
3. monitored objects are active and observable, not merely stored
4. deprecated objects must be explicitly marked
5. archived objects are historical, not current
6. purged objects are intentionally removed, not casually forgotten
7. staging is a modeling role and must not be confused with lifecycle state
8. gold-like outputs usually correspond to curated or monitored states, not merely completed SQL

---

## 16. Relationship to other policies

This policy should be read together with:

- `policies/lifecycle/retention_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`
- `policies/documentation/documentation_governance_policy_v1.md`

Together they define:

- what things are
- what state they are in
- how long they remain
- where truth lives
- when they should be replaced

---

## 17. Final principle

A governed platform does not only know what objects exist.

It also knows:

- what state each important object is in
- whether it is active or historical
- whether it is transitional or stable
- whether it should still be trusted as current

If lifecycle state is unclear, governance is incomplete.

```

