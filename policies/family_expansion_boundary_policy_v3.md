# Family Expansion Boundary and Publication Dedup Policy v3

## Purpose

This policy defines how OPS-derived family expansion should be handled in the governed patent warehouse **after** the family-collision incident revealed that unrestricted expansion can create unsafe overlap.

This version replaces the earlier hard-boundary approach with a more review-oriented policy.

The goal is:

- keep expansion useful
- avoid naive auto-attachment
- avoid over-aggressive deletion
- preserve patent-domain complexity
- make human review an explicit part of the workflow

---

## Why this policy exists

Family expansion is not only a technical join problem.
It is also a **definition-scope problem**.

A dataset may treat family identity one way, while OPS expansion may surface a broader publication universe.

That means collisions can appear even when:

- primary keys exist
- the bridge is syntactically correct
- the source family IDs look stable

The `71103201` vs `78817222` incident showed this clearly.

That collision is therefore treated as the concrete motivating case for this policy.

---

## Family-definition complexity that must be acknowledged

### Narrow / simple-family style reasoning

A narrower family interpretation expects tighter family boundaries and fewer acceptable overlaps.

This style is closer to a "same originating priority basis / nearly equivalent publication family" view.

### Broad / extended-family style reasoning

A broader family interpretation allows a larger candidate universe because family linkage may be established through direct or indirect priority relationships.

### Policy implication

Even if the warehouse uses a stable canonical `family_id`, expansion can still create overlap because the **expanded publication universe may reflect a broader family logic than the dataset family itself**.

Therefore:

> family collision is a plausible side effect of family-definition mismatch during expansion, not only of bad keys or bad SQL

This is why publication-level dedup and human review are necessary.

---

## Core principle

> OPS expansion is a candidate publication pool, not final governed truth.

The warehouse still uses:

- `family_id` as canonical dataset family identity
- `publication_number` as canonical publication identity after normalization

But family expansion is allowed to remain broad **until publication-level dedup and review are applied**.

---

## What this policy rejects

This policy explicitly rejects the earlier hard-boundary approach that auto-blocked expansion using a crude boundary rule such as jurisdiction matching.

That kind of rule is too aggressive for patent-family reality because it can suppress legitimate complexity, including:

- overlapping publication histories
- same-base / different-kind publication events
- office-specific publication behavior
- patent-family relationships that are not safely reducible to one simple heuristic

So this policy does **not** say:

- cross-family overlap must be auto-deleted
- all ambiguous expansion must be blocked
- one hard gate can safely represent patent-family meaning

---

## New policy direction

### Rule 1 — normalize first

All OPS-derived publication identifiers must be normalized before comparison, deduplication, or bridge attachment.

Examples of unacceptable raw forms:

- `{'$':'EP'}{'$':'3919806'}{'$':'A1'}`
- `{'$':'US'}{'$':'11326744'}{'$':'B2'}`

Examples of acceptable governed publication keys:

- `EP3919806A1`
- `US11326744B2`

### Rule 2 — exact duplicate dedup only

Automatic deduplication is allowed only when the canonical publication identity is exactly the same.

That means exact match on:

- authority / jurisdiction
- base publication number
- kind / version code

In practice:

- `A1` vs `A1` can be deduplicated if the governed publication number is the same
- `A1` vs `A4` is **not** an automatic dedup case
- `A1` vs `B1` is **not** an automatic dedup case

### Rule 3 — same-base, different-kind goes to review

If two rows share a base publication number but differ in kind / version code, they must go to review.

Examples:

- `A1` vs `A4`
- `A1` vs `B1`
- `A1` vs `B2`
- office-specific special kinds

This policy treats publication-version semantics as meaningful enough that they should not be auto-collapsed casually.

### Rule 4 — suspicious cross-family overlap goes to review, not silent deletion

If the same normalized publication appears under more than one dataset family during expansion, that is a review signal.

It is **not** automatically proof that one row must be deleted.

The system should:

- flag the overlap
- preserve evidence
- require review
- prevent silent acceptance into final serving outputs until reviewed

### Rule 5 — human in the loop is required

Patent-family expansion contains domain complexity that cannot be safely reduced to one universal hard gate.

Therefore human review is not a fallback embarrassment.
It is a required control mechanism.

---

## Role of the family-collision incident in this policy

The `71103201` vs `78817222` collision is the concrete example that explains why this policy exists.

That case showed:

- unrestricted full OPS-member attachment is unsafe
- family-definition scope matters
- normalized publication identifiers matter
- dbt tests can reveal institutional blind spots
- a better solution is review-oriented publication dedup, not crude family suppression

So the incident is not separate from this policy.
It is the explanatory case behind it.

---

## Publication-version boundary policy

This project now uses publication kind / version as a **publication-level review boundary**, not as a family-membership deletion boundary.

That means:

- kind / version code supports dedup and review
- kind / version code does not by itself decide whether a family member must be erased from the candidate universe

### Baseline

This project uses:

- **WIPO as the baseline frame**
- office-specific overlays for:
  - `WO`
  - `EP`
  - `US`

### Out of scope for v1/v3 implementation

Other jurisdictions and special local codes are acknowledged but not fully automated here.
Examples include cases such as:

- `DE`
- `CN`
- office-specific kinds such as `T`, `U`, and other local variants

These are not ignored.
They are treated as boundary cases and should be captured as:

- `manual_review_only`
- `out_of_scope_v1`
- `recognized_but_not_auto-deduped`

---

## Tables affected by this policy

### Existing tables in scope

This policy applies to:

- `silver.ops_family_members`
- `gold.bridge_family_ops_cluster`
- `gold.bridge_family_publication`

### Existing tables that should respect the result

- `gold.dim_publication`
- `gold.bm25_document`

### New or revised tables/views recommended under this policy

#### 1. `silver.stg_ops_family_members_canonical`
Purpose:
- normalize OPS-derived publication identifiers before downstream use

#### 2. `gold.dim_publication_kind_rule`
Purpose:
- define publication-version handling rules by authority and kind code
- distinguish exact-dedup cases from review cases

#### 3. `gold.bridge_family_publication_review_queue`
Purpose:
- store suspicious cross-family overlap
- store same-base different-kind collisions
- preserve review evidence instead of silently deleting rows

#### 4. `gold.bridge_family_publication_final`
Purpose:
- final bridge after normalization, exact duplicate dedup, and review decisions

#### 5. `gold.v_publication_serving_candidate`
Purpose:
- expose publication rows that are safe to feed into BM25/search serving under the revised rule set

---

## Relationship to dbt testing

dbt tests are still essential, but their role is now clearer.

dbt does not define patent-family meaning by itself.
What it does do extremely well is:

- expose suspicious overlap
- force hidden assumptions into the open
- prevent unsafe output from becoming silently accepted truth

So under this policy:

- dbt singular tests remain hard visibility controls
- policy defines the review logic
- SQL implements the logic
- review outcomes finalize ambiguous cases

---

## Minimum enforcement rules

At minimum, the system should enforce:

1. normalization checks on publication identifiers
2. uniqueness on exact governed publication identity after dedup
3. family-collision tests that surface unexpected cross-family overlap
4. review-queue insertion for same-base different-kind cases
5. explicit review decisions before ambiguous rows enter final serving outputs

---

## Summary rule

> Expand broadly if needed.
> Normalize before comparison.
> Dedup only exact publication duplicates automatically.
> Route version ambiguity and family overlap into review.
> Let final serving outputs depend on reviewed publication truth, not crude hard gates.
