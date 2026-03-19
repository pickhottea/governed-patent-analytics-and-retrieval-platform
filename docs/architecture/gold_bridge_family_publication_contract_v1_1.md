# gold.bridge_family_publication Contract v1.1

## 1. Purpose

This document defines the warehouse contract for `gold.bridge_family_publication`.

The purpose of this table is to provide an explicit alignment layer between:

- dataset-family identity
- publication identity
- future OPS family-member expansion
- BM25 representative-publication behavior
- landscape family-level reporting

This table exists to prevent silent misuse of publication-level collapse as family-level truth.

---

## 2. Why This Table Is Required

The current project already distinguishes at least two valid but different analytical views:

- **family-grain truth**
- **publication-grain retrieval**

This distinction creates a governance requirement.

At the current stage:

- the anchor family universe is 150 dataset families
- BM25 may collapse to 149 searchable publications
- semantic retrieval is handled separately
- future OPS expansion may introduce additional family-member lineage

Without a bridge layer, these views can become mixed in downstream reporting.

`gold.bridge_family_publication` is the required table that keeps those layers aligned.

---

## 3. Table Role

`gold.bridge_family_publication` is the canonical bridge between:

- `family_id`
- `publication_number`

It records which publications belong to which dataset-family context, and how that publication is being used in the current pipeline.

This table does **not** replace:

- `gold.dim_family`
- `gold.dim_publication`

It complements them.

---

## 4. Grain

**Grain:**

`1 row = 1 family_id x 1 publication_number`

This means:

- one family may map to multiple publications
- one publication may map to multiple families
- such many-to-many relationships must be stored explicitly
- no silent collapse is allowed at this layer

---

## 5. Primary Contract

The table must preserve the following rule:

> Dataset-family identity must remain explicit even when multiple dataset families converge onto the same publication.

Therefore:

- publication-level reuse is allowed
- family-level overwrite is not allowed
- family-to-publication collision must be visible

---

## 6. Minimum Required Columns

The minimum required columns for `gold.bridge_family_publication` are:

- `family_id`
- `publication_number`
- `member_role`
- `ops_family_cluster_id`
- `is_bm25_representative`
- `has_publication_collision`
- `collision_flag`
- `record_source`
- `loaded_at`

---

## 7. Column Definitions

### 7.1 `family_id`

Type: integer or bigint, aligned with warehouse family key

Definition:

- dataset-family identity
- the family-level reporting identity
- the family universe used by landscape headline counts

This column is required.

### 7.2 `publication_number`

Type: varchar / nvarchar

Definition:

- publication-level identity
- the document identity used in BM25 and publication-level retrieval layers

This column is required.

### 7.3 `member_role`

Type: varchar

Definition:

- role of this publication within the current family context

Suggested values:

- `anchor`
- `expanded_member`
- `selected_rep`

Interpretation:

- `anchor`: publication came from current anchor source
- `expanded_member`: publication came from OPS family-member expansion
- `selected_rep`: publication is currently used as the selected representative publication for that family

This column is required.

### 7.4 `ops_family_cluster_id`

Type: varchar / nvarchar / nullable

Definition:

- identifier representing OPS-derived family cluster membership
- used for expansion lineage and coverage analysis
- not equivalent to `family_id`

This column is optional at initial load, but reserved from v1 onward.

If the value is not yet available, it may remain null.

### 7.5 `is_bm25_representative`

Type: bit / boolean

Definition:

- indicates whether this publication is the current BM25-serving representative for the given family context

Interpretation:

- `1` = used by BM25 lane as representative publication for this family
- `0` = not used as BM25 representative

This column is required because BM25 behavior must remain auditable.

### 7.6 `has_publication_collision`

Type: bit / boolean

Definition:

- indicates whether the same `publication_number` appears under more than one `family_id`

Interpretation:

- `1` = this publication participates in family-to-publication collision
- `0` = no currently observed collision for this publication

This column is required.

### 7.7 `collision_flag`

Type: varchar / nullable

Definition:

- explicit governance label for collision-aware downstream handling

Suggested value:

- `FAMILY_TO_PUBLICATION_COLLISION`

Interpretation:

- null = no current collision flag
- populated = collision exists and must be handled explicitly

This column is required as a contract field, even if null for many rows.

### 7.8 `record_source`

Type: varchar

Definition:

- source lineage of this bridge row

Suggested values:

- `anchor_rawdata_patents`
- `ops_family_members`
- `representative_selection`
- `manual_reconciliation`

This column is required.

### 7.9 `loaded_at`

Type: datetime2

Definition:

- warehouse load timestamp for this bridge row

This column is required.

---

## 8. Optional Recommended Columns

The following columns are optional but recommended:

- `is_anchor_publication`
- `is_landscape_family_seed`
- `selection_policy_version`
- `expansion_batch_id`
- `notes`

These are not required for v1 but may improve auditability.

---

## 9. Relationship to Other Gold Tables

