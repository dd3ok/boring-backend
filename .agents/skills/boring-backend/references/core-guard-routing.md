# Core Guard Routing

Read this file first. Load only catalogs that can change implementation, evidence, or release caution.

## Default

- API, state, idempotency, concurrency, pagination, data integrity, or status codes: read `guard-catalog.md`.
- Evidence level, confidence, or production-readiness claims: read `evidence-strength.md`.

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

## Token Reporting

When telemetry exists, separate `total_tokens`, `input_tokens`, `cached_input_tokens`, `noncached_input_tokens`, `output_tokens`, and `reasoning_output_tokens`. Treat cached input as reference loading signal, not new reasoning output.
