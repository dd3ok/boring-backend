# Core Guard Catalog

Read this file only when the task touches core API/service state, idempotency, concurrency, pagination, data integrity, status codes, or local-only assumptions.

## Implementation Lens

| Risk | Implement |
|---|---|
| Idempotency | Use the narrowest durable mechanism the contract supports: natural operation/business ID, unique constraint, atomic conditional write, or durable idempotency key plus request fingerprint. Reject the same identity with a payload/intent mismatch. Replay only contract-final outcomes, such as success or a specified final business rejection; do not cache transient dependency, timeout, overload, or internal failures by default. Bind replay state atomically to the operation and prove retries or concurrent duplicates cause no double side effect. |
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
- Does the operation use a natural ID, uniqueness, conditional write, or durable key/fingerprint appropriate to its contract?
- Does payload mismatch reject, contract-final replay stay stable, transient failure remain retryable by default, and duplicate input prove no double side effect?
- Are list endpoints bounded?
- Does a normal API flow create data that later breaks delete/update?
- Does the report overstate local-only evidence?
- In pseudo-only reviews, mark build/test evidence unavailable; do not infer P0 unless a runnable artifact was supplied or required.
- Treat unavailable environments, tools, dependency services, or credentials as evidence gaps, not P0; P0 requires a defect in a supplied or required artifact.

## Severity

| Grade | Meaning |
|---|---|
| P0 | A defect in a supplied or required artifact prevents build, run, import, or test collection |
| P1 | Security or data integrity failure |
| P2 | API contract or status-code failure |
| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |
| P4 | Naming, style, verbosity, token cost, or report quality |

Rank P0/P1/P2 ahead of architecture preference. Token cost is a tie-breaker, not correctness evidence.
