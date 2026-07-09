# Core Guard Routing

Read this file first. Load only catalogs that can change implementation, evidence, or release caution.

## Default

- API, state, idempotency, concurrency, pagination, data integrity, or status codes: read `core-guard-catalog.md`.
- Compatibility catalog owns externally visible contract evolution. Core catalog owns current endpoint behavior.

## Conditional Catalogs

| Trigger | Read |
|---|---|
| Auth, roles, ownership, public input, secrets, logs, CORS/TLS, user-controlled URLs | `security-guard-catalog.md` |
| Schema constraints, migrations, backfills, transaction isolation, replication lag, retention, audit, backup/restore | `data-lifecycle-guard-catalog.md` |
| Latency, throughput, high traffic, list/search/export/bulk, DB performance, N+1, indexes, pools, payload, caching | `performance-guard-catalog.md` |
| External calls, retries, timeouts, locks, transactions, queues/events, quotas, backpressure, distributed/MSA behavior | `resilience-guard-catalog.md` |
| Production readiness, observability, SLOs, rollout, rollback, migration rollout, incident readiness, cost/resource risk | `operations-guard-catalog.md` |
| API/schema compatibility, versioning, deprecation, response fields, enums, pagination/filtering/sorting semantics | `compatibility-governance-guard-catalog.md` |

## Production Evidence

Use a production-evidence run only for explicit production-ready, actual DB, query plan, load test, p95/p99, saturation, observability, SLO, rollout, or rollback requests.

Without that trigger, implement or review L2/L3 guards and name L4 gaps. Do not turn ordinary CRUD work into load testing.

## Evidence Levels

Use the lowest evidence level that proves the relevant guard. Missing runnable evidence downgrades confidence and becomes a finding when a required guard or production-readiness claim depends on it.

| Level | Evidence | Proves |
|---|---|---|
| L0 Static | lint, typecheck, compile, import, test collection | artifact is loadable enough to inspect or test |
| L1 Unit/domain | validation, error mapping, state transition unit tests | isolated local behavior |
| L2 Integration | real DB/repository/API smoke/framework wiring tests | components work together in the target stack |
| L3 Risk-specific | concurrency, idempotency replay, authz bypass, migration compatibility, contract, duplicate event tests | named P1/P2 guard holds under its failure mode |
| L4 Production-readiness | load test, query plan, canary metric, SLO dashboard, restore drill, rollback rehearsal, failure injection | operational behavior is evidenced, not inferred |

## Token Reporting

When telemetry exists, separate `total_tokens`, `input_tokens`, `cached_input_tokens`, `noncached_input_tokens`, `output_tokens`, and `reasoning_output_tokens`. Treat cached input as reference loading signal, not new reasoning output.
