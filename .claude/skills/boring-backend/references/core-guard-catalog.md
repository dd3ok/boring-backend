# Core Guard Catalog

Read this file only when the task touches core API/service state, idempotency, concurrency, pagination, data integrity, status codes, or local-only assumptions.

## Implementation Lens

| Risk | Implement |
|---|---|
| Idempotency identity and replay | Use the narrowest durable mechanism the contract supports: natural operation/business ID, unique constraint, atomic conditional write, or durable idempotency key plus request fingerprint. Reject identity reuse with a payload/intent mismatch. Persist and replay the terminal contract result, atomically bind the idempotency record to the operation and result, and prove retries or concurrent duplicates cannot duplicate side effects. |
| Uncertain idempotency outcome | Release or expire an idempotency record only after proving no side effect executed and any started transaction rolled back. If an effect may have executed, including an external effect outside a rolled-back transaction, retain a durable pending/unknown state and reconcile before re-execution. Retry an executed effect only when it is independently idempotent under the same idempotency or business-operation identity. |
| Concurrent read-then-write | Use a transaction plus DB lock, unique/exclusion constraint, atomic conditional update, serializable retry, or single shared writer. A process-local lock is only single-instance protection. |
| State transition and dependent side effects | Atomically elect one transition winner. Keep effects in that transaction when they share its store; otherwise the winning transaction persists uniquely identified work that any worker may claim, execute under the same idempotent effect identity, and mark complete durably. Test competing transitions and recovery after a crash between commit and effect completion. |
| Stock/count invariants | Aggregate duplicate line items before checking stock and test duplicate-line totals. Prevent negative counts with a DB-backed strategy where concurrent requests matter. |
| Reservation/booking overlap | Prove same-resource overlap fails under concurrent create. Prefer DB-backed lock/constraint over JVM/process-local lock for scale-out assumptions. |
| Pagination | Paginate list endpoints and validate bounds, or explicitly document exclusion and high-traffic risk. |
| Error mapping | Map validation, authentication, authorization, not-found, conflict, and invalid state transition failures to the contract status codes. |
| Deletes and cascades | Verify normal API-created child records do not break parent delete/update paths. |
| Local-only assumptions | Name single-process, single-DB, in-memory, local cache, or local test assumptions instead of claiming distributed or production safety. |

## Review Lens

Ask for evidence, not intent:

- Is there a runnable test, smoke check, or static check for the invariant?
- Can two simultaneous requests violate the invariant?
- Does concurrency evidence use the target datastore and writer topology, or explicitly name that limitation?
- Does the operation use a natural ID, uniqueness, conditional write, or durable key/fingerprint appropriate to its contract?
- Does payload mismatch reject and replay of the terminal contract result stay stable?
- Does retry require proof that no effect executed, while executed or uncertain effects reconcile durably before re-execution?
- Are list endpoints bounded?
- Does a normal API flow create data that later breaks delete/update?
- Does the report overstate local-only evidence?
