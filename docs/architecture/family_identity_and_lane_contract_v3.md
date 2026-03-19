# Family Identity and Lane Contract v3.1

## 1. Purpose

This document defines the current architecture contract for family identity alignment between:

- warehouse family truth
- publication-grain BM25 serving
- OPS family-member expansion
- future family-level landscape reporting enriched by expansion coverage

Its purpose is to prevent silent identity collapse when publication-level retrieval outputs, family-level reporting, and OPS expansion are combined in the same warehouse.

This document is an architecture contract.

It does not redefine global key policy or retrieval policy.
Those are governed separately in:

- `policies/reference_key_and_traceability_policy_v1_1.md`
- `policies/two_lane_retrieval_policy_v1.md`

---

## 2. Current Project Baseline

The current project baseline is:

- warehouse layering uses `bronze`, `silver`, and `gold`
- the current anchor source is `data/raw/anchor/rawdata_patents.xlsx`
- current anchor interpretation is:

> 1 row = 1 selected publication representing 1 family

Observed current anchor behavior:

- rows = 150
- distinct `family_id` = 150
- distinct `publication_number` = 150

This source is valid for:

- anchor loading
- early warehouse modeling
- structured publication metadata
- initial family-to-publication anchor definition

This source is not full family-member coverage.

---

## 3. Current Source Roles

### 3.1 Anchor source

`data/raw/anchor/rawdata_patents.xlsx`

Role:

- selected-publication anchor source
- current warehouse authority for anchor-level publication metadata
- current warehouse authority for dataset-family anchor alignment

### 3.2 Expansion sources

- `data/raw/expansion/ops_family_members.jsonl`
- `data/raw/expansion/raw_pub_to_family_id.json`
- `data/raw/expansion/raw_pub_to_family_id_v2.json`

Role:

- family-member expansion
- bridge / lineage / coverage support
- OPS-derived relationship expansion
- OPS cluster context for future family-level coverage enrichment

### 3.3 Retrieval-support sources

- `data/raw/retrieval/patents_canonical.jsonl`
- `data/raw/retrieval/claims_representation_v3.jsonl`

Role:

- retrieval-support artifacts
- BM25 / semantic preparation artifacts
- not warehouse family-truth sources

---

## 4. Current Family and Publication Interpretation

The warehouse must explicitly distinguish two different interpretations.

### 4.1 Family truth

Family truth is represented by:

- `family_id`

Current family headline universe:

- 150 dataset families

This is the identity used for:

- family-level reporting
- landscape headline counts
- family-level reconciliation
- family-publication bridge alignment
- family-to-OPS mapping alignment

### 4.2 Publication serving view

Publication serving is represented by:

- `publication_number`

This is the identity used for:

- BM25 searchable documents
- publication-level retrieval serving
- publication-level deduplication where explicitly allowed
- publication-level lineage under the family contract

The publication serving layer is not the same thing as family truth.

### 4.3 OPS expansion context

OPS expansion context is represented by:

- `ops_family_cluster_id`
- OPS member publications
- source-side seed lookup context

This is used for:

- expansion lineage
- family-member coverage support
- family-to-OPS mapping
- future expansion-aware family reporting

OPS expansion context is not the same thing as dataset family truth.

---

## 5. BM25 and Landscape Contract Boundary

### 5.1 BM25

BM25 is publication-grain.

Current BM25 contract:

- grain = `1 row = 1 publication_number`
- current text contract = `title + abstract`
- publication-level collapse is allowed in the searchable-document layer

Therefore:

- BM25 row count is not the authoritative family count
- BM25 may show 149 searchable publication documents even when the family universe remains 150

### 5.2 Landscape

Landscape is family-grain.

Current landscape contract:

- headline family universe remains the dataset-family universe
- current expected family headline count remains 150

Therefore:

- landscape must not inherit BM25 publication collapse as headline truth
- publication-level collapse may be surfaced as a metric
- it must not silently reduce family headline counts

### 5.3 OPS expansion

OPS expansion is support for family-member coverage, lineage, and bridge enrichment.

Therefore:

- OPS expansion may enrich family-publication coverage
- OPS expansion may enrich family-level member metrics
- OPS expansion must not silently replace dataset-family identity
- OPS expansion must not redefine landscape headline counts by itself

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
- it becomes a governance problem only when publication-level collapse is silently mistaken for family-level truth

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
- acceptable in BM25
- not acceptable as family headline truth

