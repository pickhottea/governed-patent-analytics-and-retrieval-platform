# Platform Boundary and Operating Model v1

Status: Canonical  
Owner: Repo owner / architecture owner  
Supersedes: None  
Last reviewed: 2026-04-14

## 1. Purpose

This document defines the operating model and system boundaries for the governed patent analytics and retrieval platform.

It exists to answer the following questions clearly:

- when normalization is required
- when to use a view versus a table
- when dbt should be used
- what SQL Server is responsible for
- what Elasticsearch is responsible for
- what Chroma is responsible for
- when Power BI should be connected
- when Streamlit should be connected
- when analyzer design becomes mandatory
- how data moves from source to warehouse to serving layers

This policy is intended to reduce architecture drift, tool misuse, and implementation anxiety caused by unclear platform roles.

---

## 2. Core operating model

This platform is organized into five layers:

1. source acquisition
2. governed warehouse
3. transformation and contract enforcement
4. serving adapters
5. consumption interfaces

### 2.1 Simplified operating model

```text id="jlwmcd"
external sources
-> warehouse landing / raw capture
-> normalized / resolved warehouse layers
-> curated / serving-ready warehouse outputs
-> search / vector serving adapters
-> dashboard / app / analyst interfaces
```
### 2.2 Core principle

The warehouse is the system of record.

Serving systems exist to improve retrieval, exploration, and user interaction.

They do not replace the governed warehouse as the source of truth.

---

## 3. System role definitions

### 3.1 SQL Server

SQL Server is the governed warehouse.

It is responsible for:

- persistent storage
- relational joins
- canonical identifiers
- bronze / silver / gold persistence
- dimensions, facts, marts, and registry-like tables
- governed source-of-truth data objects
- reproducible serving source tables

SQL Server is **not** primarily responsible for:

- BM25 ranking
- full-text analyzer design
- vector similarity search
- interactive UI rendering

### 3.2 dbt

dbt is the warehouse transformation framework.

It is responsible for:

- source declarations
- staging models
- warehouse-layer transformations
- dependency-aware model building
- tests
- documentation of model logic
- materialization choices for warehouse models

dbt is **not** responsible for:

- direct UI behavior
- Elasticsearch index creation
- Chroma vector store population
- notebook experimentation
- ad hoc manual investigation logic

### 3.3 Elasticsearch

Elasticsearch is the search-serving adapter.

It is responsible for:

- BM25 retrieval
- analyzer behavior
- code search behavior
- tokenization and query-time search acceleration
- text-oriented serving
- search ranking and retrieval interaction

Elasticsearch is **not** the source of truth.

Any index in Elasticsearch must be rebuildable from governed warehouse outputs.

### 3.4 Chroma

Chroma is the vector-serving adapter.

It is responsible for:

- embedding-oriented storage
- semantic retrieval
- similarity-based serving
- vector query support

Chroma is **not** the warehouse.

It must be fed from governed, versioned upstream artifacts.

### 3.5 Power BI

Power BI is the governed dashboard and reporting consumer.

It is responsible for:

- KPI visualization
- governance visibility
- trend analysis
- health monitoring
- reviewability and traceability reporting
- business-facing analytical presentation

Power BI should consume curated marts, not unstable raw or bridge-heavy warehouse layers.

### 3.6 Streamlit

Streamlit is the interactive analyst-facing application layer.

It is responsible for:

- interactive retrieval workflows
- search UI
- trace evidence display
- semantic demo interface
- field and taxonomy exploration
- reviewer-oriented interaction

Streamlit is not the source of truth and must not become the only place where business logic lives.

---

## 4. Boundary model by function

### 4.1 Source acquisition boundary

Source acquisition includes:

- file downloads
- raw dumps
- external source pulls
- source version capture
- provenance capture

Typical examples:

- CPC / IPC official files
- patent raw source exports
- external API query results

Acquisition is complete when raw source material is captured and traceable.

### 4.2 Warehouse boundary

The warehouse begins when external source content is loaded into governed storage.

This includes:

- source tables
- landing tables
- staging relations
- normalized tables
- canonical joins
- marts
- serving source tables

### 4.3 Serving adapter boundary

Serving adapters begin when governed warehouse outputs are exported into engines optimized for serving behavior rather than canonical storage.

Examples:

- Elasticsearch index source
- Chroma embedding source

### 4.4 Consumer boundary

Consumers are downstream interfaces and analysis tools that read from warehouse marts or serving adapters.

Examples:

- Power BI
- Streamlit
- reviewer views
- demo pages

---

## 5. Normalization trigger rules

Normalization is required whenever any of the following are true:

