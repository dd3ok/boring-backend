---
name: rdd-review
description: Use when reviewing API/service code for P0-P4 reliability gaps in auth, data integrity, idempotency, concurrency, status codes, performance, architecture, or ops risk.
---

# RDD Review

RDD means Reliability-Driven Design: review code with evidence. Find P0/P1/P2 before architecture polish.

In review-only mode, report without editing. In fix mode, patch only necessary code and rerun verification before calling it improved.

## Review Order

1. Re-read the contract: behavior, status codes, data rules, security, tests, and explicit guards.
2. Collect evidence: build/import, typecheck, tests, static guards, and API smoke checks. When a guard catalog applies, map each relevant P1/P2 guard to evidence, a finding, or a named gap.
3. Grade findings before ranking:
   - P0: build/run/import/test collection failure.
   - P1: security or data-integrity failure.
   - P2: API contract or status-code failure.
   - P3: maintainability, package structure, performance risk, or undue complexity.
   - P4: naming, style, verbosity, token cost, or report quality.
4. If review-only, stop at findings and evidence.
5. If fixing is allowed, fix P0/P1/P2 first. Fix P3 only when narrow and risk-reducing. Leave P4 unless requested or essentially free.
6. Rerun relevant verification after each material fix.

## Read References

Read only applicable files:

| File | Trigger |
|---|---|
| `references/guard-catalog.md` | core state, idempotency, concurrency, pagination, data integrity, status codes |
| `references/security-guard-catalog.md` | auth, roles, ownership, public input, secrets, logs, CORS/TLS, user-controlled URLs, third-party responses |
| `references/performance-guard-catalog.md` | latency, throughput, high traffic, list/search/export/bulk, DB performance, N+1, indexes, pools, payload, caching |
| `references/resilience-guard-catalog.md` | external calls, retries, timeouts, locks, transactions, queues/events, quotas, throttling, backpressure, distributed/MSA behavior |
| `references/operations-guard-catalog.md` | production readiness, architecture evaluation, deployment/migration, observability, SLOs, compatibility, backup/restore, supply chain, cost/resource risk |
| `references/forward-test-prompts.md` | maintaining or evaluating this skill |

## Architecture Review

Good splits have current reasons across API, service/use-case, persistence, DTO/schema, and error mapping. Suspicious splits add interface/factory/strategy/plugin/event layers with one implementation. Small code is good only when tested and honest; larger code is good only when it protects invariants or removes coupling.

## Self-Review Fix Rule

If review adds a failing test, the work is not complete until the code is fixed and the test is rerun. A RED test left behind is evidence, not success.

Patch the narrowest code path that owns the invariant. Keep unrelated refactors out. Preserve public API unless the contract requires change.

## Skip Conditions

Do not use this skill for pure style, prose-only, metadata-only, or changes with no state, auth, API, test, architecture, external dependency, persistence, performance, or operational risk.

Do not call static inspection tests. Do not rank architecture above P0/P1/P2.

## Report Shape

Return verdict/confidence, P0-P4 findings/gaps, guard status, commands/results, architecture notes, remaining gaps, and measured tokens only when telemetry exists. Add fixes only when allowed.

## Experiment Fairness

First-run experiments: do not feed postmortem traps after seeing failures. Guarded clean runs: use the same pre-registered guard list for every variant.
