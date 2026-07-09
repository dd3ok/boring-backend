---
name: rdd-design
description: Use when designing API/service reliability contracts before implementation for auth, data integrity, concurrency, status codes, performance, microservices, distributed, or ops-risk decisions.
---

# RDD Design

RDD means Reliability-Driven Design: decide the reliability contract before code. Keep the design short, explicit, and testable. Do not turn design into speculative architecture.

## Core Rule

Design only what the current task needs to protect real invariants. A design is useful when it changes implementation choices, test cases, or risk visibility.

## Workflow

1. Read the request as a contract: actors, API behavior, status codes, data rules, security boundaries, persistence, external calls, and success criteria.
2. Identify P0/P1/P2 risks before package structure: build/run blockers, security or data-integrity failures, and API/status-contract failures.
3. Name the smallest conventional architecture that owns the invariants: route/controller, service/use-case, repository/DAO, DTO/schema, transaction boundary, and error mapping when useful.
4. Choose guard evidence for each relevant risk: unit test, integration test, concurrency test, static guard, smoke check, benchmark/load evidence, or named local-only gap.
5. State tradeoffs and assumptions that can change P0/P1/P2 outcomes. Omit generic best-practice prose.
6. Hand off to implementation with concrete acceptance criteria.

## Concurrency Strategy Choice

Before strategy choice, define boundary semantics: half-open `[start, end)` ranges and invalid-transition status.

| Signal | Prefer |
|---|---|
| DB can express the invariant | Native constraint; map violation to conflict |
| One aggregate row owns it | Transaction plus row lock, or atomic conditional update |
| Low contention with version field | Optimistic version plus bounded retry or conflict |
| Cross-row/range without native constraint | Serializable plus bounded retry; name DB limits |
| In-memory or process lock | Local-only; no distributed safety claim |

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

## Design Output

When a design artifact is requested, return:

- Contract summary: behavior, status codes, data rules, and security boundary.
- Risk map: P0/P1/P2 risks first, then P3/P4 if relevant.
- Minimal architecture: current package/module boundaries and why each exists.
- Guard plan: tests/checks/evidence required for each relevant guard.
- Assumptions and exclusions: local-only or deferred risks without overclaiming production readiness.

## Skip Conditions

Do not use this skill for pure copy edits, UI-only style changes, trivial local refactors, or documentation-only work that cannot affect state, auth, API contracts, external calls, persistence, performance, distributed behavior, or operational risk.

Do not require a separate design document when implementation can safely include a short contract and risk scan.