1. the same business concept appears in multiple incompatible forms
2. a field will be used in joins
3. the grain of a dataset is not yet stable
4. codes require canonical formatting
5. downstream serving depends on consistent identifiers
6. a field will be used for grouping, filtering, or aggregation
7. raw values include whitespace, punctuation, casing, or typing inconsistencies
8. cross-source reconciliation is required

### 5.1 Typical normalization examples

Normalization may include:

- trimming
- case normalization
- casting
- canonical code construction
- date normalization
- identifier standardization
- null handling
- controlled token cleanup

### 5.2 Rule

If a downstream system depends on consistency, normalization must happen before that dependency is formalized.

---

## 6. Resolved versus curated boundary

### 6.1 Resolved layer

A dataset is resolved when:

- canonical keys are established
- cross-source joins are stabilized
- duplicates and structural conflicts are addressed
- family/publication identity rules are enforced

### 6.2 Curated layer

A dataset is curated when:

- it is stable enough for direct analytical or serving use
- its grain is explicitly defined
- its columns are meaningful for consumers
- its role in the platform is clear
- it passes basic quality expectations

Curated does not mean perfect.

Curated means serving-ready within governed scope.

---

## 7. Materialization rules: view versus table

### 7.1 Use a view when

Use a view when most of the following are true:

- logic is still evolving
- the object is lightweight
- the object is primarily a projection or wrapper
- the object is used for exploration or transition
- recomputation cost is low
- it helps stabilize a serving contract before freezing materialization

Views are useful for:

- lightweight lookup layers
- intermediate wrappers
- transition states during design freeze
- thin presentation layers over already-governed objects

### 7.2 Use a table when

Use a table when one or more of the following are true:

- the object is repeatedly consumed
- the logic is expensive to recompute
- the object acts as a stable serving source
- downstream systems depend on consistent performance
- snapshots, rollback, or reproducibility matter
- the object is part of a business-facing mart
- the object feeds Elasticsearch or other serving systems regularly

Tables are preferred for:

- core marts
- stable dimensions
- repeatedly used serving sources
- reproducible index source tables
- dashboard-facing curated assets

### 7.3 Rule

A view is acceptable as a transitional contract.

A table is preferred when the object becomes an operational dependency.

---

## 8. dbt usage policy

### 8.1 Use dbt when

Use dbt when the work is primarily:

- warehouse transformation
- contract enforcement
- source-to-staging mapping
- mart building
- dependency-managed SQL transformation
- repeatable model testing
- governed warehouse documentation

### 8.2 Do not use dbt when

Do not use dbt as the default tool for:

- Elasticsearch-specific operations
- vector store loading
- interactive notebook experiments
- one-off manual diagnostics
- UI application logic
- acquisition scripts outside warehouse transformation

### 8.3 Rule

dbt owns the governed warehouse transformation layer, not every data-related action in the repo.

---

## 9. SQL Server versus Elasticsearch boundary

### 9.1 SQL Server should be used for

- canonical data storage
- relational business logic
- joins and identity resolution
- marts and dimensions
- source-of-truth serving sources
- traceable warehouse lineage

### 9.2 Elasticsearch should be used for

- BM25 retrieval
- code search behavior
- prefix and analyzer-based matching
- query-time retrieval experience
- ranking over search-oriented fields

### 9.3 Boundary rule

If the requirement is canonical storage, governed joins, or reproducible source truth, use SQL Server.

If the requirement is ranking, analyzer behavior, or low-latency text search serving, use Elasticsearch.

---

## 10. SQL Server versus Chroma boundary

### 10.1 SQL Server should be used for

- source-of-truth structured data
- canonical joins
- serving source tables
- metadata registry
- auditability

### 10.2 Chroma should be used for

- semantic similarity retrieval
- embedding-based search
- vector nearest-neighbor behavior
- retrieval experiments and governed semantic serving

### 10.3 Boundary rule

If the task is relational truth, use SQL Server.

If the task is vector similarity serving, use Chroma.

---

## 11. Power BI versus Streamlit boundary

### 11.1 Power BI is for

- dashboarding
- governance visibility
- quality trends
- operational health
- analytical summaries
- business-facing metrics

### 11.2 Streamlit is for

- interactive search
- reviewer workflows
- trace display
- semantic retrieval exploration
- analyst-facing inspection
- controlled demo interaction

### 11.3 Boundary rule

If the goal is monitored reporting, use Power BI.

If the goal is interactive retrieval or evidence exploration, use Streamlit.

---

## 12. When to connect each consumer

### 12.1 Connect Power BI when

Power BI should be connected only when:

- marts are stable enough
- grain is defined
- naming is understandable
- downstream refresh logic is clear
- the data is intended for trend or KPI consumption

Power BI should not be used as the first place to discover whether a model contract is broken.

### 12.2 Connect Streamlit when

