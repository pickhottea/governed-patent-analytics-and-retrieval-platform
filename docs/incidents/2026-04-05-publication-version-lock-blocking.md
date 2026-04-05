# Incident — Schema Lock Blocking on Publication Version Queries

## Status
Confirmed

## Category
Locking / blocking incident

## First observed
2026-04-05

## Symptom
Publication-version queries remained running for nearly one hour without returning.

The issue was initially observed in a VS Code SQL query tab and later reproduced indirectly when a separate `sqlcmd` diagnostic session also became suspended.

## Affected objects
- `gold.dim_publication_kind_rule`
- `gold.publication_version_review_queue`
- `gold.v_publication_version_candidate`

## Related slice
Publication version review framework.

## Exact SQL initially observed
```sql
select count(*) as cnt from gold.dim_publication_kind_rule;
select count(*) as cnt from gold.publication_version_review_queue;
select count(*) as cnt from gold.v_publication_version_candidate;

select *
from gold.dim_publication_kind_rule
order by authority_code, kind_code;

select
    review_reason,
    count(*) as cnt
from gold.publication_version_review_queue
group by review_reason
order by cnt desc;
```

## Confirmed evidence

### Session snapshot

- `session_id = 52`
    - client: `SQLCMD`
    - request status: `suspended`
    - command: `SELECT`
- `session_id = 61`
    - client: `vscode-mssql-Query`
    - session status: `sleeping`
    - `open_transaction_count = 1`
- `session_id = 63`
    - client: `vscode-mssql-GeneralConnection`
    - session status: `sleeping`
    - `open_transaction_count = 0`

### Lock evidence

`session_id = 61` held:

- `OBJECT Sch-M` lock
- multiple `X` locks (`EXTENT`, `KEY`, `PAGE`)
- additional metadata locks

This confirmed that the issue was not merely a slow query or UI-only client problem.

`logs/performance/2026-04-05_publication_version_candidate_benchmark.out`

Post-unblock benchmark showed that gold.v_publication_version_candidate remained slower than the other two publication-version objects, suggesting a separate follow-up performance issue after the blocking incident was resolved.


### Confirmed root cause

A stale VS Code query session (`session_id = 61`, `program_name = vscode-mssql-Query`) held an open transaction (`open_transaction_count = 1`) and an `OBJECT Sch-M` lock, along with multiple `X` locks.

This blocked later publication-version reads and caused downstream sessions, including `sqlcmd` diagnostic session `52`, to remain suspended.

`session_id = 63` (`vscode-mssql-GeneralConnection`) was not the blocker; it had `open_transaction_count = 0`.

The most recent SQL captured for blocker session `61` pointed to `sql/gold/load_publication_version_review_queue.sql`.

## Why this matters

This was initially framed as a slow-query / long-response-time problem, but the actual failure mode was concurrency-related blocking.

That distinction matters because the appropriate remediation is not only query tuning, but also:

- transaction hygiene
- explicit session cleanup
- safer diagnostics
- avoiding multi-statement debugging batches in VS Code

## Immediate remediation

- cancel the original VS Code batch query
- identify and terminate stale blocker session if needed
- re-run minimal single-statement checks with lock timeout
- avoid sending multiple statements in one debug batch

## Guardrails to add

- use `SET LOCK_TIMEOUT` during interactive diagnostics
- run one statement at a time during SQL debugging
- record blocker session / lock evidence before retrying
- consider a small blocking diagnostic script under `sql/diagnostics/`
- add governance dashboard visibility for long-running SQL / blocking events

## Evidence files

- `logs/performance/2026-04-05_publication_version_query_symptom.log`
- `logs/performance/2026-04-05_publication_version_safe_snapshot.out`

## Notes

This incident belongs to the publication-version review slice and should be documented separately from identity-contract incidents such as family collision.

```

