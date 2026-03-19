# Two-Lane Retrieval Policy v1

## 1. Purpose

This policy defines the governing retrieval-lane model for the current project.

Its purpose is to prevent:

- identity drift across retrieval lanes
- source-authority confusion
- silent collapse between family-grain and publication-grain interpretations
- semantic leakage into warehouse-governed BM25 behavior
- misuse of retrieval-serving outputs as canonical warehouse truth

This policy governs how landscape, BM25, and semantic retrieval work must remain separated while still being traceable through the same project.

---

## 2. Scope

This policy applies to:

- warehouse-governed retrieval preparation
- BM25 serving preparation
- semantic serving preparation
- source-authority interpretation
- collision handling between family-level and publication-level views

This policy does **not** define:

- UI behavior
- dashboard layout
- search evaluation metrics
- semantic chunk schema internals
- exact BM25 scoring settings
- vector reranking formulas

Those belong in implementation documents, architecture contracts, or evaluation docs.

---

## 3. Identity Baseline

The project uses the following approved identity model:

- `family_id` = family-level identity
- `publication_number` = publication-level identity
- `chunk_id` = semantic unit identity
- `vector_id` = embedding artifact identity

A separate warehouse-level `asset_id` is not used.

A separate generated `doc_id` is not used as the canonical publication identity.

This means:

- warehouse family truth remains `family_id`
- warehouse publication truth remains `publication_number`
- semantic serving remains traceable through `chunk_id` and `vector_id`

---

## 4. Retrieval-Lane Model

The project currently operates with three practical lanes, but two governance boundaries are the most important:

- warehouse / landscape + BM25 lane
- semantic lane

For implementation and interpretation, the project uses the following lane model.

### 4.1 Landscape lane

Purpose:

- family/publication analytics
- IPC / applicant / inventor / date coverage analysis
- family-grain reporting
- warehouse-governed interpretation

Primary identity:

- `family_id`

Allowed grain:

- family-grain
- publication-grain where explicitly modeled through warehouse structures

Authority:

- warehouse-governed family/publication structures
- anchor + expansion alignment once modeled through bridge tables

Important restriction:

- publication-level collapse must not be mistaken for family headline truth

---

### 4.2 BM25 lane

Purpose:

- keyword retrieval
- searchable document serving
- publication-level search interpretation

Primary identity:

- `publication_number`

Current BM25 text contract:

- `title + abstract`

Current BM25 source behavior:

- BM25 serving is publication-grain
- BM25 may collapse multiple family contexts at the document-serving layer
- BM25 result counts are not authoritative family headline counts

Important restriction:

- BM25 must not silently use semantic-only text as a substitute for governed BM25 text
- BM25 must not redefine family truth

---

### 4.3 Semantic lane

Purpose:

- semantic retrieval
- chunk-based retrieval
- evidence-centered retrieval
- RAG-oriented traceability

Primary identities:

- `chunk_id`
- `vector_id`

Supporting identities:

- `publication_number`
- `family_id` where mapped and governed

Important restriction:

- semantic lane remains isolated from BM25 text authority
- semantic lane must not silently absorb unresolved family/publication ambiguity as if it were governed truth

---

## 5. Source-Authority Rules

## 5.1 Anchor source

Current anchor source:

`data/raw/anchor/rawdata_patents.xlsx`

Current accepted interpretation:

> 1 row = 1 selected publication representing 1 family

This source is accepted as:

- selected-publication anchor source
- family anchor source
- bronze anchor ingestion input
- early publication-level structured metadata source

This source is **not** accepted as:

- full family-member coverage source
- semantic authority source
- complete publication-event lineage source

---

## 5.2 Family-member expansion source

Family-member expansion must come from a separate expansion artifact.

Current expansion artifacts include:

- `data/raw/expansion/ops_family_members.jsonl`
- `data/raw/expansion/raw_pub_to_family_id.json`
- `data/raw/expansion/raw_pub_to_family_id_v2.json`

This source family is accepted as:

- family-member expansion input
- bridge / lineage / coverage support
- OPS-derived relationship expansion

This source family is **not** accepted as a replacement for dataset family identity.

OPS family clustering must not silently replace `family_id`.

---

## 5.3 Retrieval-support source

Current retrieval-support artifacts include:

- `data/raw/retrieval/patents_canonical.jsonl`
- `data/raw/retrieval/claims_representation_v3.jsonl`

These are accepted as:

- retrieval-support artifacts
- BM25 or semantic preparation artifacts
- serving-support inputs

