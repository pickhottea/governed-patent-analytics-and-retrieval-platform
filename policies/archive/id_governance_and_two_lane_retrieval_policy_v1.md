# ID Governance and Two-Lane Retrieval Policy v1

## Purpose

Define the governing identity model and retrieval-lane boundaries for the patent warehouse and retrieval system.

This policy exists to prevent identity drift, lane leakage, and source-authority confusion across landscape, BM25, and semantic retrieval work.

---

## Core identity model

The project uses the following identity model:

- `family_id` = family-level identity
- `publication_number` = publication-level identity
- `chunk_id` = semantic unit identity
- `vector_id` = embedding artifact identity

### Explicit decision

A separate warehouse-level `asset_id` is not used.

`family_id` is the family-level key.

This decision is final for the current architecture unless a later technical blocker requires formal reconsideration.

---

## Retrieval-lane model

The project has three operational lanes:

### 1. Landscape lane

Purpose:

- family/publication analytics
- IPC/CPC/applicant/inventor/date coverage
- BI/dashboard analysis

Authority:

- canonical landscape / warehouse-controlled publication-family structures

### 2. BM25 lane

Purpose:

- keyword retrieval

Rules:

- publication-level retrieval
- inherits publication/family identity from warehouse
- BM25 text contract is currently based on `title + abstract` where available
- BM25 must not silently reuse semantic-only text as a substitute for governed BM25 text

### 3. Semantic lane

Purpose:

- semantic retrieval
- chunk-based retrieval
- RAG

Rules:

- semantic authority is Google-derived canonical full text for the semantic lane
- semantic lane does not use OPS fallback as semantic authority
- chunking uses governed chunk units
- semantic identity must remain isolated at dataset-family / publication / chunk level

---

## Source-authority rules

### Selected-publication anchor source

`rawdata_patents.xlsx` is currently accepted as:

- selected-publication anchor source
- family anchor source
- bronze anchor ingestion input

It is not accepted as:

- full family-member coverage source
- semantic authority source
- complete publication-event lineage source

### Family-member expansion source

Family-member expansion must come from a separate source, such as:

- OPS family member extraction output
- equivalent publication-family expansion artifact

This source is required for full coverage modeling.

### Semantic authority source

Semantic authority is not taken from landscape anchor files.

Semantic authority must come from the governed semantic text pipeline.

---

## Collision tolerance policy

### Landscape / warehouse side

Landscape may tolerate flagged proxy situations temporarily during source reconciliation, as long as:

- the family/publication interpretation is documented
- unresolved ambiguity is not silently treated as canonical truth

### Semantic side

Semantic lane may not tolerate unresolved identity collision.

If publication-family identity is unresolved, semantic chunk construction or retrieval serving must not silently proceed as if the identity were authoritative.

---

## Warehouse modeling implications

The warehouse must support at least:

- family-level identity
- publication-level identity
- publication-to-family bridge
- IPC structured modeling
- downstream BM25 support
- future applicant/inventor structured modeling
- semantic chunk linkage without identity ambiguity

Current desired warehouse core includes:

- `gold.dim_family`
- `gold.dim_publication`
- `gold.bridge_family_publication`
- `gold.dim_ipc`
- `gold.bridge_publication_ipc`
- future publication-party structures
- retrieval-serving structures later

---

## Current contract position

Current implemented path includes:

- `bronze.rawdata_patents`
- `silver.rawdata_patents`
- `silver.publication_ipc`
- `gold.dim_ipc`
- `gold.bridge_publication_ipc`

This means the anchor-source-to-IPC-warehouse path is already governed and implemented.

---

## Non-goals of this policy

This policy does not define:

- UI behavior
- presentation layout
- experimentation prioritization
- detailed semantic chunk schema
- exact BM25 scoring implementation

Those belong in separate contracts or implementation docs.

---

## Current deferred areas

Deferred but expected later:

- applicant raw split
- inventor raw split
- family-member expansion integration
- publication lineage enrichment
- abstract enrichment
- BM25 document refresh
- semantic serving refresh

---

## Governing principle

This project is governed as:

> selected-publication anchor source + family-member expansion source -> warehouse core -> BM25 + semantic/RAG serving

Any implementation that collapses these layers or mixes source authority without explicit approval is out of policy.