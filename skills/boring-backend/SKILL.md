---
name: boring-backend
description: Use when API/service work involves auth, integrity, idempotency, concurrency, dependencies, migrations, compatibility, performance, or ops risk; not for UI or non-contract docs edits.
license: MIT
---

# Boring Backend

Boring Backend means deliberately ordinary service code: protect real invariants with the smallest conventional architecture and evidence strong enough for the claim.

## Modes

- Design: before implementation, define contract, risk, minimal boundaries, guard evidence, and exclusions.
- Implementation: write the narrowest framework-native code that satisfies the contract and verifies high-risk guards.
- Review: find P0/P1/P2 before architecture polish. Review-only work never edits; patch only in an authorized fix run.

## Core Rule

Correctness, security, integrity, status codes, and runnable evidence override brevity, SOLID, YAGNI, and style. Use SOLID for real boundaries and YAGNI against speculative seams.

## Workflow

1. Classify the mode from the user request; do not create a separate design artifact unless requested or risk demands it.
2. Read the request as a contract: behavior, status codes, data rules, security boundary, persistence, external calls, success criteria, and explicit guards.
3. For explicitly requested environment-specific L4 evidence, read `references/production-evidence.md` first. If its permission gate is incomplete, stop without loading catalogs or running actions.
4. Read `references/core-guard-routing.md`, then load only the catalogs that match the remaining risk.
5. Resolve material correctness, security, integrity, and contract risks before package structure or style. Before any P0-P4 label appears in output, read `references/severity.md`; otherwise do not load it.
6. Choose the smallest conventional boundary that owns each invariant: route/controller, service/use-case, repository/DAO, DTO/schema, transaction, or error mapping.
7. Map each relevant guard to evidence, a finding, or a named local-only gap. Do not claim production readiness from local smoke tests.
8. Verify with the strongest practical evidence. Scale output and evidence detail to task size and risk; explain only non-obvious catalog choices.

Catalog targets; load only when routed: `references/core-guard-catalog.md`, `references/security-guard-catalog.md`, `references/data-lifecycle-guard-catalog.md`, `references/performance-guard-catalog.md`, `references/resilience-guard-catalog.md`, `references/operations-guard-catalog.md`, and `references/compatibility-governance-guard-catalog.md`.

## Mode Details

Scale mode output to material items:

- Design: contract, P0-P2 risks, minimal boundaries, guard plan, assumptions, and exclusions.

- Implementation: changed files, evidence, commands/results, architecture choices, and gaps.

- Review: findings-first P0-P4 findings or gaps, evidence, and permitted fixes.

## Fix Rules

For an authorized behavior fix, add and run a failing-then-passing regression test when feasible. If that is infeasible, use the strongest practical evidence and name the reason and residual gap. Review-only work must not add or modify tests; an observed pre-existing RED test is evidence, not a fix.

Patch the narrowest code path that owns the invariant. Keep unrelated refactors out. Preserve public API unless the contract requires change.

## Skip Conditions

Do not use this skill for pure copy edits, UI-only style changes, trivial local refactors, metadata-only edits, or docs-only work that cannot affect state, auth, API contracts, external calls, persistence, performance, distributed behavior, or operational risk.

