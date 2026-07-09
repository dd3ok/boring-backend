---
name: boring-backend
description: Use when designing, implementing, or reviewing API/service reliability for auth, data integrity, idempotency, concurrency, performance, distributed behavior, or ops risk.
---

# Boring Backend

Boring Backend means deliberately ordinary service code: protect real invariants with the smallest conventional architecture and evidence strong enough for the claim.

## Mode

- Design: before implementation, define contract, risk, minimal boundaries, guard evidence, and exclusions.
- Implementation: write the narrowest framework-native code that satisfies the contract and verifies high-risk guards.
- Review: find P0/P1/P2 before architecture polish; patch only when fixing is allowed.
- Production evidence: use a production-evidence run only when production readiness, actual DB behavior, p95/p99, query plans, load, saturation, observability, rollout, or rollback is explicitly requested.

## Core Rule

Correct behavior, security, data integrity, status codes, and runnable tests override brevity, SOLID, YAGNI, and style. Use SOLID for real boundaries. Use YAGNI to reject speculative seams.

Operational escalation: performance, cost, migration, observability, or release risk is P1 when it can cause data loss/corruption, security/privacy exposure, availability/SLO breach, unbounded spend, or irreversible rollout. It is P2 when it can cause client-breaking contract drift or status/API compatibility failure.

## Workflow

1. Classify the mode from the user request; do not create a separate design artifact unless requested or risk demands it.
2. Read the request as a contract: behavior, status codes, data rules, security boundary, persistence, external calls, success criteria, and explicit guards.
3. Read `references/core-guard-routing.md` first, then load only the catalogs that match the risk.
4. Resolve P0/P1/P2 before package structure, style, or token cost.
5. Choose the smallest conventional boundaries that own the invariant: route/controller, service/use-case, repository/DAO, DTO/schema, transaction boundary, and error mapping when useful.
6. Map each relevant guard to evidence, a finding, or a named local-only gap. Do not claim production readiness from local smoke tests.
7. Verify with the strongest practical local evidence unless an L4 production-evidence run is requested.

## References

Read only applicable files:

| File | Trigger |
|---|---|
| `references/core-guard-routing.md` | always read first to choose the smallest catalog set |
| `references/guard-catalog.md` | core state, idempotency, concurrency, pagination, data integrity, status codes |
| `references/data-lifecycle-guard-catalog.md` | schema constraints, migrations, backfills, isolation/locking, replication lag, retention/deletion, audit, backup/restore |
| `references/security-guard-catalog.md` | auth, roles, ownership, public input, secrets, logs, CORS/TLS, user-controlled URLs, third-party responses |
| `references/performance-guard-catalog.md` | latency, throughput, high traffic, list/search/export/bulk, DB performance, N+1, indexes, pools, payload, caching |
| `references/resilience-guard-catalog.md` | external calls, retries, timeouts, locks, transactions, queues/events, quotas, throttling, backpressure, distributed/MSA behavior |
| `references/operations-guard-catalog.md` | production readiness, deployment/rollback, migration rollout, observability, SLOs, incident readiness, supply chain, cost/resource risk |
| `references/evidence-strength.md` | evidence level, confidence grading, local-only gaps, production-readiness claims |
| `references/compatibility-governance-guard-catalog.md` | API/schema/SDK compatibility, versioning, deprecation, request/response fields, enums, status codes, pagination/filtering/sorting, idempotency semantics |
| `references/forward-test-prompts.md` | maintaining or evaluating this skill |

## Mode Details

Design output: contract summary, risk calibration, P0/P1/P2 map, minimal architecture, guard plan, assumptions, exclusions, and token telemetry plan when experiments request it.

Implementation output: changed files, guard evidence, commands/results, architecture notes, remaining gaps, and token fields when telemetry exists.

Review output: verdict/confidence, P0-P4 findings or gaps, guard status, commands/results, architecture notes, remaining gaps, and fixes only when allowed.

For token telemetry, split `total_tokens`, `input_tokens`, `cached_input_tokens`, `noncached_input_tokens`, `output_tokens`, and `reasoning_output_tokens`.

## Handoff

When first-attempt experiments or multi-phase runs request reports, write `reports/handoffs/<task>-first-handoff.json` before review. Include contract bullets, guard evidence, known gaps, commands/results, changed files, and token fields when telemetry exists.

Use handoff-first review when that file exists: read it before the full first report, then open only cited files, evidence, and relevant catalogs unless a claim is unclear or contradicted.

## Fix Rules

If review adds a failing test, the work is not complete until the code is fixed and the test is rerun. A RED test left behind is evidence, not success.

Patch the narrowest code path that owns the invariant. Keep unrelated refactors out. Preserve public API unless the contract requires change.

## Experiment Fairness

First-run experiments: do not feed postmortem traps after seeing failures. Guarded clean runs: use the same pre-registered guard list for every variant.

## Skip Conditions

Do not use this skill for pure copy edits, UI-only style changes, trivial local refactors, metadata-only edits, or docs-only work that cannot affect state, auth, API contracts, external calls, persistence, performance, distributed behavior, or operational risk.

