# Core Guard Routing

Read this file first. Load only catalogs that can change implementation, evidence, or release caution.

## Default

- API, state, idempotency, concurrency, pagination, data integrity, or status codes: read `core-guard-catalog.md`.
- Compatibility catalog owns externally visible contract evolution. Core catalog owns current endpoint behavior.

## Conditional Catalogs

| Trigger | Read |
|---|---|
| Authn/authz, tenant/owner boundary, public field binding/mass assignment, server-owned fields, sensitive data/logging, CORS/TLS, user-controlled URLs, untrusted third-party responses, interpreter inputs | `security-guard-catalog.md` |
| Durable schema/data model, constraints/indexes, migrations/backfills, non-default isolation/locking, replication, retention/audit/restore | `data-lifecycle-guard-catalog.md` |
| Performance goal/claim, high-traffic path, large list/search/export/bulk, DB plan/index/N+1/pool/payload/cache optimization | `performance-guard-catalog.md` |
| External dependencies, retries/timeouts, queues/events, distributed locks, cache consistency, quotas/backpressure/overload | `resilience-guard-catalog.md` |
| Production readiness, observability, SLOs, rollout, rollback, migration rollout, incident readiness, cost/resource risk | `operations-guard-catalog.md` |
| Existing API/schema compatibility, versioning, deprecation, field/type/nullability/enums, documented client semantics, SDKs | `compatibility-governance-guard-catalog.md` |

## Production Evidence

Use production-evidence mode only for explicitly requested environment-specific L4 evidence such as deployed query plans, load, p95/p99, saturation, observability, SLOs, rollout, or rollback.

Real DB integration remains L2. Without an environment-specific L4 request, implement or review L2/L3 guards and name L4 gaps. Do not turn ordinary CRUD work into load testing.

## Evidence Levels

Use the lowest evidence level that proves the relevant guard. Missing runnable evidence downgrades confidence and becomes a finding when a required guard or production-readiness claim depends on it.

| Level | Evidence | Proves |
|---|---|---|
| L0 Static | lint, typecheck, compile, import, test collection | artifact is loadable enough to inspect or test |
| L1 Unit/domain | validation, error mapping, state transition unit tests | isolated local behavior |
| L2 Integration | real DB/repository/API smoke/framework wiring tests | components work together in the target stack |
| L3 Risk-specific | concurrency, idempotency replay, authz bypass, migration compatibility, contract, duplicate event tests | named P1/P2 guard holds under its failure mode |
| L4 Production-readiness | environment-specific load, query plan, canary metric, SLO dashboard, restore drill, rollback rehearsal, failure injection | operational behavior in the designated environment is evidenced, not inferred |
