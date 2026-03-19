# Semantic / Serving Contract v2.0

Previous version: `docs/architecture/semantic_station_contract.md`

Status: Active  
Scope: Warehouse-to-serving contract for landscape/core warehouse, BM25 serving, semantic serving, and RAG evidence trace  
Related:

- `policies/id_governance_and_two_lane_retrieval_policy_v1.md`
- `policies/semantic/semantic_chunk_policy_v2_1.md`
- `policies/semantic/semantic_embedding_layer_policy_v3_0.md`
- `policies/semantic/claim_presence_policy_v2_0.md`

---

## Why this version exists

The previous station contract focused mainly on the semantic pipeline.

That is no longer sufficient.

The system now includes:

- landscape / core warehouse
- BM25 serving
- semantic serving
- RAG evidence trace

A previous failure showed that lane heterogeneity and implicit handoff assumptions
can introduce silent structural bias.

To prevent recurrence, this contract defines the serving-layer boundary model:

- each station declares governed inputs
- each station declares deterministic outputs
- each handoff defines required IDs
- lane separation is explicit
- BM25 / semantic boundaries are explicit
- RAG evidence trace must remain reconstructable

This document does **not** redefine policy.
It binds policy to executable serving architecture.

---

# Core architectural principle

The system is governed as:

> selected-publication anchor source + family-member expansion source -> warehouse core -> BM25 serving + semantic serving -> RAG evidence trace

No serving layer may silently redefine warehouse identity or source authority.

---

# Lane model

## Lane 1 — Landscape / Core Warehouse

Purpose:

- family/publication analytics
- structured dimensions and bridges
- governed source normalization
- downstream retrieval identity support

Authority:

- warehouse-governed family/publication structures

Primary IDs:

- `family_id`
- `publication_number`

Implemented examples:

- `bronze.rawdata_patents`
- `silver.rawdata_patents`
- `silver.publication_ipc`
- `gold.dim_family`
- `gold.dim_publication`
- `gold.dim_ipc`
- `gold.bridge_publication_ipc`

---

## Lane 2 — BM25 Serving

Purpose:

- keyword retrieval
- publication-oriented lexical serving

Authority:

- warehouse-governed publication identity
- governed BM25 text contract

Primary IDs:

- `family_id`
- `publication_number`
- `bm25_document_id` (if introduced later as a serving artifact)

Current BM25 contract direction:

- text built from `title + abstract` where available
- BM25 must not silently substitute semantic-only text for governed BM25 text

---

## Lane 3 — Semantic Serving

Purpose:

- semantic retrieval
- embedding retrieval
- chunk-oriented serving
- RAG grounding

Authority:

- Google canonical full text for semantic lane
- governed semantic chunk policy
- governed semantic embedding policy

Primary IDs:

- `family_id`
- `publication_number`
- `chunk_id`
- `vector_id`

Semantic lane is not allowed to inherit text authority from BM25 or landscape shortcuts.

---

# Contract matrix overview

## Station 0 — Warehouse Foundation

### Purpose

Create governed family/publication structures for downstream serving.

### Input

- selected-publication anchor source
- family-member expansion source when available
- warehouse contracts and ID governance rules

### Output

Warehouse structures such as:

- `gold.dim_family`
- `gold.dim_publication`
- `gold.bridge_family_publication`
- `gold.dim_ipc`
- `gold.bridge_publication_ipc`

### Required IDs

- `family_id`
- `publication_number`

### Hard rules

- no separate `asset_id`
- warehouse family identity is `family_id`
- publication identity is `publication_number`
- serving layers must not redefine these IDs

### Governing policy

- `id_governance_and_two_lane_retrieval_policy_v1.md`

---

## Station 1 — BM25 Document Construction

### Purpose

Build governed lexical-serving documents from warehouse-controlled publication records.

### Input

- warehouse publication identity
- governed BM25 source fields
- publication-level descriptive text

### Output

BM25 document artifacts / tables such as:

- `gold.fact_bm25_document` or equivalent serving structure

Each BM25 document must include:

- `family_id`
- `publication_number`
- `bm25_text`
- `bm25_text_contract_version`
- source trace fields

### Required IDs

- `family_id`
- `publication_number`

### Hard rules

- BM25 uses publication-governed text only
- BM25 must not silently reuse semantic chunk text as its primary text contract
- BM25 artifacts must remain publication-addressable

### Governing policy

- `id_governance_and_two_lane_retrieval_policy_v1.md`

---

## Station 2 — Semantic Acquisition

### Purpose

Fetch canonical Google full text for the semantic lane.

### Input

- governed publication/family anchors
- dataset-selection output
- semantic acquisition rules

### Output

Semantic acquisition artifacts such as:

- canonical Google full-text records
- acquisition audit outputs
- lineage / governance flags

Each record must include:

- `family_id`
- `publication_number` or selected semantic publication reference
- `source = GOOGLE`
- raw text fields
- claims presence flags
- governance flags

### Required IDs

- `family_id`
- `publication_number`

### Hard rules

- semantic authority is Google-only for this lane
- OPS fallback is not semantic text authority
- unresolved identity collision blocks semantic continuation

### Governing policy

- `claim_presence_policy_v2_0.md`
- `id_governance_and_two_lane_retrieval_policy_v1.md`

---

## Station 3 — Semantic Canonical Validation

### Purpose

