# Family Identity and Lane Contract v1

## 1. Purpose

This document defines the current governance contract for family identity across the three project lanes:

- BM25 lane
- Landscape lane
- Semantic lane

Its purpose is to prevent silent identity collapse when publication-level retrieval outputs, dataset-family reporting, and future family-member expansion are combined in the same warehouse.

This is a contract document for current project alignment.  
It is not a historical debugging memo and it is not a policy rewrite.

---

## 2. Current Project Truth

The current project baseline is:

- warehouse layering uses `bronze`, `silver`, and `gold`
- warehouse identity uses:
  - `family_id` as family-level key
  - `publication_number` as publication-level key
  - `chunk_id` as semantic unit key
  - `vector_id` as embedding artifact key
- warehouse identity does **not** reintroduce `asset_id`
- the current anchor source is `data/raw/anchor/rawdata_patents.xlsx`
- current anchor interpretation is:

> 1 row = 1 selected publication representing 1 family

Observed current behavior of the anchor source:

- rows = 150
- distinct `family_id` = 150
- distinct `publication_number` = 150

This source is valid for:

- anchor loading
- early warehouse modeling
- structured publication metadata

This source is **not** full family-member coverage.

---

## 3. Current Raw Source Roles

### 3.1 Anchor source

`data/raw/anchor/rawdata_patents.xlsx`

Role:

- selected-publication anchor source
- current warehouse authority for anchor-level publication metadata

### 3.2 Expansion sources

- `data/raw/expansion/ops_family_members.jsonl`
- `data/raw/expansion/raw_pub_to_family_id.json`
- `data/raw/expansion/raw_pub_to_family_id_v2.json`

Role:

- future family-member expansion
- bridge / lineage / coverage support
- not current anchor authority

### 3.3 Retrieval-support sources

- `data/raw/retrieval/patents_canonical.jsonl`
- `data/raw/retrieval/claims_representation_v3.jsonl`

Role:

- retrieval-support artifacts
- BM25 / semantic preparation artifacts
- not current bronze anchor authority

---

## 4. Canonical Identity Concepts

This project currently distinguishes three different identity layers.

### 4.1 Dataset family identity

`family_id`

Definition:

- the dataset-family identity currently used by the warehouse
- the current project headline family universe
- current expected headline count = 150

This is the identity used for:

- family-level reporting
- landscape headline counts
- future family-publication bridge modeling

### 4.2 Publication identity

`publication_number`

Definition:

- publication-level document identity
- the identity used for BM25 publication documents
- the identity used for publication-level deduplication

This identity may legally collapse multiple dataset-family contexts into one publication-level searchable document set.

### 4.3 OPS family cluster identity

`ops_family_cluster_id`  
(name reserved for future explicit modeling)

Definition:

- the family cluster identity derived from OPS family-member expansion
- used for expansion, coverage, and lineage support
- not equivalent to `family_id`

This identity must not silently overwrite or replace dataset-family identity.

---

## 5. Lane Contracts

### 5.1 BM25 lane

BM25 is a **publication-grain retrieval lane**.

Current BM25 contract:

- grain = `1 row = 1 publication_number`
- current text contract = `title + abstract`
- current abstract enrichment may come from `patents_canonical.jsonl`
- BM25 document generation is allowed to perform publication-level collapse

This means:

- BM25 row count is **not** the authoritative family count
- BM25 may show 149 searchable publication documents even when the dataset-family universe remains 150
- publication-level collapse in BM25 is acceptable for keyword retrieval

It is **not** acceptable to reuse BM25 row count as the official family headline count.

### 5.2 Landscape lane

Landscape is a **dataset-family-grain reporting lane**.

Current landscape contract:

- headline family universe remains the dataset-family universe
- current expected headline family count remains 150
- landscape must preserve dataset-family identity even if two families later map to the same publication-level representative

This means:

- landscape must not inherit BM25 publication collapse as headline truth
- landscape must report family-level truth first
- publication collision may be surfaced as a separate metric, but must not silently reduce headline family count

### 5.3 Semantic lane