Streamlit should be connected when:

- a serving contract exists
- user-facing interactions are needed
- trace or explanation views are useful
- retrieval outputs are stable enough for inspection

### 12.3 Connect Elasticsearch when

Elasticsearch should be connected when:

- search behavior is a real requirement
- retrieval depends on ranking
- analyzer design materially affects quality
- warehouse serving source has been identified

### 12.4 Connect Chroma when

Chroma should be connected when:

- semantic retrieval is intentionally in scope
- embeddings are versioned and governed
- dataset scope is fixed enough for meaningful evaluation
- BM25 and structured filters are not being confused with vector search objectives

---

## 13. Analyzer release policy

Analyzer design is not optional once search behavior depends on token treatment.

### 13.1 Analyzer design becomes mandatory when

Any of the following are true:

- search depends on code normalization
- search depends on punctuation handling
- users expect `F21S8` to match `F21S 8/00`
- prefix behavior matters
- exact keyword and search text behaviors both matter
- ranking quality is sensitive to token boundaries

### 13.2 Minimum analyzer release flow

```
1. identify search requirement
2. identify governed source fields
3. write mapping and analyzer design
4. create or version index definition
5. load index from governed source
6. run smoke queries
7. validate expected matches
8. expose via serving interface
9. log freshness and release version
```

### 13.3 Rule

No search-serving path should be treated as production-valid unless its analyzer behavior is intentional and testable.

---

## 14. Semantic lane entry criteria

The semantic lane should not be treated as the automatic next step after raw ingestion.

Semantic / vector serving should begin only when all are substantially true:

- core warehouse identity is stable
- main structured marts are usable
- BM25 or structured retrieval baseline exists
- source scope is explicit
- dataset versions are controlled
- retrieval evaluation criteria are defined

### 14.1 Rule

Semantic work enters after structured and search-serving foundations are stable enough to support governed comparison.

---

## 15. Data flow boundary map

### 15.1 Canonical path

```
external source
-> raw capture
-> warehouse source / staging
-> normalized / resolved warehouse layer
-> curated warehouse mart or serving source
-> search / vector serving adapter
-> dashboard or interactive application
```

### 15.2 Key interpretation

- external source to warehouse = ingestion and provenance
- warehouse to dbt = transformation framework operating on warehouse state
- warehouse to Elasticsearch = search-serving export
- warehouse to Chroma = embedding-serving export
- warehouse to Power BI = dashboard consumption
- warehouse / serving adapter to Streamlit = interactive application consumption

---

## 16. Deprecation and replacement rule

A serving object may be replaced only when:

1. a replacement exists
2. downstream dependencies are known
3. rollback is possible or acceptable
4. current consumers can migrate safely

When replacing a view with a table, or one serving source with another:

- mark the old object deprecated
- point consumers to the replacement
- preserve transition clarity
- avoid silent swaps without documentation

---

## 17. Practical decision matrix

### 17.1 Should I normalize?

Normalize if:

- a join depends on it
- a serving layer depends on it
- identity or grouping depends on it
- source variability exists

### 17.2 Should I use a view?

Use a view if:

- it is thin
- it is transitional
- it is cheap
- it helps expose a stable contract before freezing

### 17.3 Should I use a table?

Use a table if:

- it is reused
- it is expensive
- it is serving-critical
- it is dashboard-critical
- it is index-source-critical

### 17.4 Should I use dbt?

Use dbt if:

- it is warehouse transformation with repeatability and testing needs

### 17.5 Should I use Elasticsearch?

Use Elasticsearch if:

- the problem is search behavior, ranking, or analyzer-driven matching

### 17.6 Should I use Chroma?

Use Chroma if:

- the problem is semantic similarity retrieval

### 17.7 Should I use Power BI?

Use Power BI if:

- the output is a monitored, aggregated, or executive-facing dashboard

### 17.8 Should I use Streamlit?

Use Streamlit if:

- the output is an interactive inspection, retrieval, or analyst-facing interface

---

## 18. Immediate repository decisions

The following decisions are now adopted:

1. SQL Server is the governed warehouse
2. dbt is the warehouse transformation framework
3. Elasticsearch is a search-serving adapter, not the source of truth
4. Chroma is a vector-serving adapter, not the source of truth
5. Power BI consumes curated marts
6. Streamlit consumes curated marts or serving adapters
7. analyzer behavior must be intentionally designed once search quality depends on token behavior
8. semantic serving should not outrun structured and BM25 foundations
9. table versus view decisions must follow operational role, not personal preference

---

## 19. Final principle

Every tool in this platform must have a clear job.

If a tool is being used because it feels convenient, but its role is not explicit, stop and define the boundary first.

Clear boundaries reduce rework, improve trust, and make the platform governable.