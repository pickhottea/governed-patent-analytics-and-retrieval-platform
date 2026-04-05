# Performance Follow-up — Post-Unblock Benchmark for `gold.v_publication_version_candidate`

## Status
Open

## Category
Post-incident performance follow-up

## Related incident
See:
- `docs/incidents/2026-04-05-publication-version-lock-blocking.md`

This note is about post-unblock runtime behavior, not the original blocking incident itself.

## Date
2026-04-05

## Scope
Benchmark the runtime of publication-version objects after the blocking session was cleared.

Objects benchmarked:
- `gold.dim_publication_kind_rule`
- `gold.publication_version_review_queue`
- `gold.v_publication_version_candidate`

## Benchmark method
The benchmark was run with:
- `SET STATISTICS IO ON`
- `SET STATISTICS TIME ON`
- `SET LOCK_TIMEOUT 5000`

Benchmark SQL files:
- `sql/diagnostics/publication_kind_rule_benchmark.sql`
- `sql/diagnostics/publication_version_review_queue_benchmark.sql`
- `sql/diagnostics/publication_version_candidate_benchmark.sql`

## Observed counts
- `gold.dim_publication_kind_rule` → `0`
- `gold.publication_version_review_queue` → `396`
- `gold.v_publication_version_candidate` → `806`

## Benchmark summary
### 1. `gold.dim_publication_kind_rule`
- count returned immediately
- effectively negligible runtime / reads

### 2. `gold.publication_version_review_queue`
- count returned quickly
- low read volume
- observed count `396` matches the current queue-load checkpoints:
  - `same_base_different_kind = 77`
  - `authority_out_of_scope_v1 = 319`

### 3. `gold.v_publication_version_candidate`
- count returned `806`
- materially slower than the other two benchmarked objects
- observed runtime was approximately:
  - CPU ≈ `83s`
  - elapsed ≈ `83s`

## Main performance signal
The candidate view is not just slightly slower.
It is materially heavier than the other two publication-version objects in post-unblock runtime.

The benchmark output showed especially heavy reads on:
- `ops_family_members`
- `patents_canonical_raw`

It also showed large LOB logical reads on the candidate-view execution path.

## Refined interpretation after inspecting view definition
Inspection of `gold.v_publication_version_candidate` shows that the view itself is relatively thin.

Its logic mainly:
- reads `publication_number` from `dbo.dim_publication`
- normalizes the string
- derives:
  - `authority_code`
  - `kind_code`
  - `base_number`
  - `kind_prefix`

So the current evidence suggests that the main cost is not the candidate view’s parsing logic itself, but the upstream cost inherited from the current `dbo.dim_publication` view path.

## Important correctness note
`gold.dim_publication_kind_rule = 0` is likely not just a performance observation.

The publication-version slice handover states that V1 seed rules should exist for:
- `WO`
- `EP`
- `US`

So the zero-row result should be treated as a separate correctness / seeding follow-up.

## Why this matters
This publication-version slice now has at least three distinct follow-ups:
1. resolved blocking incident
2. remaining upstream publication-view performance cost exposed by candidate counting
3. separate rule-table seeding correctness check

These should stay separated in repo narrative and debugging workflow.

## Follow-up actions
1. inspect the SQL definition of `dbo.dim_publication`
2. identify which upstream joins / transforms drive the heavy reads
3. evaluate whether publication-version candidates should be materialized from a lighter source instead of inheriting the full current publication view path
4. separately verify why `gold.dim_publication_kind_rule` currently returns `0`
5. keep post-unblock benchmark logs as baseline evidence

## Evidence files
- `logs/performance/2026-04-05_publication_kind_rule_benchmark.out`
- `logs/performance/2026-04-05_publication_version_review_queue_benchmark.out`
- `logs/performance/2026-04-05_publication_version_candidate_benchmark.out`

## Post-materialization result

The post-materialization benchmark was re-run against the candidate-equivalent projection on `gold.dim_publication` after normalized / parsed publication fields were persisted directly in gold.

Observed outcome:
- query returned effectively immediately in interactive execution
- prior long-running behavior was no longer reproduced on the working publication-version path

Interpretation:
- this strongly supports the earlier hypothesis that the main latency cost was dominated by the old upstream `dbo.dim_publication` view path
- the parsing logic itself was not the primary bottleneck
- materializing parsed publication fields into `gold.dim_publication` resolved the main candidate-path performance issue

Important note:
- `gold.dim_publication_kind_rule` still remained empty during this validation pass
- that is a separate correctness / seeding issue, not evidence against the performance improvement