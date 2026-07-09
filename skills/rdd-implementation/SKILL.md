---
name: rdd-implementation
description: Use when implementing API/service code with reliability guards for auth, data integrity, idempotency, concurrency, status codes, performance, distributed, or ops risks.
---

# RDD Implementation

RDD means Reliability-Driven Design: implement the smallest conventional solution that satisfies the contract and protects invariants with evidence.

## Core Rule

Correct behavior, security, data integrity, status codes, and runnable tests override brevity, SOLID, YAGNI, and style.

Use SOLID to separate real boundaries. Use YAGNI to reject speculative seams.

## Workflow

1. Read the contract: endpoints, status codes, data rules, security, persistence, tests, and explicit guards.
2. Run a brief design scan: invariant owner, transaction boundary, package/module boundary, and P0/P1/P2 risks.
3. Surface only assumptions that can change P0/P1/P2 outcomes.
4. Choose the smallest framework-native structure: route/controller, service/use-case, repository/DAO, DTO/schema, and error mapping when useful.
5. Implement the narrowest path. Prefer existing patterns, standard library, native DB/framework features, and installed dependencies.
6. Test required behavior and high-risk edges. When any guard catalog applies, turn each relevant P1/P2 guard into a focused test, smoke check, static guard, or explicitly named local-only gap. Missing runnable evidence is a confidence downgrade.
7. Before reporting completion, run relevant verification and map applicable guards to evidence, findings, or named gaps.

## Read References

Read only applicable files:

| File | Trigger |
|---|---|
| `references/guard-catalog.md` | core state, idempotency, concurrency, pagination, data integrity, status codes |
| `references/data-lifecycle-guard-catalog.md` | schema constraints, migrations, backfills, transaction isolation/locking, replication lag, retention/deletion, audit, backup/restore, critical persistent data |
| `references/security-guard-catalog.md` | auth, roles, ownership, public input, secrets, logs, CORS/TLS, user-controlled URLs, third-party responses |
| `references/performance-guard-catalog.md` | latency, throughput, high traffic, list/search/export/bulk, DB performance, N+1, indexes, pools, payload, caching |
| `references/resilience-guard-catalog.md` | external calls, retries, timeouts, locks, transactions, queues/events, quotas, throttling, backpressure, distributed/MSA behavior |
| `references/operations-guard-catalog.md` | production readiness, launch/deployment/rollback, migration rollout, observability, SLOs, incident readiness, supply chain, cost/resource risk |
| `references/evidence-strength.md` | required evidence level, confidence grading, local-only gaps, production-readiness claims |
| `references/compatibility-governance-guard-catalog.md` | API/schema/SDK compatibility, versioning, deprecation, request/response fields, enums, status codes, pagination/filtering/sorting, idempotency semantics |
| `references/forward-test-prompts.md` | maintaining or evaluating this skill |

## Architecture Defaults

| Signal | Do |
|---|---|
| Controller mixes routing, business rules, persistence, and error mapping | Split along framework-native boundaries |
| Interface/factory/strategy/plugin/event layer has one current use | Do not add it |
| DTO/schema leaks persistence, or entity leaks API shape | Separate API and persistence boundaries |
| Rule affects state transition, money, stock, auth, ownership, or concurrency | Put it in a transactional service/use-case |
| Task is non-HTTP/local | Mark API/status/controller fields N/A; do not add an API layer |
| Refactor touches unrelated behavior | Stop and report, do not expand scope |

## Skip Conditions

Do not load guard catalogs for pure functions, UI-only style, typos, docs-only edits, or local refactors that cannot affect state, auth, API contracts, external calls, persistence, performance, or distributed behavior.

Do not claim production readiness from local smoke tests. Name local-only assumptions instead.

## Report Fields

Report verdict/confidence, P0-P4 gaps, guard status, commands/results, architecture notes, remaining gaps, measured tokens only when telemetry exists, skill run, behavior, package structure, and assumptions.

## Experiment Fairness

First-run experiments: no stack-specific postmortem guards unless the same guard list is pre-registered for every variant.