These are **not** accepted as current bronze authority for warehouse family truth.

---

## 5.4 Semantic authority

Semantic authority does not come from anchor landscape files.

Semantic authority must come from the governed semantic text pipeline.

Semantic lane authority must remain documented and distinct from BM25 text authority.

---

## 6. Family-Grain vs Publication-Grain Rules

The project must explicitly distinguish:

- family-grain truth
- publication-grain serving

### 6.1 Landscape interpretation

Landscape headline counts remain family-grain.

Current expected family headline universe:

- 150 dataset families

### 6.2 BM25 interpretation

BM25 serving is publication-grain.

BM25 may legitimately produce a collapsed searchable-publication count that differs from the family headline count.

Example interpretation:

- family universe = 150
- BM25 searchable-publication set = possibly 149 after publication-level collapse

This is acceptable **only** if it is not misreported as the family headline count.

---

## 7. Collision Tolerance Policy

A collision exists when publication-level serving and family-level interpretation no longer align cleanly.

### 7.1 Landscape / warehouse side

Landscape may tolerate flagged proxy situations temporarily during source reconciliation, as long as:

- the family/publication interpretation is documented
- unresolved ambiguity is explicitly surfaced
- the ambiguity is not silently treated as canonical family truth

### 7.2 BM25 side

BM25 may tolerate publication-level collapse for keyword retrieval.

However:

- BM25 must not redefine family identity
- BM25 document count must not be reused as family headline count
- family-to-publication collision must remain governable through warehouse bridge structures

### 7.3 Semantic side

Semantic lane may not tolerate unresolved identity ambiguity as authoritative truth.

If family/publication identity is unresolved, chunk construction, vector serving, or RAG evidence must not silently proceed as if the source identity were fully governed.

---

## 8. Warehouse Modeling Implications

The warehouse must support at least:

- family-level identity
- publication-level identity
- publication-to-family bridge
- IPC structured modeling
- downstream BM25 support
- future applicant / inventor structured modeling
- semantic linkage without identity ambiguity

Current implemented warehouse path includes:

- `bronze.rawdata_patents`
- `silver.rawdata_patents`
- `silver.publication_ipc`
- `silver.publication_inventor_raw`
- `silver.publication_applicant_raw`
- `gold.dim_family`
- `gold.dim_publication`
- `gold.dim_ipc`
- `gold.bridge_publication_ipc`
- `gold.fact_publication_inventor`
- `gold.fact_publication_applicant`

Current expected bridge direction includes:

- future `gold.bridge_family_publication`

This means:

- the warehouse is already the canonical interpretation layer for structured publication metadata
- BM25 and semantic lanes must inherit governed identity from warehouse-aligned structures rather than redefine identity independently

---

## 9. BM25-Specific Policy Position

The current BM25 lane is governed as follows:

- BM25 is publication-grain
- BM25 text contract is currently `title + abstract`
- BM25 uses warehouse-aligned publication identity
- BM25 is a serving lane, not a family-truth layer

Therefore:

- `gold.bm25_document` is a serving table, not a family headline table
- BM25 indexing into Elasticsearch is allowed
- BM25 engine implementation does not change warehouse identity truth

---

## 10. Semantic-Lane Policy Position

The semantic lane is governed separately from BM25.

Semantic lane responsibilities include:

- chunk generation
- embedding generation
- vector serving
- semantic evidence traceability

Semantic lane must remain traceable back through governed identities, but it must not overwrite BM25 or warehouse source-authority rules.

---

## 11. Non-Goals of This Policy

This policy does not define:

- the exact Elasticsearch mapping
- the exact BM25 tuning parameters
- the exact chunking algorithm
- Power BI implementation details
- presentation-layer filtering logic
- UI navigation behavior

These belong elsewhere.

---

## 12. Current Deferred Areas

Deferred but expected later:

- full family-member expansion integration into gold bridge structures
- collision-aware family-publication reconciliation
- publication lineage enrichment
- applicant/inventor refresh alignment
- BM25 document refresh rules
- semantic serving refresh rules

---

## 13. Governing Principle

This project is governed as:

> selected-publication anchor source  
> + family-member expansion source  
> -> warehouse core  
> -> landscape + BM25 + semantic serving

Any implementation that:

- collapses family truth into publication-serving counts
- mixes source authority without documentation
- lets semantic authority overwrite BM25 text authority
- lets OPS family clustering silently replace `family_id`

is out of policy.