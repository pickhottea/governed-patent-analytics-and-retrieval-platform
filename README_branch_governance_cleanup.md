# Branch README — Governance Cleanup and Reference Alignment

Status: Working branch document  
Branch: `feature/tests-checks-boundary-cleanup`  
Parent foundation branch: `feature/docs-policy-governance-foundation`  
Purpose: controlled trial space for governance implementation cleanup, reference alignment, and policy completeness testing

---

## 1. Why this branch exists

This branch exists to test governance implementation in practice before merging structural decisions into the main repository.

The goal is not to produce more documents only.
The goal is to verify whether current governance rules actually hold when applied to real warehouse objects, dbt models, tests, and source mappings.

This branch is intentionally used as a safe trial space to:

- test assumptions
- expose reference errors
- clean high-risk raw fields
- remove or reduce confusing duplicate objects
- validate whether current policies are complete enough
- decide what should be kept, merged, deprecated, or removed

This is a controlled optimization branch, not a documentation-only branch.

---

## 2. Core branch objective

This branch is used to improve the repository by working through the most failure-prone parts first.

The objective is:

1. clean the dirtiest raw/staging areas first
2. verify source and object references end-to-end
3. test whether naming and boundary policies are strong enough
4. remove or merge unnecessary tables and views where justified
5. only promote changes that reduce confusion and improve governance clarity

This branch exists to support trial, correction, and convergence.

---

## 3. What this branch is testing

This branch is testing five things at once:

### 3.1 Raw-to-canonical boundary clarity

Can we clearly distinguish:

- raw passthrough staging
- normalized staging
- canonical intermediate logic
- serving-ready output

### 3.2 Source registry correctness

Do dbt sources, SQL objects, YAML tests, and real warehouse objects all refer to the same thing?

### 3.3 Naming policy usefulness

Does the current naming policy actually help prevent wrong references, wrong schemas, and ambiguous objects?

### 3.4 Test strategy usefulness

Do generic tests and singular tests catch the right kinds of failures?

### 3.5 Object sprawl control

Are there duplicated, stale, or overlapping tables/views that should be merged, deprecated, or removed?

---

## 4. Current working hypothesis

The current repository issues are not caused by one single problem.

The working hypothesis is that repeated failures come from a combination of:

- incomplete source-to-object alignment
- inconsistent schema/object naming across layers
- raw models being treated like canonical models
- insufficient follow-through after earlier reference failures were discovered
- duplicated or overlapping objects that were not explicitly retired

This branch is intended to test that hypothesis.

---

## 5. Scope of work in this branch

### In scope

- cleaning `stg_ops_family_members`
- testing raw vs canonical field boundaries
- validating source registry and dbt source mappings
- validating YAML column definitions against actual model output
- validating dbt test references against real objects and columns
- moving manual SQL checks out of root `tests/`
- separating dbt singular tests from manual warehouse checks
- identifying objects that should be merged or removed
- deciding whether current policies need revision after implementation trials

### Out of scope for now

- large-scale expansion of gold layer objects
- adding more serving abstractions before reference hygiene is fixed
- broad semantic pipeline redesign
- dashboard redesign
- adding new systems only to work around unclear current ones

This branch is for cleanup and verification before expansion.

---

## 6. Branch priorities

### Priority 1 — Clean the dirtiest area first

The first target is `stg_ops_family_members`.

Reason:

- it is visibly dirty
- it exposes raw-versus-canonical confusion clearly
- it is a good stress test for current policy completeness

Expected work:

- identify real source columns
- preserve raw source fields
- add cleaned/canonicalized fields where needed
- keep tests that expose dirty raw data
- decide whether a canonical intermediate model is required

### Priority 2 — Fix reference alignment

The second target is reference hygiene across:

- `sources.yml`
- dbt model SQL
- model YAML
- singular tests
- actual warehouse objects

Expected work:

- confirm objects really exist
- confirm schema names are correct
- confirm YAML columns match actual output columns
- confirm tests target enabled nodes only
- confirm source names do not silently point to legacy or missing objects

### Priority 3 — Review naming policy by implementation evidence

The third target is policy evaluation.

Expected work:

- assess whether current naming rules prevented confusion
- assess whether the problem is naming, implementation discipline, or both
- revise policy only where trial evidence shows a real gap

### Priority 4 — Reduce unnecessary object sprawl

The fourth target is object cleanup.

Expected work:

- identify views/tables with duplicated purpose
- identify legacy objects that still create ambiguity
- decide whether to merge, deprecate, or remove them
- avoid keeping parallel objects without explicit reason

---

## 7. Working principles for this branch

### 7.1 Fix the smallest high-risk thing first

Do not widen scope before the immediate reference and cleanliness problems are understood.

