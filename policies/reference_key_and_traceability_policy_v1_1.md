# Reference Key and Traceability Policy v1.1

## 1. Purpose

This policy defines the approved reference key model for the current project.

Its purpose is to ensure:

- consistent identity usage across warehouse layers
- stable traceability across retrieval and semantic workflows
- clear distinction between business keys, relationship keys, mapping keys, and technical row identifiers
- governance-safe alignment between landscape, BM25, semantic, and OPS family-expansion workflows

This policy updates traceability rules for OPS family expansion.

It preserves the current approved canonical business identifiers and does not reintroduce older internal ID schemes based on `asset_id` and `doc_id`.

---

## 2. Core Principle

The system must prefer canonical business identifiers whenever they are already available and stable enough for the current layer.

The current approved canonical reference model is:

- `family_id`
- `publication_number`
- `chunk_id`
- `vector_id`

The system must not reintroduce unnecessary parallel identifiers when the business identifier already exists and is usable.

The system must also distinguish clearly between:

- canonical business identity
- relationship identity
- mapping identity
- technical row identity

These are not interchangeable.

---

## 3. Approved Key Types

### 3.1 Canonical business keys

Canonical business keys are the primary identity anchors of the system.

#### `family_id`

Definition:

- family-level business identifier
- current dataset-family warehouse anchor
- current landscape headline family key

Used in:

- family-level warehouse modeling
- family-level reporting
- landscape interpretation
- family-publication bridge alignment
- family-to-OPS mapping alignment

Important:

- `family_id` remains the authoritative family truth for the current project
- `family_id` must not be silently replaced by OPS family cluster identity

#### `publication_number`

Definition:

- publication-level business identifier
- current publication-grain warehouse and BM25 anchor

Used in:

- publication-level warehouse modeling
- BM25 document serving
- publication-level traceability
- family-publication bridge alignment

Important:

- `publication_number` remains the canonical publication-level business identifier
- publication-level serving behavior must not silently redefine family-level truth

---

### 3.2 Semantic serving keys

Semantic serving keys are used only for semantic retrieval and embedding workflows.

#### `chunk_id`

Definition:

- semantic unit identifier
- used for chunk-level retrieval and evidence traceability

Used in:

- chunk generation
- chunk-level semantic retrieval
- evidence highlighting
- claim/spec retrieval workflows

#### `vector_id`

Definition:

- embedding artifact identifier
- used to identify vector records or embedding-level serving units

Used in:

- vector store alignment
- embedding reload / refresh workflows
- semantic serving traceability

---

### 3.3 Relationship keys

Relationship keys are allowed when a table needs a readable identifier for a relationship record.

A relationship key is not a canonical business key.

It exists to identify a relationship row in a readable and controlled way.

#### Current approved example

`ops_family_member_key`

Format:

