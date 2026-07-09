# Operations Guard Catalog

Read this file only when the task asks for production readiness, architecture evaluation, deployment/migration risk, observability, SLOs, API compatibility, backup/restore, supply chain, or cost/resource risk.

## Implementation Lens

| Risk | Implement or Report |
|---|---|
| Observability | Add or identify request IDs, structured logs, error counters, latency metrics, and tracing boundaries for cross-service calls. Avoid logging sensitive data. |
| SLO readiness | Name user-visible success, latency, availability, and saturation signals. Local tests are not SLO evidence. |
| Deployment safety | Prefer automated verification, staged rollout/canary, and rollback notes for high-risk API, data, config, or dependency changes. |
| Migration safety | For schema changes, prefer expand/contract, backward-compatible reads/writes, data backfill plan, and rollback limits. |
| API compatibility | Treat APIs as contracts. Avoid removing fields, changing field meaning, changing status codes, or making optional input required without versioning/migration notes. |
| Contract drift | Keep OpenAPI/contract docs, tests, and implementation aligned. If no contract exists, state that compatibility confidence is limited. |
| Backup and restore | For persistent critical data, name backup/restore assumptions, RPO/RTO expectations, and whether restore has been tested. |
| Supply chain | Follow workspace install policy. Prefer lockfiles, pinned major versions, vulnerability/dependency checks, secret scans, and minimal new dependencies. Avoid global installs unless explicitly approved and allowed by the workspace. |
| Cost/resource risk | Bound external API spend, storage growth, background jobs, high-cardinality metrics, and resource growth that can become an operational bill or capacity incident. |
| Incident readiness | Name runbook gaps for new failure modes when production readiness is requested. |

## Review Lens

- Can operators correlate one request across logs, metrics, traces, and downstream calls?
- Are user-visible failure signals separated from internal causes?
- Is rollout/rollback safe when code, config, schema, and clients are temporarily mixed?
- Could this change break older clients or undocumented consumers?
- Is data recoverable, and has restore been proven rather than assumed?
- Did the implementation add supply-chain or secret-management risk?
- Can a tenant, job, dependency call, metric label, or stored artifact create runaway cost or resource exhaustion?

