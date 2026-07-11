---
name: boring-backend
description: Design, implement, or review API/service reliability changes involving authentication or authorization, data integrity, idempotency, concurrency, external dependencies, migrations, compatibility, performance, or operational risk. Skip UI-only, metadata-only, trivial refactor, and prose-only work that cannot change API/service behavior, contracts, or operational risk.
license: MIT
---

# Boring Backend

Boring Backend means deliberately ordinary service code: protect real invariants with the smallest conventional architecture and evidence strong enough for the claim.

## Modes

- Design: before implementation, return the contract, material risks, minimal boundaries, risk controls, evidence plan, assumptions, and exclusions.
- Implementation: write the narrowest framework-native code that satisfies the contract and verifies controls for high-risk failures; report changed files, commands/results, choices, and gaps.
- Review: report findings first, ordered by impact and grounded in evidence. For partial artifacts, treat unsupplied surrounding components as evidence gaps, not defects, unless the contract requires the artifact itself to be complete or runnable. Review-only work never edits; patch only when the user requests a fix.

## Core Rule

Correctness, security, integrity, status codes, and runnable evidence take precedence over brevity or architecture preferences. Add boundaries only where they own a current invariant or integration; avoid abstractions for hypothetical variants.

## Workflow

1. Classify the mode from the user request. Do not create a separate design file unless the user requests one; keep necessary planning in the response.
2. Read the request as a contract: behavior, status codes, data rules, security boundary, authoritative state and where it is stored, runtime and writer topology, consistency and retry semantics, external calls, success criteria, and required safeguards.
3. For explicitly requested evidence from a named staging or production environment, including live telemetry, read [production evidence](references/production-evidence.md) first. Follow its staged gate: establish the safety envelope, prepare a bounded plan, obtain separate execution approval, then perform invasive action.
4. Route only material risks with the table below. Load a linked catalog only when it can change implementation, evidence, or release caution.
5. Resolve material correctness, security, integrity, and contract risks before package structure or style.
6. Choose the smallest conventional boundary that owns each invariant: route/controller, service/use-case, repository/DAO, DTO/schema, transaction, or error mapping.
7. Map each relevant risk control to evidence, a finding, or a named evidence gap; identify local-only limits when applicable. Do not claim production readiness from local smoke tests.
8. Choose evidence proportionate to the claim: static checks for loadability, unit tests for isolated behavior, integration tests for wiring, risk-specific tests for failure modes, and environment evidence for production claims. Scale detail to task size and risk.

## Risk Routing

| Trigger | Read |
|---|---|
| Mutable API behavior or status contract, state, idempotency, concurrency, pagination, or data integrity | [core guard catalog](references/core-guard-catalog.md) |
| Authentication/authorization, tenant/owner boundary, sensitive-flow abuse, public field binding, sensitive data/logging, CORS/TLS, user-controlled URLs, untrusted responses, or interpreter inputs | [security guard catalog](references/security-guard-catalog.md) |
| Durable schema/model, constraints/indexes, migrations/backfills, isolation/locking, replication, retention/deletion, audit, or restore | [data lifecycle catalog](references/data-lifecycle-guard-catalog.md) |
| Performance claim, high-traffic path, large list/search/export/bulk, query plan/index/N+1/pool/payload, or cache optimization | [performance catalog](references/performance-guard-catalog.md) |
| Downstream services, subprocesses, shared filesystems, or other failure-prone runtime integrations; retries/timeouts, queues/events, distributed locks, cache consistency, quotas, backpressure, or overload | [resilience catalog](references/resilience-guard-catalog.md) |
| Package supply chain, production readiness, observability/SLOs, rollout/rollback, incident readiness, or cost/resource risk | [operations catalog](references/operations-guard-catalog.md) |
| Existing API/schema or published client SDK evolution, versioning/deprecation, field/type/nullability/enum changes, or client semantics | [compatibility catalog](references/compatibility-governance-guard-catalog.md) |

If multiple rows match, load only the catalogs needed to decide the material risk. A negated or excluded topic is not a trigger by itself; load its catalog when the remaining contract still makes the risk material. Core owns current endpoint behavior; compatibility owns evolution of externally visible behavior.

## Fix Rules

When the user requests a behavior fix, add and run a failing-then-passing regression test when feasible. If that is infeasible, use the strongest practical evidence and name the reason and residual gap. Review-only work must not add or modify tests; an observed pre-existing RED test is evidence, not a fix.

Patch the narrowest code path that owns the invariant. Keep unrelated refactors out. Preserve public API unless the contract requires change.
