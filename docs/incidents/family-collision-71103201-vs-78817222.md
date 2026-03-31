# Project

`governed-patent-analytics-and-retrieval-platform`

## Why this case is portfolio-worthy

This is a strong **data contract violation + governed incident analysis** example.

It shows that the project does not only build warehouse tables and retrieval features, but also:

- defines explicit family / publication identity contracts
- enforces those contracts with dbt tests
- catches a real family-expansion defect in the warehouse bridge
- preserves reproducible SQL evidence across silver and gold layers
- turns a failing test into an architectural correction, not just a patch

That is exactly the kind of material that raises the repo quality beyond “it runs” into “it is engineered, testable, and auditable.”

---

## Incident title

**Unexpected family collision in `gold.bridge_family_publication` detected by dbt singular test**

---

## Short version

A dbt singular test (`test_family_collision`) failed because the same `publication_number` was mapped to more than one `family_id`.

The failing pair was:

- `family_id = 71103201`
- `family_id = 78817222`

At first this looked like it might be related to known reconciliation nuances in the project, such as the distinction between family-level landscape truth and publication-grain search serving.

However, deeper SQL inspection showed that this was **not** a harmless reconciliation artifact.

The actual problem was that two different dataset families independently mapped to two different OPS families whose member publication sets were nearly identical. The warehouse bridge then attached the **full OPS member set** to each dataset family without enforcing any dataset-family boundary rule.

As a result, the same AU / CA / EP / JP / MX / US publications were attached to both families inside `gold.bridge_family_publication`.

This was therefore treated as a **real family-expansion defect**, not a reporting exception.

---

## What failed

### Test

`dbt test --select bridge_family_publication`

### Failing singular test

`tests/test_family_collision.sql`

### Intended rule

Fail if any `publication_number` maps to more than one `family_id` unexpectedly.

This is a family-identity contract test.

---

## Failure signal

The dbt test run passed almost everything, but `test_family_collision` failed.

### Example status summary

- dbt parse: passed
- dbt tests: 29 total
- pass: 28
- fail: 1
- failing test: `test_family_collision`

This matters because it shows that most warehouse contracts were stable, while one specific identity rule was violated in a way that directly affects trust and traceability.

---

## Observed collision pair

The collision output showed the same publication members attached to both:

- `71103201`
- `78817222`

Example overlapping publications observed in `gold.bridge_family_publication` included:

- `AU2020207798A1`
- `AU2020207798B2`
- `CA3089880A1`
- `EP3919806A1`
- `JP2021190413A`
- `JP7080937B2`
- `MX2020008652A`
- `US11326744B2`
- `US11920738B2`
- `US2021381658A1`
- `US2023341094A1`

Under the project’s governed warehouse contract, this should not happen if `family_id` is the canonical family key.

---

## Why this mattered

This project intentionally distinguishes two valid truths:

- **landscape family truth**
- **publication-grain search serving truth**

That distinction is acceptable.

But this failure was not merely a harmless “150 families vs 149 searchable publications” nuance.

It was a stronger defect:

> two different dataset families were expanded into overlapping publication universes inside the warehouse bridge.
> 

That breaks traceability and can distort:

- family-level landscape reporting
- publication reconciliation logic
- BM25 feed preparation
- governance dashboards
- reviewer trust
- downstream search explanation

---

## Evidence chain

This case is strong because the defect was reproducible across multiple layers.

### 1. dbt failure

The singular collision test failed and surfaced the publication-to-multi-family mapping.

### 2. Gold-layer SQL inspection

A follow-up query against `gold.bridge_family_publication` showed that the same `publication_number` values were attached to both `71103201` and `78817222`.

### 3. `bridge_family_ops_cluster` check

A direct inspection of `gold.bridge_family_ops_cluster` showed that the two dataset families did **not** collapse to the same OPS family key.

Instead:

- `71103201 -> 71103201`
- `78817222 -> 78817222`

This ruled out the simpler hypothesis that both dataset families were incorrectly mapped to one shared OPS family.

