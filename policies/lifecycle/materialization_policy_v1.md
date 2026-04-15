# Materialization Policy v1

Status: Canonical  
Owner: Repo owner / architecture owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This policy defines how materialization decisions are made in this repository.

It exists to answer the following questions clearly:

- when to use a view
- when to use a table
- when to use an incremental table
- when a view is only a transitional contract
- when an object has become a stable operational dependency
- when a serving source must stop being a thin wrapper and become materialized

This policy is intended to reduce rework, ambiguous architecture, unstable serving paths, and accidental misuse of warehouse objects.

---

## 2. Scope

This policy applies to warehouse and serving-source materialization decisions for:

- SQL Server warehouse objects
- dbt models
- staging outputs
- resolved identity layers
- dimensions
- facts
- marts
- search-serving source tables
- dashboard-facing curated outputs
- thin lookup views
- transitional wrapper views

This policy does not govern:

- Elasticsearch index mappings
- Chroma collection construction
- notebook experimentation
- UI rendering logic

Those are governed by platform boundary and serving policies.

---

## 3. Core principles

### 3.1 Materialization follows operational role

An object should be materialized according to how it is used, not according to habit or personal preference.

### 3.2 A view is allowed to be transitional

A view may be the correct choice while logic is stabilizing.

### 3.3 A table is preferred once dependency becomes real

Once an object becomes reused, performance-sensitive, serving-critical, or dashboard-critical, materialization should become explicit.

### 3.4 Curated does not automatically mean table

Some curated objects may remain views when they are lightweight, stable, and clearly bounded.

### 3.5 Repeated recomputation is a signal

If an object is repeatedly recomputed for multiple downstream consumers, that is a strong signal that table materialization should be considered.

### 3.6 Materialization must be explainable

A contributor should be able to explain:

- why this object is a view
- why this object is a table
- why this object is incremental
- what would trigger a later change

If that cannot be explained, the choice is not governed well enough.

---

## 4. Approved materialization classes

This repository uses the following materialization classes:

1. `view`
2. `table`
3. `incremental_table`

These may be implemented through:

- warehouse DDL
- dbt model materializations
- controlled SQL deployment patterns

---

## 5. View policy

### 5.1 Use a view when

Use a view when most of the following are true:

- logic is still stabilizing
- the object is lightweight
- the object is primarily a projection or wrapper
- recomputation cost is low
- the object exposes a helpful contract over already-governed upstream data
- the object is not yet relied on by many consumers
- the object is transitional by design

### 5.2 Good use cases for views

Views are a good fit for:

- taxonomy lookup wrappers
- breadcrumb or display-code helpers
- thin serving lookup layers
- transition layers while contracts freeze
- explanation-friendly wrappers over stable tables
- light denormalized projections for inspection

### 5.3 Bad use cases for views

Views are a poor fit when they become:

- repeatedly expensive to compute
- the hidden dependency of many dashboards
- the only source used to rebuild serving systems
- performance bottlenecks
- opaque logic bundles that are hard to trace
- pseudo-permanent marts pretending to be lightweight

### 5.4 View rule

A view is acceptable when it remains thin, understandable, and inexpensive enough to justify recomputation.

If it becomes a central dependency, promote it.

---

## 6. Table policy

### 6.1 Use a table when

Use a table when one or more of the following are true:

- the object is reused by multiple downstream consumers
- the logic is expensive to recompute
- the object is dashboard-facing
- the object is a stable serving source
- the object feeds Elasticsearch regularly
- the object supports Power BI or repeated reporting workloads
- reproducibility and rollback matter
- performance becomes a real concern
- a stable contract has been reached

### 6.2 Good use cases for tables

Tables are a good fit for:

- dimensions
- facts
- bridge tables
- marts
- dashboard-facing aggregates
- governed search source tables
- stable semantic source manifests
- repeatable release assets

### 6.3 Table rule

If an object is part of the platform's stable operational surface, prefer a table unless there is a clear reason not to.

---

## 7. Incremental table policy

### 7.1 Use an incremental table when

Use an incremental table when all or most of the following are true:

- the object is large enough that full rebuilds are expensive
- the load pattern is append-heavy or delta-friendly
- the change detection logic is known
- the object has a clear merge/update rule
- rebuild cost is materially higher than incremental maintenance cost
- downstream consumers need freshness more often than full rebuilds are practical

