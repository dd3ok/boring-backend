# Performance Guard Catalog

Read this file only when the task touches latency, throughput, high-traffic endpoints, large list/search/export/bulk operations, DB query performance, N+1 risk, indexing, connection/thread pools, payload size, caching for speed, load testing, or performance optimization.

## Implementation Lens

| Risk | Implement or Measure |
|---|---|
| Measure before optimize | Do not claim faster performance without before/after evidence, a benchmark/load test, query plan, or a clearly named measurement gap. |
| API latency budget | For high-traffic paths, name the expected latency signal such as p95/p99 duration, error rate, traffic rate, or saturation. Local unit tests are not latency evidence. |
| List/search/export/bulk | Bound page size, filters, sort fields, exports, uploads, and batch sizes. Use streaming or async jobs for large payloads instead of loading everything into memory. |
| DB query path | Check indexes, query shape, N+1 risk, unbounded sort, large offset scans, row counts, and transaction scope. Prefer framework-native query/count tests or `EXPLAIN` evidence when performance is the goal. |
| Resource saturation | Bound connection pools, thread pools, queues, memory buffers, file handles, and request body sizes. Do not hide saturation by adding unbounded workers. |
| Payload and serialization | Avoid returning unused fields, large nested graphs, raw blobs, or repeated serialization work on hot endpoints. Prefer DTO/projection shapes that match the contract. |
| Cache value | Measure the latency, throughput, or dependency-load benefit. Do not add a cache until key scope, invalidation, stale tolerance, and caller/security context are explicitly defined and owned. |
| Microbenchmark scope | Use JMH, pytest-benchmark, k6, or equivalent only when the task asks for hot-path, latency, throughput, or algorithmic optimization. Do not add benchmark harnesses to ordinary CRUD work. |

## Review Lens

- Is the endpoint or job bounded by request, caller/tenant, result size, and memory use?
- Could the code introduce N+1 queries, full scans, unbounded sort/export, or large offset pagination?
- Are indexes/query plans/test evidence present when performance improvement is claimed?
- Are pools, queues, buffers, and request bodies bounded under load?
- Does caching preserve correctness, authorization, and invalidation semantics?
- Are p95/p99 latency, throughput, error rate, or saturation claims backed by measurement?
- Is microbenchmarking requested and useful, or would it add cost without changing the decision?
