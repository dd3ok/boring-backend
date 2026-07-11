# Operations Guard Catalog

Read this file only when the task touches package/dependency/lockfile or supply-chain risk, or asks for production readiness, launch/deployment/rollback, migration rollout, observability, SLOs, incident readiness, or cost/resource risk.

## Implementation Lens

| Risk | Implement or Report |
|---|---|
| Observability | Add or identify request IDs, structured logs, error counters, latency metrics, and tracing boundaries for cross-service calls. Avoid logging sensitive data. |
| SLO readiness | Name user-visible success, latency, availability, and saturation signals. Local tests are not SLO evidence. |
| Deployment safety | Prefer automated verification, staged rollout/canary, and rollback notes for high-risk API, data, config, or dependency changes. |
| Migration rollout | For schema or data changes, name expand/contract sequencing, mixed-version behavior, backfill ownership, and rollback limits. |
| Package/dependency supply chain | Route package manifests, dependencies, lockfiles, registries/provenance, vulnerabilities/licenses, and build/install policy here. Keep manifests and lockfiles synchronized, follow workspace-local install policy, verify relevant integrity/audit/build evidence, pin compatible versions, minimize additions, and avoid unapproved global installs. |
| Cost/resource risk | Bound external API spend, storage growth, background jobs, high-cardinality metrics, and resource growth that can become an operational bill or capacity incident. |
| Incident readiness | Name runbook gaps for new failure modes when production readiness is requested. |

## Release Readiness Lens

Use this lens only when launch, deployment, migration, rollback, or production-readiness risk is in scope. This is evidence guidance, not a new workflow phase.

- Name rollout mode: canary, staged, feature flag, dark launch, or all-at-once.
- Name rollback path: code rollback, config rollback, data rollback limited, or forward-fix only.
- Identify observability needed before launch: dashboard, alert, request ID, error rate, latency, saturation, and dependency health.
- Define post-deploy validation: smoke, synthetic check, canary metric, error-budget check, or named evidence gap.
- Name runbook gaps for detection, mitigation, owner, and escalation.

## Review Lens

- Can operators correlate one request across logs, metrics, traces, and downstream calls?
- Are user-visible failure signals separated from internal causes?
- Is rollout/rollback safe when code, config, schema, and clients are temporarily mixed?
- Did the implementation add supply-chain or secret-management risk?
- Can a tenant, job, dependency call, metric label, or stored artifact create runaway cost or resource exhaustion?
