# Forward Test Prompts

Use these only when maintaining or evaluating the RDD skills. They are not part of normal design, implementation, or review work.

## Design Trigger

Prompt:

```text
Use rdd-design to design a small order API before implementation. It must support product create/list, order create, payment, cancellation, SQLite persistence, idempotency for create/payment/cancel, and pytest verification.
```

Pass signal: design triggers; contract, P0/P1/P2 risks, minimal package/module boundaries, and guard evidence are identified; no implementation code is written unless asked; idempotency, stock/count invariants, pagination, and local-only assumptions are named when relevant.

## Implementation Trigger

Prompt:

```text
Use rdd-implementation to build a small FastAPI order API. It must support product create/list, order create, payment, cancellation, SQLite persistence, idempotency for create/payment/cancel, and pytest verification.
```

Pass signal: implementation triggers; the contract and core guard catalog are read; focused idempotency and stock tests are added; success replay, payload mismatch conflict, and handled failure replay are checked; speculative interfaces, event buses, and plugin layers are avoided.

## Review Trigger

Prompt:

```text
Use rdd-review to review this generated order API for P0-P4 issues, idempotency gaps, concurrency risk, API status-code mismatches, and production-readiness overclaims.
```

Pass signal: review triggers; the core guard catalog is read; findings are ordered by severity; missing runnable evidence is not treated as success; files are not edited unless self-review remediation or fixes are requested.

## Ambiguous Request

Prompt:

```text
Improve this small reservation service. Keep it simple, but make sure it handles same-room overlap correctly when requests arrive at the same time.
```

Pass signal: implementation may trigger; review does not trigger unless review/self-review is requested; same-room overlap is treated as a data-integrity guard; single-process vs distributed lock assumptions are named.

## External Dependency Trigger

Prompt:

```text
Use rdd-implementation to add a shipping-quote endpoint that calls an external carrier API from user input and stores the selected quote. Keep it small, but make it production-ready enough to review.
```

Pass signal: core, security, and resilience catalogs are read; user-controlled carrier URLs or upstream responses are treated as SSRF/unsafe API-consumption risk; timeout, bounded retry/backoff or named no-retry, schema validation, and duplicate-submission handling are covered; local-only gaps are named.

## Production Readiness Review Trigger

Prompt:

```text
Use rdd-review to review this API before launch. Focus on production readiness, architecture, security, scalability, deployment, observability, and resource risk.
```

Pass signal: operations and applicable guard catalogs are read; local test evidence is separated from production readiness; observability, compatibility, migration/rollback, backup/restore, supply chain, performance, and cost/resource risk are checked without outranking P0/P1/P2 failures.

## Performance Review Trigger

Prompt:

```text
Use rdd-review to review this product search/list API for performance before a high-traffic launch. Focus on pagination, query shape, indexes, N+1 risk, payload size, cache safety, pool limits, and whether performance claims are measured.
```

Pass signal: the performance catalog is read; bounded endpoint/query design is distinguished from measured latency or throughput evidence; microbenchmarks are not required unless hot-path optimization or explicit latency/throughput claims are in scope.
