# Core Guard Catalog

Read this file only when the task touches core API/service state, idempotency, concurrency, pagination, data integrity, status codes, local-only assumptions, or an AI coding-agent guarded-run comparison.

## Implementation Lens

| Risk | Implement |
|---|---|
| Idempotency | Store a durable idempotency key and request fingerprint. Same key + same payload replays the prior result, including handled failure or invalid-transition responses unless the contract explicitly excludes them. Same key + different payload returns conflict. Side effects must not double-apply. Test success replay, payload mismatch conflict, and failure replay for state-changing operations. |
| Concurrent read-then-write | Use a transaction plus DB lock, unique/exclusion constraint, atomic conditional update, serializable retry, or single shared writer. A process-local lock is only single-instance protection. |
| Stock/count invariants | Aggregate duplicate line items before checking stock and test duplicate-line totals. Prevent negative counts with a DB-backed strategy where concurrent requests matter. |
| Reservation/booking overlap | Prove same-resource overlap fails under concurrent create. Prefer DB-backed lock/constraint over JVM/process-local lock for scale-out assumptions. |
| Pagination | Paginate list endpoints and validate bounds, or explicitly document exclusion and high-traffic risk. |
| Error mapping | Map validation, authentication, authorization, not-found, conflict, and invalid state transition failures to the contract status codes. |
| Deletes and cascades | Verify normal API-created child records do not break parent delete/update paths. |
| Local-only assumptions | Name single-process, single-DB, in-memory, local cache, or local test assumptions instead of claiming distributed or production safety. |

## Review Lens

Ask for evidence, not intent:

- Is there a runnable test, smoke check, or static guard for the invariant?
- Can two simultaneous requests violate the invariant?
- Does repeated input replay safely, or does it reapply side effects?
- Do handled failures or invalid state transitions replay for the same idempotency key, or can retries observe a different result?
- Are list endpoints bounded?
- Does a normal API flow create data that later breaks delete/update?
- Does the report overstate local-only evidence?
- In pseudo-only reviews, mark build/test evidence unavailable; do not infer P0 unless a runnable artifact was supplied or required.

## Severity

| Grade | Meaning |
|---|---|
| P0 | Cannot build, run, import, or collect tests |
| P1 | Security or data integrity failure |
| P2 | API contract or status-code failure |
| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |
| P4 | Naming, style, verbosity, token cost, or report quality |

Rank P0/P1/P2 ahead of architecture preference. Token cost is a tie-breaker, not correctness evidence.