### 7.2 Good use cases for incremental tables

Incremental tables are a good fit for:

- large fact-style tables
- append-oriented event logs
- refreshed search source tables with stable keys
- monitored history tables
- selected serving summaries with known change windows

### 7.3 Bad use cases for incremental tables

Incremental tables are a poor fit when:

- identity rules are still unstable
- dedup logic is still changing
- the change window is unclear
- full rebuilds are cheap enough already
- contributors cannot confidently explain merge semantics
- hidden update bugs would be hard to detect

### 7.4 Incremental rule

Incremental materialization is an optimization, not a shortcut.
It should be adopted only when change logic is explicit and testable.

---

## 8. Materialization by layer

### 8.1 Ingested / raw-like layer

Preferred materialization:
- table

Reason:
- captured source state must persist
- reproducibility and provenance matter
- raw capture should not be recomputed from downstream objects

### 8.2 Normalized / staging layer

Preferred materialization:
- usually table or dbt-managed relation
- sometimes view when lightweight and transitional

Reason:
- staging often supports repeated downstream use
- but some thin dbt staging models may remain view-like if low-cost and stable

### 8.3 Resolved identity layer

Preferred materialization:
- table, unless the layer is very thin and stable

Reason:
- canonical joins and identity logic are usually too important to hide behind unstable recomputation

### 8.4 Curated marts and serving sources

Preferred materialization:
- table
- incremental table where justified

Reason:
- curated objects are often the main serving surface for dashboards, search exports, and governed consumption

### 8.5 Lookup and explanation helpers

Preferred materialization:
- view, if thin
- table, if repeatedly reused or expensive

Reason:
- lookup layers are often ideal thin wrappers, but should not become hidden heavy marts

---

## 9. dbt-specific materialization rules

### 9.1 dbt staging models

dbt staging models may use view-like materialization when:

- logic is thin
- cost is low
- they mainly normalize or rename source fields
- they are not heavy downstream bottlenecks

However, once a staging model becomes:

- expensive
- heavily reused
- central to many marts

promotion to table may be justified.

### 9.2 dbt marts

dbt marts should generally prefer:

- `table`
- or `incremental`

Reason:
- marts are consumer-facing and operationally important
- repeated recomputation often becomes wasteful

### 9.3 dbt singular tests are not materialization targets

Tests validate models.
They do not determine materialization by themselves.

### 9.4 Rule

In dbt, materialization must reflect the role of the model, not only a default project setting.

---

## 10. View-to-table promotion triggers

A view should be reviewed for promotion when any of the following are true:

1. more than one stable downstream consumer depends on it
2. query latency becomes noticeable or repeatedly discussed
3. Power BI or Streamlit relies on it directly
4. Elasticsearch export depends on it repeatedly
5. contributors keep wrapping the same view with more views
6. the view becomes the de facto system-of-record serving source
7. full recomputation is expensive enough to affect delivery
8. rollback or release traceability matters

### 10.1 Promotion rule

Promotion from view to table is not a failure.
It is a normal sign that a transitional layer has become operationally important.

---

## 11. Table-to-view demotion triggers

A table may be reconsidered as a view when all of the following are true:

- logic has become thin
- storage cost is not justified
- recomputation is cheap
- no downstream SLA depends on persistence
- the object was over-materialized during experimentation

This should be rare for serving-critical objects.

### 11.1 Demotion rule

Do not demote a table to a view simply to make the repo look simpler.
Only do so when operational and governance needs still remain satisfied.

---

## 12. Search-serving source rules

### 12.1 Elasticsearch source objects

If an object feeds Elasticsearch repeatedly and serves as the governed source for index rebuilds, it should usually be a table.

Reason:
- reproducibility matters
- release traceability matters
- export logic should not depend on fragile layered recomputation

### 12.2 Thin search helper views

A thin search helper view may be allowed when:

- it only wraps a stable table
- it adds lightweight projection logic
- it does not hide expensive joins
- it is not the only reproducible source

### 12.3 Rule

Search-serving must not rely only on unstable or opaque views.

---

## 13. Dashboard-facing source rules

### 13.1 Power BI sources