Semantic lane is currently treated as a separate governed lane.

For the purpose of this contract refresh:

- semantic lane is out of scope
- current semantic implementation is not redefined here
- this document focuses only on BM25 lane and landscape lane alignment

---

## 6. Collision Contract

A collision exists when:

- multiple `family_id` values map to the same `publication_number`
- or future expansion logic causes multiple dataset-family contexts to converge onto the same publication-level representative

This is defined as:

**family-to-publication collision**

Important interpretation:

- this is not automatically a storage bug
- this is not automatically a retrieval bug
- this becomes a governance problem only when publication-level collapse is silently mistaken for family-level truth

Therefore:

- BM25 may absorb this collision at the searchable-document layer
- landscape must not absorb this collision at the family headline layer
- collision must be modeled explicitly and surfaced explicitly

---

## 7. Current 150 / 149 Interpretation

At the current stage, the project must distinguish two different counts.

### 7.1 Family headline count

`dataset_family_count`

Current expected value:

- 150

Interpretation:

- current warehouse family universe
- landscape headline truth
- based on current anchor interpretation

### 7.2 Collapsed searchable-publication count

`collapsed_publication_count`

Current observed possible value:

- 149

Interpretation:

- publication-level searchable set after publication collapse
- acceptable in BM25 lane
- not acceptable as family headline truth

Therefore, `150 -> 149` is not a single-number problem.

It is a contract distinction between:

- family universe
- publication search universe

---

## 8. Required Output Metrics

The following metrics must be surfaced explicitly after family expansion and lane reconciliation are implemented:

- `dataset_family_count`
- `collapsed_publication_count`
- `collision_family_count`
- `collision_publication_count`
- `ops_expanded_member_count`

Minimum interpretation rules:

- `dataset_family_count` is the landscape headline count
- `collapsed_publication_count` is the BM25 searchable-publication count
- collision metrics must be visible and testable

---

## 9. Required Warehouse Contract Update

To support the above distinction, the warehouse must add an explicit family-publication bridge.

### 9.1 Required future table

`gold.bridge_family_publication`

### 9.2 Grain

`1 row = 1 family_id x 1 publication_number`

### 9.3 Minimum required columns

- `family_id`
- `publication_number`
- `member_role`
- `ops_family_cluster_id`
- `is_bm25_representative`
- `has_publication_collision`
- `collision_flag`
- `record_source`
- `loaded_at`

### 9.4 Column interpretation

`member_role` suggested values:

- `anchor`
- `expanded_member`
- `selected_rep`

`collision_flag` suggested value for current governance use case:

- `FAMILY_TO_PUBLICATION_COLLISION`

This bridge table becomes the required alignment layer between:

- anchor family truth
- future OPS expansion
- BM25 searchable document construction
- landscape family reporting

---

## 10. Lane-Safe Usage Rules

### 10.1 Allowed

Allowed:

- BM25 using publication-level document collapse
- landscape using dataset-family headline counts
- future OPS expansion enriching bridge and coverage layers
- explicit collision testing and reporting

### 10.2 Not allowed

Not allowed:

- using BM25 row count as family headline count
- letting OPS-derived clustering silently replace dataset-family identity
- treating publication-level deduplication as landscape family deduplication
- reporting 149 as the official family universe unless the family contract itself is explicitly redefined

---

## 11. Immediate Implementation Consequences

The next alignment steps should be:

1. keep current BM25 lane as publication-grain
2. preserve landscape headline family universe as 150
3. implement `gold.bridge_family_publication`
4. add collision-aware tests
5. only then decide how future family expansion should affect landscape member metrics

This means:

- BM25 can continue now
- landscape should not be rewritten using BM25 counts
- family expansion must be written under the bridge contract, not ad hoc

---

## 12. Final Principle

This project accepts publication-level collapse as a valid retrieval behavior.

This project does **not** allow publication-level collapse to silently redefine dataset-family truth.

In short:

> BM25 may collapse documents.  
> Landscape may not collapse family truth.  
> Collision must be modeled, tested, and surfaced.