Therefore, `150 -> 149` is not a single-number problem.

It is a contract distinction between:

- family universe
- publication search universe

---

## 8. Alignment Failure Learned from Current Implementation

The project has now verified an important alignment constraint.

### 8.1 Rejected assumption

The following exact-match assumption is not approved as the general OPS expansion alignment rule:

```text
anchor publication_number = OPS seed_publication_number
```

Reason:

- the OPS seed publication universe may differ from the selected anchor publication universe
- OPS lookup seeds may come from different jurisdictions or publication variants
- exact publication-number equality is not guaranteed even when the family expansion is still relevant to the same dataset family

### 8.2 Consequence

OPS family expansion must not rely on publication-to-publication exact equality as the sole family-alignment mechanism.

This means:

- `seed_publication_number` remains valid as OPS lookup lineage
- `seed_publication_number` does not define dataset-family truth
- publication-number equality may be supporting evidence
- publication-number equality is not the primary architecture contract for family expansion alignment

### 8.3 Approved correction

OPS family expansion must align through an explicit family-level mapping layer.

Approved alignment path:

```text
family_id
→ family-to-OPS mapping
→ ops_family_cluster_id
→ OPS family members
→ member publication_number
```

This path preserves:

- dataset family truth
- OPS cluster traceability
- family-member publication coverage
- lane-safe reporting behavior

---

## 9. Required Output Metrics

The following metrics must be surfaced explicitly after family expansion and lane reconciliation are implemented:

- `dataset_family_count`
- `collapsed_publication_count`
- `collision_family_count`
- `collision_publication_count`
- `ops_expanded_member_count`
- `mapped_ops_cluster_count`
- `family_expansion_coverage_count`

Minimum interpretation rules:

- `dataset_family_count` is the landscape headline count
- `collapsed_publication_count` is the BM25 searchable-publication count
- collision metrics must be visible and testable
- OPS expansion metrics must be visible separately from family headline counts

---

## 10. Required Warehouse Contract Update

To support the above distinction, the warehouse must include both:

- an explicit family-to-OPS mapping layer
- an explicit family-to-publication bridge
- a publication dimension that represents publication identity without silently collapsing family membership into a single-valued attribute

### 10.1 Required mapping table

`gold.bridge_family_ops_cluster`

### 10.2 Mapping grain

`1 row = 1 family_id x 1 ops_family_cluster_id`

### 10.3 Minimum required mapping columns

- `family_id`
- `ops_family_cluster_id`
- `mapping_method`
- `mapping_confidence`
- `record_source`
- `loaded_at`

### 10.4 Mapping interpretation

`mapping_method` suggested values:

- `source_attached`
- `seed_lineage_verified`
- `manual_verified`
- `derived_with_review`

`mapping_confidence` suggested values:

- `high`
- `medium`
- `low`

Important:

- this table exists to align dataset-family truth with OPS cluster context
- this table is a mapping layer, not a canonical family identity table
- `ops_family_cluster_id` must not replace `family_id`

---

## 11. Required Family-Publication Bridge Contract

### 11.1 Required table

`gold.bridge_family_publication`

### 11.2 Grain

`1 row = 1 family_id x 1 publication_number`

### 11.3 Minimum required columns

- `family_id`
- `publication_number`
- `member_role`
- `ops_family_cluster_id`
- `is_bm25_representative`
- `has_publication_collision`
- `collision_flag`
- `record_source`
- `loaded_at`

### 11.4 Column interpretation

`member_role` suggested values:

- `anchor`
- `expanded_member`
- `selected_rep`

`collision_flag` suggested value for current governance use case:

- `FAMILY_TO_PUBLICATION_COLLISION`

`record_source` suggested values may include:

- `anchor_rawdata_patents`
- `ops_family_members`
- `anchor+ops_expansion`

### 11.5 Required alignment rule for expansion rows

Anchor rows may come directly from the anchor source.

Expanded member rows must not depend solely on:

```text
anchor publication_number = OPS seed_publication_number
```

Instead, expansion rows must be attached by:

```text
family_id
→ gold.bridge_family_ops_cluster
→ ops_family_cluster_id
→ silver.ops_family_members
→ member publication_number
```

This bridge table remains the required alignment layer between:

- anchor family truth
- OPS expansion
- BM25 searchable document construction
- landscape family reporting

---

## 12. Publication Dimension Interpretation

`gold.dim_publication` is the publication entity dimension.