### 9.1 Relationship to `gold.dim_family`

`gold.dim_family` remains the family dimension.

`gold.bridge_family_publication` must not replace it.

Expected join:

- `gold.bridge_family_publication.family_id`
- `gold.dim_family.family_id`

### 9.2 Relationship to `gold.dim_publication`

`gold.dim_publication` remains the publication dimension.

`gold.bridge_family_publication` must not replace it.

Expected join:

- `gold.bridge_family_publication.publication_number`
- `gold.dim_publication.publication_number`

Important interpretation:

- `gold.dim_publication` is a publication entity dimension
- it should be interpreted as `1 row = 1 publication_number`
- it should not be interpreted as a single-family ownership table
- publication-to-family membership remains governed by `gold.bridge_family_publication`

### 9.3 Relationship to `gold.bm25_document`

`gold.bm25_document` is a publication-grain retrieval artifact.

It may collapse family context.

`gold.bridge_family_publication` is the required interpretive layer that explains how that publication relates back to dataset-family context.

Therefore:

- `gold.bm25_document` is not family truth
- `gold.bridge_family_publication` is required to reconnect BM25 outputs to family identity

---

## 10. Allowed Behaviors

Allowed:

- one `family_id` mapping to multiple `publication_number` values
- one `publication_number` mapping to multiple `family_id` values
- publication-level reuse across dataset-family contexts
- explicit collision flagging
- future OPS expansion enriching the bridge
- publication-only `gold.dim_publication` modeling alongside many-to-many family membership in the bridge

---

## 11. Not Allowed

Not allowed:

- enforcing one-to-one uniqueness between `family_id` and `publication_number`
- overwriting one family context with another because the publication is identical
- using BM25 publication count as the official family headline count
- silently collapsing bridge rows during load
- replacing `family_id` with OPS cluster identity
- treating `gold.dim_publication` as proof that each publication belongs to only one family

---

## 12. Data Quality Rules

The following rules should be enforced in testing.

### 12.1 Required non-null fields

These fields must be non-null:

- `family_id`
- `publication_number`
- `member_role`
- `is_bm25_representative`
- `has_publication_collision`
- `record_source`
- `loaded_at`

### 12.2 Grain integrity

The table must allow:

- multiple rows per `family_id`
- multiple rows per `publication_number`

But it must not allow duplicate rows at the exact bridge grain:

- duplicate `family_id x publication_number x member_role x record_source`

If exact duplicates are present, they must be treated as load defects.

### 12.3 Collision consistency

If the same `publication_number` appears under multiple `family_id` values:

- `has_publication_collision` must be `1`
- `collision_flag` should be populated

If a publication appears under only one family:

- `has_publication_collision` should be `0`

### 12.4 BM25 representative consistency

If `is_bm25_representative = 1`:

- the row must correspond to a publication that is eligible for BM25 serving
- only one active BM25 representative should exist per family under a given selection policy version

This rule may later be enforced through additional versioning metadata.

---

## 13. Downstream Interpretation Rules

### 13.1 For BM25 lane

Use:

- `publication_number`
- `is_bm25_representative`

Do not interpret BM25 row counts as family headline counts.

### 13.2 For Landscape lane

Use:

- `family_id`
- bridge rows
- collision-aware family interpretation

Landscape headline counts must remain family-grain.

### 13.3 For Coverage and Expansion

Use:

- `ops_family_cluster_id`
- `member_role`
- `record_source`

Do not replace dataset-family truth with OPS clustering.

### 13.4 For publication-grain dimensions

Use:

- `publication_number`
- publication-grain dims and facts
- `gold.bridge_family_publication` when family context is needed

Do not infer single-family ownership from the existence of a publication row in `gold.dim_publication`.

---

## 14. Initial Population Strategy

The recommended initial population sequence is:

1. load anchor-based family-publication pairs from current anchor source
2. mark anchor rows with `member_role = 'anchor'`
3. identify selected BM25 representative rows
4. set collision fields based on repeated `publication_number` across families
5. later enrich with OPS expansion rows using `member_role = 'expanded_member'`

This allows the bridge to exist before full expansion is complete.

---

## 15. v1.1 Implementation Principle

Version 1.1 preserves the v1 bridge contract and adds one clarifying rule:

- `gold.dim_publication` is publication-only
- publication-to-family membership remains bridge-governed

Version 1.1 still does not require full OPS family expansion to exist on day one.

It requires only that:

- family-publication mapping be made explicit
- publication collision be visible
- BM25 representative behavior be reconnectable to family context
- publication identity and family membership not be silently conflated

---

## 16. Final Principle

`gold.bridge_family_publication` is the alignment table that protects family identity from being silently absorbed by publication-level retrieval behavior.

It also protects publication identity from being misread as single-family ownership.

In short:

> BM25 may serve publications.
> Landscape must report families.
> `gold.dim_publication` may model publication identity.
> The bridge must preserve publication-to-family membership.