### 4. Silver-layer member inspection

A direct query against `silver.ops_family_members` showed that:

- `ops_family_id = 71103201`
- `ops_family_id = 78817222`

each had member publication sets that were nearly identical.

This was the key finding.

The issue was **not** that one OPS family was wrongly reused as another.

The issue was that two different OPS-family expansions produced almost the same publication universe, and the warehouse bridge attached both full member sets without further boundary control.

### 5. Publication identifier quality check

The same silver query also showed that `member_publication_number` and `member_publication_docdb` were stored as partially parsed string fragments such as:

- `{'$':'EP'}{'$':'3919806'}{'$':'A1'}`
- `{'$':'US'}{'$':'11326744'}{'$':'B2'}`

This is a real data quality issue and should be corrected.

However, it was **not** the primary cause of the collision. Even if the identifiers were perfectly normalized, the overlap would still occur, because the bridge currently attaches the full OPS-family member universe with no dataset-level boundary restriction.

### 6. Architectural inspection of bridge logic

The current build logic for `gold.bridge_family_publication` confirmed the problem.

Expanded members are attached through:

```
FROM gold.bridge_family_ops_cluster bfo
INNERJOIN silver.ops_family_members ofm
ON bfo.ops_family_cluster_id= ofm.ops_family_id
```

and then projected as:

```
COALESCE(ofm.member_publication_number, ofm.member_publication_docdb)AS publication_number
```

This means that once a dataset family is linked to an OPS family, the bridge attaches **all** publications from that OPS family.

There is no second-stage rule that constrains which OPS members are actually acceptable for the governed dataset family.

That is the actual defect.

---

## Root cause

The root cause was **uncontrolled OPS-family expansion**, not a simple cluster-key misjoin.

In plain language:

- dataset family identity and OPS-family expansion were treated as if they were equivalent enough to share the same full publication universe
- the bridge path attached all OPS members once a dataset family was linked to an OPS family
- no dataset-family boundary rule filtered that expanded publication set
- because `71103201` and `78817222` each mapped to OPS families with nearly identical members, the same publications were attached to both dataset families

So the defect is best understood as:

> **full expansion without governed boundary control**
> 

not merely:

> “wrong cluster mapping”
> 

---

## Architectural lesson

The incident reinforced a core rule:

> **Do not treat OPS family expansion as canonical dataset family identity.**
> 

OPS-family expansion may be useful as a candidate universe, but it must remain subordinate to the warehouse’s governed family definition.

A dataset family can link to an OPS family for expansion support, but the final attached publication set must still be constrained by explicit project-level family rules.

---

## Secondary data-quality issue

The investigation also surfaced a separate but important quality problem:

- `silver.ops_family_members.member_publication_number`
- `silver.ops_family_members.member_publication_docdb`

were not fully normalized and still contained partially parsed string fragments.

This should be fixed because it weakens:

- publication-key stability
- deduplication quality
- readability of diagnostics
- downstream join reliability

But this was a **secondary issue**, not the main cause of the family collision.

---

## Why the test was valuable

This is an excellent example of why singular tests matter.

A row-count test would not have explained the issue.

A null test would not have caught it.

A uniqueness test on `(family_id, publication_number)` alone would only expose a local symptom.

The singular collision test expressed the actual contract:

> a publication should not unexpectedly belong to more than one dataset family inside the governed warehouse bridge.
> 

That made the defect visible immediately.

---

## Suggested remediation direction

### Immediate

- keep `test_family_collision` as a hard fail
- do not downgrade this case to a harmless exception
- preserve `71103201` vs `78817222` as a named incident pair

### Near term

- revise `gold.bridge_family_publication` so OPS-family expansion is treated as a **candidate publication pool**, not an automatic full attachment
- add a second-stage boundary rule that limits which expanded publications are allowed to belong to a dataset family
- separately normalize `member_publication_number` and `member_publication_docdb` in `silver.ops_family_members`

### After fix

- rerun dbt tests
- confirm `test_family_collision` passes
- document the corrected expansion rule and why it is required