Validate acquired semantic text before chunking.

### Input

- canonical Google semantic text

### Output

Validation artifacts such as:

- semantic text validation report
- language / corruption checks
- governance exception report

### Required IDs

- `family_id`
- `publication_number`

### Hard rules

- no corrupted text continuation
- claim-presence flags must exist
- structural failure stops semantic pipeline

### Governing policy

- `claim_presence_policy_v2_0.md`

---

## Station 4 — Semantic Chunking

### Purpose

Convert canonical semantic text into governed semantic units.

### Input

- validated semantic text
- chunk policy

### Output

Chunk artifacts such as:

- `claim_1`
- `claim_set`
- `spec`

Each chunk record must include:

- `chunk_id`
- `family_id`
- `publication_number`
- `chunk_type`
- `text`
- `chunk_policy_version`
- creation metadata

### Required IDs

- `family_id`
- `publication_number`
- `chunk_id`

### Hard rules

- only allowed chunk types may be produced
- chunk type set must match policy
- hidden chunk mutation is forbidden

### Governing policy

- `semantic_chunk_policy_v2_1.md`

---

## Station 5 — Semantic Embedding

### Purpose

Convert governed chunks into vectors.

### Input

- chunk artifacts
- embedding model definition
- embedding control parameters

### Output

Vector artifacts / collections plus manifest metadata.

Each vector record must include:

- `vector_id`
- `chunk_id`
- `family_id`
- `publication_number`
- `chunk_type`
- `embedding_model`
- `embedding_version_id`
- `chunk_policy_version`

### Required IDs

- `family_id`
- `publication_number`
- `chunk_id`
- `vector_id`

### Hard rules

- vector metadata must be complete
- embedding version must be deterministic
- partial or unmanifested collections are invalid

### Governing policy

- `semantic_embedding_layer_policy_v3_0.md`

---

## Station 6 — Retrieval Serving

### Purpose

Serve retrieval results through BM25 and semantic lanes without identity leakage.

### Input

- BM25 serving artifacts
- semantic vector artifacts
- governed query inputs

### Output

Serving-layer retrieval result sets.

Each retrieval result must preserve:

- lane label (`BM25` or `SEMANTIC`)
- `family_id`
- `publication_number`
- `chunk_id` if semantic
- score
- source artifact reference

### Required IDs

- `family_id`
- `publication_number`
- optional `chunk_id` for semantic results

### Hard rules

- BM25 and semantic scores must not be merged without explicit fusion logic
- lane identity must be visible in results
- chunk-level semantic results must remain traceable to publication/family identity

### Governing policy

- `id_governance_and_two_lane_retrieval_policy_v1.md`

---

## Station 7 — RAG Evidence Trace

### Purpose

Construct answerable evidence paths from retrieval results to grounded source records.

### Input

- retrieval outputs
- warehouse identifiers
- semantic chunk references where applicable

### Output

RAG evidence trace objects or answer-support metadata.

Each evidence trace must include:

- `family_id`
- `publication_number`
- lane label
- `chunk_id` if semantic
- cited text span or evidence unit
- source artifact path / reference
- generation timestamp

### Required IDs

- `family_id`
- `publication_number`
- optional `chunk_id`
- optional `vector_id` for debugging lineage

### Hard rules

- every generated answer must be traceable to evidence units
- semantic evidence must be chunk-traceable
- BM25 evidence must be publication-document-traceable
- no answer may cite hidden or non-contract evidence

### Governing policy

- `id_governance_and_two_lane_retrieval_policy_v1.md`
- semantic chunk / embedding policies where applicable

---

# Required ID contract

## Family layer
- `family_id`

## Publication layer
- `publication_number`

## Semantic unit layer
- `chunk_id`

## Embedding artifact layer
- `vector_id`

## Rule

No station may invent alternative primary business identity when these IDs already exist.

---

# BM25 / Semantic handoff boundaries

## BM25 may consume

- warehouse publication identity
- governed lexical text fields

## BM25 may not consume as primary authority

- semantic chunk text
- embedding-derived text artifacts
- semantic-only normalization shortcuts

## Semantic may consume

- warehouse family/publication identity
- canonical Google full text
- governed chunk policy
- governed embedding policy

## Semantic may not consume as primary authority

- OPS fallback text as canonical semantic text
- BM25 document text as semantic text authority

---

# RAG evidence path requirement

Every RAG answer must be reconstructable through:

1. retrieval lane
2. source result object
3. governing ID path
4. evidence unit
5. source artifact location

Minimum trace path:

- BM25 path: `publication_number -> bm25_document -> evidence span`
- semantic path: `publication_number / family_id -> chunk_id -> vector result -> evidence span`

If this path cannot be reconstructed, the answer is out of contract.

---

# Station isolation principle

Each station must:

- consume only declared inputs
- produce only declared outputs
- not mutate upstream artifacts
- not infer hidden metadata as authoritative truth

Cross-station silent coupling is forbidden.

---

# Reproducibility rule

A full rebuild of serving outputs must be reproducible from governed inputs, policies, and deterministic versioned transformations.

If outputs materially differ without a declared version increment, the rebuild is invalid.

---

# Final note

Policies define rules.

Contracts define executable boundaries.

Stations execute those contracts.

This document ensures that warehouse, BM25 serving, semantic serving, and RAG evidence trace remain governed, auditable, and reproducible.