```text
<ops_family_id>_<member_jurisdiction><3-digit-sequence>

Example:

```
69845166_EP001
69845166_EP002
69845166_WO003
```

Definition:

- `ops_family_id` = OPS family cluster identifier
- `member_jurisdiction` = publication jurisdiction of the member
- `3-digit-sequence` = member sequence within the same OPS family ordering rule

Purpose:

- make OPS member rows human-readable
- make OPS member lineage easier to inspect
- avoid opaque hash-only relationship keys where readability is more useful

Important:

- relationship keys must not replace canonical business keys
- relationship keys must not be promoted to global system identity anchors
- relationship keys must not be used as a substitute for dataset family truth

---

### 3.4 Mapping keys

Mapping keys are allowed when two identity systems must be aligned without collapsing them into one identifier.

A mapping key is not a canonical business key.

A mapping key is also not a relationship row key.

It exists to support controlled identity alignment between different systems or identity domains.

### Current approved mapping use case

`family_id` ↔ `ops_family_cluster_id`

Definition:

- `family_id` = canonical dataset-family identity
- `ops_family_cluster_id` = OPS-side family expansion cluster identity

Purpose:

- align dataset family truth with OPS expansion context
- allow family-member expansion to be attached to the correct dataset family
- preserve the distinction between dataset family identity and OPS family clustering

Important:

- `ops_family_cluster_id` must not replace `family_id`
- the mapping layer exists because the two identities are related, not equivalent
- mapping identity must remain explicit and inspectable

### Approved mapping object example

`gold.bridge_family_ops_cluster`

Suggested grain:

- `1 row = 1 family_id x 1 ops_family_cluster_id`

Suggested minimum columns:

- `family_id`
- `ops_family_cluster_id`
- `mapping_method`
- `mapping_confidence`
- `record_source`
- `loaded_at`

This table is a mapping layer, not a canonical identity table.

---

### 3.5 Technical row identifiers

Technical row identifiers are allowed for operational convenience.

Example:

- `ops_family_member_row_id`

Purpose:

- row ordering
- debugging
- operational inspection

Technical row identifiers are:

- not business truth
- not cross-run stable unless explicitly designed that way
- not substitutes for canonical business keys

---

## 4. Explicitly Disallowed Keys

The following identifiers are not approved as canonical system identifiers in the current project state.

### `asset_id`

Disallowed as a canonical family-level replacement.

Reason:

- `family_id` already exists and is currently the approved family-level business key
- introducing `asset_id` creates unnecessary parallel identity logic
- it increases governance complexity without clear benefit in the current warehouse model

### `doc_id` as a replacement for `publication_number`

Disallowed as canonical publication identity.

Reason:

- `publication_number` already serves as the current publication-level business key
- replacing it with a generated hash-style identifier adds unnecessary indirection
- current BM25 and warehouse alignment should remain publication-number based

### `ops_family_cluster_id` as a replacement for `family_id`

Disallowed as canonical family identity.

Reason:

- OPS family clustering is an external expansion context, not the dataset-family truth
- dataset family identity and OPS cluster identity are not guaranteed to represent the same identity contract
- treating OPS cluster identity as dataset family truth would create silent identity drift

### `seed_publication_number` as the sole family-alignment key

Disallowed as the only approved alignment key between OPS expansion and dataset family truth.

Reason:

- seed publications used for OPS lookup may differ from the dataset anchor selected publication
- exact equality between `seed_publication_number` and anchor `publication_number` is not guaranteed across jurisdictions or publication variants
- `seed_publication_number` may remain useful as source lineage context, but it must not be the sole canonical alignment contract for family expansion

---

## 5. Lane-Aware Traceability

The system uses different keys depending on the lane.

### 5.1 Landscape lane

Primary trace key:

- `family_id`

Trace intent:

- family-level reporting
- family-level aggregation
- family-level business interpretation

Landscape must remain family-grain.

---

### 5.2 BM25 lane

Primary trace key:

- `publication_number`

Trace intent:

- publication-level keyword retrieval
- searchable document serving
- publication-level result tracing

BM25 is a publication-grain lane.

BM25 result counts must not be confused with family headline counts.

---

### 5.3 Semantic lane

Primary trace keys:

- `chunk_id`
- `vector_id`

Supporting trace keys:

- `publication_number`
- `family_id` where available in metadata

Trace intent:

- explainable semantic retrieval
- embedding lineage
- chunk-level evidence tracing

---

### 5.4 OPS family-expansion lane

Primary trace keys:

- `ops_family_member_key`
- `ops_family_cluster_id`

Supporting alignment keys:

- `family_id`
- `publication_number`
- `seed_publication_number` as source lineage context only

Trace intent:

- family-member expansion lineage
- OPS cluster inspection
- controlled alignment back to dataset-family truth

OPS family expansion must remain traceable both to:

- its OPS-side source context
- its dataset-family alignment context

---

## 6. Relationship Between Keys

The approved reference model is layered and non-redundant.

### Business identity layer

- `family_id`
- `publication_number`

### Semantic identity layer

- `chunk_id`
- `vector_id`

### Relationship layer

- `ops_family_member_key`
- future bridge-level readable relationship keys, if explicitly documented

### Mapping layer

- `family_id ↔ ops_family_cluster_id`
- future documented cross-system mapping keys, if explicitly approved

### Technical layer

- row ids
- load sequence ids
- helper counters

Each layer has a different purpose and must not be confused with another.

---

## 7. Traceability Requirements

Every user-visible retrieval or analytics artifact must be traceable backward through the appropriate lane.

### BM25 example

BM25 result

→ `publication_number`

→ `gold.bm25_document`

→ publication metadata

→ family alignment through `gold.bridge_family_publication` if needed

### Semantic example

Semantic hit

→ `vector_id`

→ `chunk_id`

→ `publication_number`

→ `family_id` (if mapped)

→ source lineage

### OPS family expansion example

OPS family member row

→ `ops_family_member_key`

→ `ops_family_cluster_id`

→ `gold.bridge_family_ops_cluster`

→ `family_id`

→ `gold.bridge_family_publication`

→ landscape reporting / family-level interpretation

Supporting source lineage may additionally include:

→ `seed_publication_number`

→ raw OPS JSONL record

Important:

- `seed_publication_number` remains a valid operational lineage field
- it is not the approved sole family-alignment key

---

## 8. Governance Rules

### Allowed

Allowed:

- using `family_id` as canonical family identity
- using `publication_number` as canonical publication identity
- using `chunk_id` and `vector_id` for semantic workflows
- using readable relationship keys for relationship tables
- using explicit mapping objects for cross-system identity alignment
- using technical row ids for operational convenience
- keeping `seed_publication_number` as lineage context where relevant

### Not allowed

Not allowed:

- reintroducing `asset_id` as canonical family identity
- replacing `publication_number` with generated `doc_id` as canonical publication identity
- using relationship keys as global business truth
- using technical row ids as business identifiers
- mixing lane-specific keys without documenting the trace path
- letting `ops_family_cluster_id` silently replace `family_id`
- treating `seed_publication_number` as the sole approved family-alignment key

---

## 9. Current Project Application

The current project applies this policy as follows:

- `family_id` = canonical family key
- `publication_number` = canonical publication key
- `chunk_id` = semantic chunk key
- `vector_id` = vector artifact key
- `ops_family_member_key` = readable OPS relationship key
- `ops_family_member_row_id` = technical row sequence only
- `ops_family_cluster_id` = OPS-side expansion cluster identity, not canonical dataset-family identity
- `gold.bridge_family_ops_cluster` = approved family-to-OPS mapping layer
- `gold.bridge_family_publication` = family-to-publication bridge under the dataset-family contract

This policy is aligned with the current warehouse and retrieval model and supersedes older internal hash-first identity designs.

---

## 10. Final Principle

The system should not invent new identifiers unless there is a clear governance need.

When an existing business identifier is already sufficient, it should remain the primary key of meaning.

When two identity systems must be aligned but should not be collapsed, the alignment must be modeled explicitly through a mapping layer.

In short:

- use business keys for business identity
- use semantic keys for semantic serving
- use relationship keys for readable relationship rows
- use mapping keys for controlled cross-system alignment
- use technical row ids only for operational convenience