Approved interpretation:

- grain = `1 row = 1 publication_number`
- it represents publication identity, not family ownership
- it may be used as the parent dimension for publication-grain facts and bridges

Not approved:

- treating `gold.dim_publication.family_id` as a required single-valued attribute
- interpreting `gold.dim_publication` as a one-publication-to-one-family ownership table
- using `gold.dim_publication` to replace `gold.bridge_family_publication`

If a publication participates in multiple dataset-family contexts, that many-to-many membership must remain modeled through `gold.bridge_family_publication`.

---

## 13. Current Transitional Interpretation

The project may temporarily hold a partial-coverage version of `gold.bridge_family_publication` built from exact seed-publication matching.

If such a version exists, it must be interpreted as:

- structurally valid for already matched rows
- not the final architecture-complete expansion bridge
- incomplete for full OPS family-member coverage

This means:

- its anchor rows may still be fully valid
- its family headline universe may still be valid
- its OPS expansion coverage may be partial if it depends on exact seed-publication equality

The architecture-complete target remains the family-mapped version.

---

## 14. Lane-Safe Usage Rules

### 14.1 Allowed

Allowed:

- BM25 using publication-level document collapse
- landscape using dataset-family headline counts
- OPS expansion enriching bridge and coverage layers
- explicit collision testing and reporting
- explicit family-to-OPS mapping
- family-member publication enrichment through mapped OPS clusters
- using `gold.dim_publication` as the publication-grain parent dimension for publication-grain marts and tests

### 14.2 Not allowed

Not allowed:

- using BM25 row count as family headline count
- letting OPS-derived clustering silently replace dataset-family identity
- treating publication-level deduplication as landscape family deduplication
- reporting 149 as the official family universe unless the family contract itself is explicitly redefined
- using `seed_publication_number` as the sole approved family-alignment contract for OPS expansion
- allowing OPS expansion to bypass the family mapping layer when family identity is the downstream reporting truth
- forcing publication-to-family membership into a single-valued publication dimension attribute

---

## 15. Immediate Implementation Consequences

The next alignment steps are:

1. keep BM25 as publication-grain
2. preserve landscape headline family universe as 150
3. preserve `gold.bridge_family_publication` as the official family-publication bridge
4. add `gold.bridge_family_ops_cluster` as the official family-to-OPS mapping layer
5. migrate OPS expansion alignment to the family-mapped path
6. add collision-aware tests
7. add mapping-coverage tests
8. keep `gold.dim_publication` publication-only at the identity layer
9. only then finalize OPS-driven family member metrics in landscape reporting

This means:

- BM25 can continue now
- landscape should not be rewritten using BM25 counts
- family expansion must be written under the mapping-plus-bridge contract, not ad hoc
- OPS cluster identity must remain explicit and inspectable

---

## 16. Minimum Test Expectations

The warehouse should test at least the following.

### 16.1 Family truth stability

- distinct `family_id` in family headline layer remains 150 unless the family contract itself is explicitly redefined

### 16.2 Bridge grain integrity

- `gold.bridge_family_publication` must not contain duplicate `(family_id, publication_number)` pairs

### 16.3 Mapping grain integrity

- `gold.bridge_family_ops_cluster` must not contain duplicate `(family_id, ops_family_cluster_id)` pairs

### 16.4 Collision visibility

- family-to-publication collision must be surfaced explicitly through collision flags and counts

### 16.5 Mapping coverage visibility

- the number of families with mapped OPS clusters must be measurable
- the number of expansion rows attached through family-level mapping must be measurable
- partial-coverage exact-join behavior must not be mistaken for full expansion success

### 16.6 Publication dimension integrity

- `gold.dim_publication` must enforce unique `publication_number`
- publication-grain facts and bridges should relationship-test to `gold.dim_publication`
- family membership must not be asserted through a single-valued `family_id` column on `gold.dim_publication`

---

## 17. Final Principle

This project accepts publication-level collapse as a valid retrieval behavior.

This project does not allow publication-level collapse to silently redefine dataset-family truth.

This project also does not allow OPS lookup context to silently redefine dataset-family identity.

This project further distinguishes publication identity from publication-to-family membership.

In short:

> BM25 may collapse documents.
> Landscape may not collapse family truth.
> OPS expansion must align through family-level mapping.
> Publication identity may be singular while family membership remains many-to-many.
> Collision and mapping coverage must be modeled, tested, and surfaced.
