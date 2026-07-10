# Forward Test Prompts

Use these behavior scenarios only after explicitly selecting the boring-backend skill. They are not part of normal design, implementation, or review work. Use `trigger-eval-cases.json` for implicit selection tests and `experiment-fairness.md` for comparison controls.

## Design Behavior

Prompt:

```text
Use $boring-backend to design a small order API before implementation. It must support product create/list, order create, payment, cancellation, SQLite persistence, idempotency for create/payment/cancel, and pytest verification.
```

Pass signal: design mode triggers; contract, P0/P1/P2 risks, minimal package/module boundaries, and guard evidence are identified; no implementation code is written unless asked; idempotency, stock/count invariants, pagination, and local-only assumptions are named when relevant.

## Implementation Behavior

Prompt:

```text
Use $boring-backend to build a small FastAPI order API. It must support product create/list, order create, payment, cancellation, SQLite persistence, idempotency for create/payment/cancel, and pytest verification.
```

Pass signal: implementation mode triggers; the contract and core guard catalog are read; natural operation IDs, unique constraints, conditional writes, or a durable key plus fingerprint are accepted idempotency mechanisms; payload mismatch is rejected; only contract-final outcomes replay; transient failures are not cached by default; repeated or concurrent requests prove no double side effect; focused stock tests are added; speculative interfaces, event buses, and plugin layers are avoided.

## Review Behavior

Prompt:

```text
Use $boring-backend to review this generated order API for P0-P4 issues, idempotency gaps, concurrency risk, API status-code mismatches, and production-readiness overclaims.
```

Pass signal: review mode triggers; the core guard catalog is read; findings are ordered by severity; missing runnable evidence is not treated as success; review-only work never edits, while an authorized fix run leaves no new regression test failing.

## Ambiguous Request

Prompt:

```text
Improve this small reservation service. Keep it simple, but make sure it handles same-room overlap correctly when requests arrive at the same time.
```

Pass signal: implementation may trigger; review does not trigger unless review/self-review is requested; same-room overlap is treated as a data-integrity guard; single-process vs distributed lock assumptions are named.

## External Dependency Behavior

Prompt:

```text
Use $boring-backend to add a shipping-quote endpoint that calls an external carrier API from user input and stores the selected quote. Keep it small, but make it production-ready enough to review.
```

Pass signal: core, security, and resilience catalogs are read; user-controlled carrier URLs or upstream responses are treated as SSRF/unsafe API-consumption risk; timeout, bounded retry/backoff or named no-retry, schema validation, and duplicate-submission handling are covered; local-only gaps are named.

## Production Readiness Review Behavior

Prompt:

```text
Use $boring-backend to review this API before launch. Focus on production readiness, architecture, security, scalability, deployment, observability, and resource risk.
```

Pass signal: operations and applicable guard catalogs are read; local test evidence is separated from production readiness; observability, deployment/rollback, supply chain, performance, and cost/resource risk are checked; compatibility and backup/restore route to their dedicated catalogs when in scope.

## Learning Feedback Prompt

Use only when maintaining Boring Backend after a production incident, escaped P1/P2 defect, rollback caused by a missed guard, or repeated review miss.

Prompt:

```text
Evaluate whether the missed failure should become a Boring Backend guard. Record the missed invariant, the catalog that should own it, required evidence, and whether it is ready for a later clean run where every variant receives the same pre-registered guard.
```

Pass signal: learning is recorded as a candidate guard or regression prompt, not as a first-run implementation hint.

## Performance Review Behavior

Prompt:

```text
Use $boring-backend to review this product search/list API for performance before a high-traffic launch. Focus on pagination, query shape, indexes, N+1 risk, payload size, cache safety, pool limits, and whether performance claims are measured.
```

Pass signal: the performance catalog is read; bounded endpoint/query design is distinguished from measured latency or throughput evidence; microbenchmarks are not required unless hot-path optimization or explicit latency/throughput claims are in scope.

