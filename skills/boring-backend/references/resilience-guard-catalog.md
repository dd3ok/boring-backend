# Resilience Guard Catalog

Read this file only when the task touches downstream services, subprocesses, shared filesystems, or other failure-prone runtime integrations; retries/timeouts, queues/events, distributed locks, cache consistency, quotas, throttling, backpressure, overload control, or multi-instance behavior.

## Implementation Lens

| Risk | Implement |
|---|---|
| Timeout and retry | Set timeouts for external calls. Retry only transient failures, with bounded attempts, backoff, jitter, and an overall deadline. Do not retry non-idempotent work without an idempotency key. |
| Retry storm | Add a retry budget, circuit breaker, or fail-fast behavior when repeated retries can amplify overload. Surface 429/503 and `Retry-After` where the API contract supports it. |
| Overload and quotas | Bound request fan-out, queue depth, retry concurrency, worker pools, tenant/caller quotas, and dependency calls. Use rate limits, bulkheads, or backpressure where overload can spread. |
| Distributed lock | Prefer DB constraints, conditional writes, leases with fencing tokens, or a proven coordination service. Name single-process lock assumptions. |
| Event consistency | When a DB write publishes a message/event, use outbox or an equivalent atomic handoff. Consumers must tolerate duplicate, delayed, and reordered messages. |
| Idempotent consumer | Deduplicate by stable message/business ID. Reprocessing a delivered message must not double-charge, double-reserve, double-email, or corrupt counters. |
| Poison messages | Define retry limits, dead-letter behavior, and observability for messages that repeatedly fail. |
| Cache consistency | Define TTL, invalidation, stale-data tolerance, and stampede/cold-start behavior. Do not cache authorization-sensitive data without keying by caller/security context. |
| Cascading failure | Identify hard dependencies, soft dependencies, degraded modes, and whether fallback can create worse load or stale decisions. |

## Review Lens

- Are external calls bounded by timeout, retry budget, and circuit breaker/fail-fast behavior?
- Can retries duplicate state changes or amplify overload?
- Can retries, queues, fan-out, or worker pools exceed bounded quotas under load?
- Does a distributed lock still protect data after process crash, network delay, or stale leadership?
- Can duplicate or out-of-order messages reapply side effects?
- Can cache stale data, cold starts, or stampedes violate correctness or overload dependencies?
- Does a local test overclaim multi-instance or distributed safety?
