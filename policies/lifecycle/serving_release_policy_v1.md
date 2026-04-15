# Serving Release Policy v1

Status: Canonical  
Owner: Repo owner / platform owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines when a serving path is considered release-ready in this repository.

It exists to answer the following questions clearly:

- when a warehouse object is ready to feed a serving layer
- when Elasticsearch is ready to be treated as a governed search-serving path
- when Chroma is ready to be treated as a governed semantic-serving path
- when Power BI is allowed to consume a mart
- when Streamlit is allowed to expose a retrieval or explanation workflow
- when analyzer design becomes a release gate rather than a future improvement
- what minimum validation is required before a serving path is trusted

This policy is intended to reduce the pattern of "it runs, therefore it is released."

---

## 2. Scope

This policy applies to release readiness for:

- warehouse serving source tables
- lightweight serving lookup views
- Elasticsearch-backed BM25 serving
- Chroma-backed semantic serving
- Power BI-facing marts
- Streamlit user-facing retrieval interfaces
- taxonomy lookup serving
- analyzer-bound search paths
- benchmark-backed retrieval release candidates

This policy does not define:

- retention duration
- lifecycle state vocabulary
- platform tool boundaries
- low-level index mapping syntax

Those are governed by:

- `policies/lifecycle/retention_policy_v1.md`
- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/platform/platform_boundary_and_operating_model_v1.md`

---

## 3. Core release principles

### 3.1 Running is not release

A workflow is not release-ready merely because a script finishes successfully.

### 3.2 Release requires trust signals

A serving path is release-ready only when its upstream source, transformation logic, and serving behavior are all sufficiently understood.

### 3.3 Governed source first

No serving layer should be treated as reliable unless the governed warehouse source is identified and stable enough.

### 3.4 Release depends on role

Different serving consumers require different release criteria.

Examples:

- Power BI requires mart stability
- Elasticsearch requires analyzer and query behavior validation
- Chroma requires dataset scope and manifest clarity
- Streamlit requires stable interaction paths and traceable outputs

### 3.5 Release is reversible

A serving release should support rollback, rebuild, or controlled replacement.

### 3.6 Release readiness is stronger than demo convenience

A path may be acceptable for a quick experiment but still not qualify as governed serving.

---

## 4. Serving layers covered by this policy

This repository recognizes four main serving release classes:

1. warehouse serving source release
2. search-serving release
3. semantic-serving release
4. consumer-facing release

---

## 5. Warehouse serving source release

A warehouse object may be treated as a serving source only when all relevant conditions are true.

### 5.1 Minimum conditions

- grain is explicit
- columns are understandable
- naming is stable enough
- source path is known
- transformation logic is reproducible
- object ownership is clear
- downstream purpose is explicit

### 5.2 Additional strong signals

- dbt tests or equivalent checks exist
- row counts are understood
- joins are contract-aligned
- the object is no longer relying on hidden manual fixes
- a replacement path is known if later refactored

### 5.3 Rule

A warehouse object must be judged release-ready before it is allowed to become the input of Elasticsearch, Chroma, Power BI, or Streamlit.

---

## 6. Elasticsearch serving release

Elasticsearch release readiness requires more than successful index creation.

### 6.1 Minimum release conditions

All of the following should be true:

- governed source table or view is identified
- source row count is understood
- index mapping is versioned
- analyzer design is intentional
- index build is repeatable
- reload path is understood
- smoke queries exist
- expected matches have been checked

### 6.2 Analyzer release gate

Analyzer behavior becomes a release gate when any of the following matter:

- code search depends on punctuation normalization
- users expect `F21S8` to match `F21S 8/00`
- lowercase and space-insensitive search is required
- prefix or partial matching is expected
- exact-match and search-text behaviors both matter

### 6.3 Minimum Elasticsearch release flow

```text id="h5v3m2"
1. identify governed source
2. freeze source fields for this release
3. define mapping and analyzer behavior
4. create versioned index
5. load index
6. run smoke queries
7. compare expected hits
8. expose through serving interface
9. log release version and freshness
```
### 6.4 Rule

If search quality depends materially on analyzer behavior, analyzer design is not optional and must be treated as a release criterion.

---

## 7. Chroma semantic-serving release

Semantic serving is not automatically release-ready because embeddings exist.

### 7.1 Minimum release conditions

All of the following should be true:

- dataset scope is fixed for the release
- input source is governed and version-aware
- embedding model/version is recorded
- manifest exists
- retrieval purpose is explicit
- benchmark or comparison basis exists
- source-to-result traceability is possible

### 7.2 Additional strong signals

- semantic retrieval is not being used to compensate for broken structured modeling
- BM25 and metadata filters remain conceptually separate from vector similarity
- collection rebuild path is known
- result interpretation is documented

### 7.3 Rule

A semantic-serving release must be tied to a manifest, a source scope, and an evaluation context.

No governed semantic release should rely on an unnamed or drifting collection.

---

## 8. Power BI release

Power BI should not be connected directly to unstable warehouse objects.

### 8.1 Minimum release conditions

- the source is a curated mart or intentionally approved serving source
- grain is explicit
- metric meaning is stable enough
- refresh expectations are known
- row count surprises are understood
- null/duplicate risks are known
- naming is readable for dashboard use

### 8.2 Required mindset

Power BI is for monitored reporting, not for discovering whether raw structural modeling is broken.

### 8.3 Rule

If a dataset still requires frequent explanation of what each row means, it is not yet ready as a Power BI release source.

---

## 9. Streamlit release

Streamlit is an interactive interface, not a substitute for governed data contracts.

### 9.1 Minimum release conditions

- the upstream source is stable enough
- returned results are traceable
- key filters and explanations make sense
- there is no hidden dependency on ad hoc notebook logic
- failure cases are understandable
- user-facing output aligns with current platform truth

### 9.2 Streamlit may expose

- field lookup
- taxonomy lookup
- BM25 retrieval
- semantic retrieval
- explanation traces
- evidence-linked result cards

### 9.3 Rule

A Streamlit path is release-ready only if its upstream serving path is already understandable and governable.

---

## 10. Reviewability and traceability release criteria

A serving path is much stronger when it can support reviewability and traceability.

### 10.1 Minimum reviewability signals

- result source can be traced
- serving object can be identified
- current release version can be named
- critical assumptions are documented
- replacement path is known if the release is later deprecated

### 10.2 Preferred traceability signals

- source row counts can be compared
- release note or change note exists
- benchmark or smoke query set is retained
- review feedback can be attached or linked

### 10.3 Rule

A serving path that cannot explain where its results came from is not governance-ready, even if it is technically usable.

---

## 11. Release classes

This policy recognizes three release classes.

### 11.1 Experimental

Purpose:

- internal exploration
- unstable logic
- no claim of governed readiness

Requirements:

- minimal documentation
- no public trust claim
- no assumption of stable release behavior

### 11.2 Controlled demo

Purpose:

- portfolio demo
- interview demo
- reviewer walkthrough
- stakeholder explanation

Requirements:

- clear source path
- stable enough outputs
- known limits
- smoke-tested behavior
- visible scope constraints

### 11.3 Governed serving

Purpose:

- stable governed platform capability
- repeatable rebuild
- traceable consumer-facing behavior

Requirements:

- governed source
- release note or stable contract
- validation checks
- clear ownership
- rollback or rebuild path
- no hidden dependency on unstable logic

---

## 12. Release gating checklist

Use this checklist before calling a serving path release-ready.

### 12.1 Common gates

- [ ]  source object identified
- [ ]  grain understood
- [ ]  role understood
- [ ]  owner known
- [ ]  downstream consumer known
- [ ]  rebuild or rollback path known
- [ ]  current version identified

### 12.2 Elasticsearch-specific gates

- [ ]  mapping defined
- [ ]  analyzer intentional
- [ ]  load path repeatable
- [ ]  smoke queries pass
- [ ]  expected code-match behavior checked

### 12.3 Chroma-specific gates

- [ ]  dataset scope fixed
- [ ]  embedding model/version logged
- [ ]  manifest stored
- [ ]  comparison or evaluation basis exists

### 12.4 Power BI-specific gates

- [ ]  mart is stable
- [ ]  metrics interpretable
- [ ]  refresh path understood

### 12.5 Streamlit-specific gates

- [ ]  output traceable
- [ ]  user-facing logic understandable
- [ ]  upstream release already stable enough

---

## 13. Release note rule

A meaningful serving release should have a minimal release note or change note when any of the following are true:

- source path changed
- analyzer changed
- semantic scope changed
- grain changed
- consumer contract changed
- row-count meaning changed
- a previously missing case is now included
- a replacement path was introduced

A release note may be short, but should record:

- what changed
- why
- what the consumer impact is
- how to rebuild or rollback if relevant

---

## 14. Replacement and rollback rule

No serving release should assume perfect permanence.

### 14.1 Replacement rule

When replacing a serving path:

- identify the replacement clearly
- document whether behavior changes
- maintain migration clarity for consumers
- avoid silent path swapping

### 14.2 Rollback rule

A serving release should be rollbackable by one of the following:

- reactivating prior warehouse source
- rebuilding prior Elasticsearch index version
- rehydrating prior semantic manifest
- pointing the consumer back to the previous known-good path

### 14.3 Rule

If a serving path cannot be rolled back or confidently rebuilt, it must meet a higher confidence bar before release.

---

## 15. Relationship to current platform lanes

### 15.1 Structured / warehouse lane

This lane must stabilize first.

Serving release confidence is much weaker if identity, grain, and marts are still unclear.

### 15.2 BM25 lane

BM25 serving may release after:

- source is governed
- search behavior is intentional
- analyzer needs are handled
- expected search examples pass

### 15.3 Semantic lane

Semantic serving should not outrun the structured and BM25 foundations.

It may be released as a controlled demo before it becomes a governed serving path, but only if its scope and limitations are explicit.

### 15.4 Dashboard lane

Dashboard release requires mart stability and metric meaning, not just query success.

---

## 16. Immediate repository decisions

The following decisions are now adopted:

1. a serving path is not release-ready merely because it runs
2. warehouse serving sources must stabilize before downstream serving release
3. analyzer behavior is a release gate once search quality depends on it
4. semantic-serving requires versioned manifest and scope clarity
5. Power BI should consume curated marts, not unstable raw dependency chains
6. Streamlit should expose only explainable and traceable serving paths
7. controlled demo release is allowed as a class distinct from governed serving
8. release notes are required when behavior or contract materially changes

---

## 17. Relationship to other policies

This policy should be read together with:

- `policies/platform/platform_boundary_and_operating_model_v1.md`
- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/lifecycle/materialization_policy_v1.md`
- `policies/lifecycle/backup_restore_policy_v1.md`

Together these policies define:

- what the platform components are for
- what state they are in
- how they are materialized
- how they are restored
- when they are ready to be trusted as serving paths

---

## 18. Final principle

A governed serving release must be able to answer five questions:

1. What is the source?
2. What behavior is being released?
3. Why should it be trusted?
4. How is it rebuilt or rolled back?
5. What consumer is it safe for?

If those five questions cannot be answered, the path is not truly release-ready.


