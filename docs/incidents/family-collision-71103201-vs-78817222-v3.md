# Family Collision Incident Case Study — `71103201` vs `78817222`

## Project

`governed-patent-analytics-and-retrieval-platform`

## Why this case matters

This incident is valuable because the system did **not** fail silently.

A dbt singular test (`test_family_collision`) forced the project to look beyond row counts, null checks, and surface-level reconciliation. It exposed a design blind spot in family expansion logic that normal QA would likely miss.

In other words:

> dbt testing did not merely validate the warehouse.
> It challenged an implicit modeling assumption.

That is the core value of this case.

---

## Incident title

**Unexpected family collision in `bridge_family_publication` surfaced by dbt singular test**

---

## Short version

A dbt singular test failed because the same `publication_number` was attached to more than one `family_id`.

The collision pair was:

- `family_id = 71103201`
- `family_id = 78817222`

At first this could have been dismissed as a simple reconciliation issue.
It was not.

Deeper inspection showed that two dataset families expanded into publication sets that overlapped heavily enough to break the governed warehouse bridge.

This incident revealed that the project had a real blind spot:

- primary keys were stable
- joins were executable
- expansion technically "worked"
- but the **meaning** of family identity during expansion had not been bounded carefully enough

---

## What the dbt test actually revealed

The failing test was not just saying "there is a duplicate."

It revealed a much more important point:

> a dataset family can remain internally keyed, but still expand into a publication universe that conflicts with another dataset family

This means the problem was not simply missing PKs or bad SQL syntax.
The system had keys.
The system had tables.
The system had joins.

What it did **not** have was a safe enough rule for how family expansion should behave when different family definitions or family scopes produce overlapping publication universes.

That is why this case matters.

---

## Where family-definition complexity enters

This incident also surfaced an important modeling reality:

### Narrow family view

A narrower family interpretation (for example, simple-family style reasoning) expects tighter family boundaries and fewer acceptable overlaps.

### Broad family view

A broader family interpretation (for example, extended-family style reasoning) can produce a larger candidate publication universe because members may be connected through direct or indirect priority links.

### Why this matters here

Even when `family_id` is the canonical warehouse key, expansion can still become unstable if:

- the dataset family is treated narrowly
- OPS family expansion behaves more broadly
- the bridge attaches all expanded members without a second-stage publication-level review policy

So the collision was not only about duplicates.
It was also about **family-definition scope leaking into bridge expansion**.

---

## What failed

### Test

`dbt test --select bridge_family_publication`

### Failing singular test

`tests/test_family_collision.sql`

### Intended business rule

Fail if the same governed `publication_number` appears under more than one governed `family_id` unexpectedly.

This was the right test.

A row-count test would not have been enough.
A null test would not have been enough.
A generic uniqueness test would only have shown a symptom.

This singular test forced the project to investigate the warehouse logic itself.

---

## Observed collision pair

The overlapping publication set included examples such as:

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

That should not happen casually inside the governed bridge.

---

## What the investigation showed

The investigation showed three separate facts:

1. The two dataset families did **not** collapse into one identical OPS key by a trivial misjoin.
2. The silver OPS expansion layer contained publication sets that were nearly identical across the two family paths.
3. The bridge then attached the full expansion result without enough publication-level discrimination.

This means the incident should be understood as:

> family expansion logic was too permissive for a governed bridge

not merely:

> one bad join broke everything

---

## Secondary issue uncovered during the incident

The investigation also found that publication identifiers in `silver.ops_family_members` were not always fully normalized.

Examples included partially parsed fragments such as:

- `{'$':'EP'}{'$':'3919806'}{'$':'A1'}`
- `{'$':'US'}{'$':'11326744'}{'$':'B2'}`

This was important, but it was **not** the primary cause of the collision.

Normalization problems created diagnostic noise and made review harder.
They did not fully explain why two families expanded into overlapping publication universes.

---

## Why dbt deserves explicit credit here

This case is a strong example of why dbt tests matter in governed systems.

The test did not simply confirm expected output.
It helped the project think outside the obvious path.

It exposed that:

- keys can exist while meaning is still unstable
- expansion can be technically correct but governably unsafe
- publication-level overlap can reveal a family-expansion modeling problem

In short:

> the test found the blind spot before the blind spot became accepted truth

That is exactly what a good governed test suite should do.

---

## Revised lesson from the incident

The lesson is **not**:

- "hard-gate everything"

The better lesson is:

- use dbt tests to surface suspicious overlap
- keep exact duplicate removal automatic
- send ambiguous version / cross-family overlap cases into human review
- separate family-definition complexity from publication-level dedup logic

So the incident did not justify a crude universal hard gate.
It justified a more mature review-oriented expansion policy.

---

## Remediation direction supported by this incident

This incident now supports the following direction:

1. **Keep the collision test** as a hard fail.
2. **Normalize publication identifiers** before bridge use.
3. **Do exact duplicate dedup only** at the publication level.
4. **Do not auto-delete all cross-family overlap.**
5. **Route ambiguous overlaps and version differences into human review.**
6. **Treat broad family expansion as candidate pool, not final truth.**

---

## Conclusion

This case is worth keeping in the repo because it proves something important:

> the warehouse was able to detect a modeling blind spot in family expansion before that blind spot hardened into platform truth

That is not an embarrassment.
That is exactly what governed testing is for.