Power BI-facing sources should usually be:

- curated tables
- marts
- governed aggregates

Power BI should not rely on deep raw-to-bridge-to-view chains if stable marts can be materialized instead. This aligns with current project guidance that Power BI should consume defined marts rather than raw bridge/fact tables. :contentReference[oaicite:0]{index=0}

### 13.2 Streamlit sources

Streamlit may consume:

- curated tables
- thin lookup views
- serving adapters such as Elasticsearch or Chroma

A thin lookup view is acceptable for Streamlit if it is clear, lightweight, and not acting as a hidden operational bottleneck.

---

## 14. Semantic-serving source rules

### 14.1 Governed semantic inputs

Artifacts that define semantic-serving scope, dataset version, or embedding manifest should be persisted as tables or controlled files, not only transient views.

### 14.2 Vector stores

Vector collections themselves are serving stores, not canonical warehouse truth.
Their governed upstream source should be materialized clearly enough to support rebuild and comparison.

### 14.3 Rule

Semantic serving should consume stable, version-aware upstream assets, not unstable ad hoc projections.

---

## 15. Materialization decision matrix

### 15.1 Choose `view` if most answers are yes

- Is the object thin?
- Is recomputation cheap?
- Is logic still stabilizing?
- Is it mainly a wrapper or projection?
- Is it not yet a major downstream dependency?
- Is it acceptable for the object to change shape before freeze?

### 15.2 Choose `table` if most answers are yes

- Is the object reused often?
- Does it feed dashboards or search-serving?
- Is the logic expensive?
- Is stable performance desirable?
- Is it part of the governed serving surface?
- Does rollback or rebuild reproducibility matter?

### 15.3 Choose `incremental_table` if most answers are yes

- Is full rebuild cost high?
- Is data growth significant?
- Is the update pattern known?
- Are keys and change logic stable?
- Is incremental freshness worth the added logic?

---

## 16. Materialization review triggers

Materialization should be reviewed when:

- a dashboard starts using an object
- an object begins feeding Elasticsearch
- semantic serving begins depending on an object
- a thin lookup grows additional join complexity
- performance complaints appear
- dbt runs become unnecessarily heavy
- the object becomes a repeated release dependency
- a view is copied or wrapped multiple times
- a table appears to be unnecessary persistence

---

## 17. Deprecation and replacement rules

When replacing a view with a table, or a table with a better materialized object:

1. document the reason
2. identify the replacement clearly
3. update downstream consumers deliberately
4. preserve rollback clarity
5. avoid silent swaps

A deprecated materialization choice should not remain ambiguous.

---

## 18. Current repository-aligned interpretations

### 18.1 Thin taxonomy lookup display layers

Thin display-oriented lookup wrappers may remain views while they are lightweight and understandable.

### 18.2 Core marts and serving sources

Core marts, search sources, and BI-facing assets should usually be tables once their contracts stabilize.

### 18.3 Transitional contract layers

Transitional views are acceptable while architecture is freezing, but they should not become invisible long-term operational dependencies.

### 18.4 dbt marts

dbt marts should usually prefer materialization that reflects operational reuse, not purely exploratory convenience.

---

## 19. Immediate repository decisions

The following decisions are now adopted:

1. materialization must follow operational role
2. views are acceptable as thin or transitional layers
3. tables are preferred once dependency becomes stable and real
4. incremental tables are justified only when change logic is explicit and worth the added complexity
5. Power BI-facing assets should usually be materialized marts
6. search-serving source objects should usually be persisted clearly enough for rebuild and release traceability
7. a view becoming important is a promotion signal, not an architecture failure
8. materialization decisions must be reviewable and documented

---

## 20. Relationship to other policies

This policy should be read together with:

- `policies/platform/platform_boundary_and_operating_model_v1.md`
- `policies/lifecycle/lifecycle_policy_v1.md`
- `policies/lifecycle/retention_policy_v1.md`

Together they define:

- what the object is for
- what state it is in
- how long it should remain
- what kind of materialization best supports that role

---

## 21. Final principle

Do not ask "Do I prefer views or tables?"

Ask instead:

- what role does this object play
- how many things depend on it
- how expensive is recomputation
- how much stability, traceability, and performance does it need

A good materialization choice is one that matches the object's operational reality.