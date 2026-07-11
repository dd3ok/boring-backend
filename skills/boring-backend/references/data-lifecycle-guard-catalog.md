# Data Lifecycle Guard Catalog

Read this file only when the task touches schema design, constraints, migrations, backfills, transaction isolation, locking, replication, retention, deletion, auditing, backup/restore, partitioning, hot keys, or critical persistent data.

## Implementation Lens

| Risk | Implement or Report |
|---|---|
| Data model invariant | Prefer database constraints, unique indexes, exclusion constraints, foreign keys, and check constraints for durable invariants. Application validation alone is a local-only control when concurrent or external writers exist. |
| Constraint and index ownership | Name which layer owns each invariant and which index supports the constraint or query path. Include referencing-column indexes when foreign-key deletes/updates or joins can become hot. |
| Transaction isolation | State whether read committed is enough. Use row locks, optimistic versions, repeatable read/serializable with safe retry, or atomic conditional updates when stale reads can corrupt state. |
| Locking and deadlocks | Keep transactions short, acquire locks in a consistent order, avoid network/user waits inside transactions, and define timeout/retry behavior for deadlocks or serialization failures. |
| Online migration | Prefer expand/contract, backward-compatible reads/writes, mixed old/new binary safety, migration smoke checks, and explicit rollback or forward-fix limits. |
| Backfill | Make backfills chunked, resumable by stable key, idempotent, rate-limited, observable, and safe under partial failure or rerun. |
| Replication lag | Define read-after-write requirements, primary/replica routing, stale-read tolerance, and cache invalidation assumptions. |
| Retention and deletion | Specify soft delete, hard delete, cascade behavior, legal hold, privacy deletion, and restoration expectations. Avoid accidental cascades across tenant or audit boundaries. |
| Audit trail | For regulated, financial, admin, or destructive changes, capture who changed what, when, why, and the before/after state or stable reference. |
| Partitioning and hot keys | Check tenant/time skew, monotonically increasing keys, partition pruning, index bloat, and shard/partition assumptions for high-volume data. |
| Backup and restore | Name RPO/RTO, point-in-time recovery assumptions, restore drill evidence, and what local-only tests do not prove. |

## Review Lens

- Is the invariant protected in the database when multiple writers or direct data access can exist?
- Can old and new code run safely while schema, data, and clients are mixed?
- Can the backfill stop, resume, rerun, and report partial failures without corrupting data?
- Are isolation level, lock order, retry policy, and transaction scope explicit for conflicting writes?
- Are retention, deletion, cascade, audit, and restore expectations stated and tested where critical?
- Does the report overclaim production database safety from local or single-process evidence?