### 7.2 Do not add new objects casually

Every new table or view increases ambiguity unless it clearly reduces confusion.

### 7.3 Prefer clarification over expansion

When a failure appears, first determine whether the issue is:

- wrong source mapping
- wrong schema/object name
- wrong column assumption
- dirty raw data
- duplicated object authority

Only then decide whether a new object is needed.

### 7.4 Keep failed tests when they reveal real dirt

If a singular test exposes real dirty raw content, do not remove it merely to get green results.
Instead, use it to define the correct boundary between raw and canonical layers.

### 7.5 Policies must be tested by implementation

A policy is not considered proven merely because it was written.
It must survive contact with real dbt models, real SQL objects, and real warehouse data.

---

## 8. Current known problems being worked through

The following problems are already visible and are part of this branch’s purpose:

### 8.1 `stg_ops_family_members` is raw passthrough and still dirty

Current state:

- JSON-like artifacts remain in member publication fields
- raw source is being evaluated against canonical expectations

### 8.2 Source registry / object naming misalignment exists

Current state:

- some dbt source references do not match actually existing objects
- some model/test paths still assume object names or schemas that are not valid

### 8.3 Same-name object drift may exist across schemas

Current state:

- the same logical object may exist in more than one schema with different behavior or row counts

### 8.4 Reference errors have repeated more than once

Current state:

- repeated failures suggest not only naming ambiguity, but also insufficient end-to-end review after earlier issues were found

---

## 9. Expected deliverables from this branch

This branch is expected to produce the following outcomes.

### Deliverable A — cleaned OPS family member handling

One of the following must be produced:

- a cleaned `stg_ops_family_members`
- or a clear split between raw staging and canonical intermediate cleanup

### Deliverable B — source/reference alignment pass

A reviewed and corrected mapping between:

- dbt sources
- dbt models
- YAML tests
- real warehouse objects

### Deliverable C — test boundary clarity

Clear separation between:

- dbt generic tests
- dbt singular tests
- manual warehouse SQL checks

### Deliverable D — object cleanup decisions

A reviewed decision set for:

- which objects remain
- which objects are merged
- which objects are deprecated
- which objects are removed

### Deliverable E — policy revision decision

A decision on whether current governance policies are already sufficient or need targeted revision after implementation trial.

---

## 10. Decision rules for removing or merging objects

A table or view should be considered for merge or removal if one or more of the following are true:

- it duplicates another object’s purpose
- it has the same name as another authoritative object in a different schema and causes ambiguity
- it exists only for historical convenience and creates reference drift
- it is no longer referenced by the governed path
- its purpose can be cleanly absorbed into a better-defined object

A table or view should not be removed merely because it is inconvenient.
Removal must improve clarity, not just reduce surface area.

---

## 11. Test strategy for this branch

### Generic tests are used for:

- not null
- unique
- accepted values
- relationships
- stable model-level uniqueness combinations

### Singular tests are used for:

- collision checks
- duplicate pair checks
- raw dirt exposure
- serving-lane mismatches
- reference/pathology cases that generic tests do not express well

### Manual SQL checks are used for:

- ad hoc warehouse inspection
- human-reviewed evidence
- exploratory diagnostics
- verification before making structural cleanup decisions

---

## 12. Success criteria

This branch is successful if, by the end of the review:

- the dirtiest raw/staging area is understood and partially cleaned
- source references are aligned with real objects
- YAML tests no longer assume nonexistent columns or objects
- singular tests clearly distinguish raw dirt from canonical expectations
- unnecessary duplicate or legacy objects are identified
- at least one set of cleanup decisions is ready to merge
- policy revisions, if needed, are evidence-based rather than speculative

---

## 13. Failure criteria

This branch is failing if:

- more objects are added without reducing ambiguity
- tests are removed merely to hide real dirt
- source mappings remain unverified
- naming policy is blamed without checking implementation discipline
- cleanup work expands scope without improving clarity

---

## 14. Relationship to existing governance documents

This branch builds on existing governance foundation documents but is not meant to blindly trust them.

These documents provide the starting framework:

- `docs/architecture/naming_contract_v2.md`
- `docs/authority/source_of_truth_manifest_v1.md`
- `policies/documentation/documentation_governance_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`
- lifecycle policies under `policies/lifecycle/`

This branch is where those documents are tested against reality.

If implementation reveals a gap, the policy may need to be refined.
If implementation violates a sound policy, execution discipline must be corrected.

---

## 15. Final principle

This branch exists to prove governance by execution.

Not by writing more rules only.
Not by adding more objects only.
Not by hiding errors.

The purpose is to try, break, inspect, clean, align, and then keep only what actually improves clarity and control.