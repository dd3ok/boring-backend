# Boring Backend Design Forward Test: Reservation API

## Skill And References Used

- Skill: `C:\Users\hwick\Documents\dev\agent-lab\skills\boring-backend\SKILL.md`
- References:
  - `skills/boring-backend/references/core-guard-catalog.md`
  - `skills/boring-backend/references/security-guard-catalog.md`
  - `skills/boring-backend/references/performance-guard-catalog.md`
  - `skills/boring-backend/references/resilience-guard-catalog.md`
  - `validation/forward-test-prompts.md`

## Skill Evaluation

The skill was clear for this task. It pushed the design toward contract, P0/P1/P2 risk, minimal ownership boundaries, and verification evidence before package structure or implementation detail. The reference routing was also clear: reservation overlap, status codes, list bounds, public input, and transaction/lock behavior mapped directly to the selected references.

Missing or weaker guidance:

- Design mode guidance does not give a concrete template for choosing among database-native exclusion constraints, pessimistic row locks, optimistic versions, or serializable retries when several could satisfy the same invariant.
- It names security boundaries but does not say how much unauthenticated single-tenant API design is acceptable before requiring auth in the contract.
- It does not explicitly ask the designer to define time-range boundary semantics, such as whether a reservation ending at 11:00 conflicts with one starting at 11:00. That matters for overlap correctness.

## Resulting Design Artifact

### Contract Summary

Actors and boundary:

- This is a small single-tenant reservation API. Authentication, per-user ownership, and admin roles are out of scope unless the API is exposed beyond trusted callers.
- Public input must bind only through request DTOs. Callers cannot set server-owned fields such as reservation status, creation time, cancellation time, or internal IDs.

Room endpoints:

- `POST /rooms`
  - Creates a room.
  - Request fields: `name`, optional `capacity`.
  - `201 Created` with the room DTO on success.
  - `400 Bad Request` for malformed input.
  - `409 Conflict` if a uniqueness rule such as room name is adopted and violated.
- `GET /rooms`
  - Lists rooms with bounded pagination.
  - `200 OK` with `items`, `limit`, `offset` or cursor, and `total` only if total count is intentionally supported.
  - `400 Bad Request` for invalid pagination bounds.

Reservation endpoints:

- `POST /reservations`
  - Creates an active reservation for one room.
  - Request fields: `room_id`, `starts_at`, `ends_at`, optional customer/contact fields if needed.
  - Time values are timezone-aware instants normalized to UTC.
  - Range semantics are half-open: `[starts_at, ends_at)`. A reservation ending at 11:00 does not conflict with one starting at 11:00.
  - `201 Created` with reservation DTO on success.
  - `400 Bad Request` when `starts_at >= ends_at`, timestamps are invalid, or required fields are missing.
  - `404 Not Found` when `room_id` does not exist.
  - `409 Conflict` when an active same-room reservation overlaps.
- `POST /reservations/{reservation_id}/cancel`
  - Cancels an active reservation.
  - `200 OK` with the canceled reservation DTO on first successful cancellation.
  - `404 Not Found` when the reservation does not exist.
  - `409 Conflict` if the reservation is already canceled and the contract chooses cancellation as a state transition rather than idempotent success. For this small API, prefer idempotent cancel returning `200 OK` with the already-canceled DTO.

Data rules:

- Room IDs are server-generated.
- Reservation IDs are server-generated.
- Only active reservations block overlap. Canceled reservations remain in history but are excluded from conflict checks.
- Same-room overlap condition: active reservation A conflicts with requested range B when `A.starts_at < B.ends_at` and `B.starts_at < A.ends_at`.
- Cross-room overlaps are allowed.
- List endpoints must be bounded by a maximum page size.

### Risk Map

P0:

- No implementation-specific P0 is present at design time. During implementation, failure to start the service, initialize persistence, run migrations, or collect tests is P0.

P1:

- Same-room overlapping reservations under concurrent create requests can corrupt the core booking invariant.
- A process-local lock can pass local tests but fail with multiple processes or instances.
- Direct entity binding from public input could allow callers to set server-owned status fields and bypass cancellation or active-reservation rules.

P2:

- Incorrect status mapping can hide contract failures, especially returning `500` for validation, overlap conflict, missing room, or already-canceled state.
- Ambiguous time boundary semantics can make adjacent reservations incorrectly fail or overlapping reservations incorrectly pass.
- Unbounded room listing can become a contract and performance risk as data grows.

P3:

- Overbuilding with event buses, distributed locks, plugin layers, or speculative service decomposition would add complexity without protecting the current invariant.

P4:

- Naming and response-shape consistency should be checked, but they do not outrank overlap correctness or API status behavior.

### Minimal Architecture

- Route/controller layer: owns HTTP parsing, DTO validation, response shaping, and status-code mapping.
- Service/use-case layer: owns reservation state transitions, overlap policy, cancellation behavior, and transaction orchestration.
- Repository/DAO layer: owns persistence queries and database constraint interactions.
- Persistence schema/migration boundary: owns room and reservation tables, indexes, and the database-backed overlap guard.
- Error mapping: converts validation, not-found, conflict, and invalid-state errors to the contract statuses.

Concurrency design:

- Prefer a database-backed invariant over an application-only check.
- Strong option: use a database constraint that prevents overlapping active ranges for the same room, such as a range/exclusion constraint in a database that supports it.
- Portable option: run reservation create in a transaction, lock the target room or same-room reservation set, check for active overlaps, insert the reservation, and handle deadlocks or serialization failures as either safe retry or `409 Conflict` according to the chosen database behavior.
- Do not rely on in-memory or process-local mutexes unless the implementation explicitly documents single-process local-only scope.
- If the selected database cannot enforce the invariant under concurrent writers, the implementation must state that as a P1 gap instead of claiming concurrency safety.

Performance and indexing:

- Index rooms by the selected uniqueness field if uniqueness is part of the contract.
- Index reservations by `room_id`, status, and time range/query fields used by the overlap check.
- Keep list responses as DTO projections, not persistence entities or nested graphs.
- Avoid claiming p95/p99 latency or production throughput without measurement.

### Guard Plan

Contract tests:

- `POST /rooms` returns `201` for valid input and rejects malformed input with `400`.
- `GET /rooms` enforces pagination bounds and returns a stable list shape.
- `POST /reservations` returns `201` for valid non-overlapping reservations.
- Missing room returns `404`.
- Invalid time range returns `400`.
- Same-room overlap returns `409`.
- Adjacent half-open ranges succeed.
- Different-room overlapping ranges succeed.
- Cancel existing active reservation returns `200` and changes status to canceled.
- Canceled reservation no longer blocks a new reservation for the same room and time range.
- Repeated cancel returns the agreed idempotent `200` response, or the test must assert the alternative `409` contract if that choice changes.

Concurrency tests:

- Start two concurrent `POST /reservations` requests for the same room with overlapping ranges. Exactly one may create an active reservation; the other must return `409` or an equivalent handled conflict. After both complete, persistence must contain no overlapping active pair.
- Start two concurrent `POST /reservations` requests for different rooms with overlapping ranges. Both should succeed.
- If using serializable isolation or locks, include a test or integration check that deadlock/serialization failure is handled rather than surfacing as `500`.

Persistence/static checks:

- Verify the migration includes the database-backed overlap guard or the lock/transaction path required by the selected database.
- Verify an index exists for the overlap query path.
- Verify public request DTOs exclude server-owned fields.
- Verify error handling maps known domain failures to `400`, `404`, and `409` rather than falling through to `500`.

Smoke checks:

- Create a room, create a reservation, cancel it, then create another reservation for the same room/time.
- Create several rooms and verify room listing respects maximum page size.

### Assumptions And Exclusions

- No code is implemented in this design pass.
- No external services, payments, notifications, queues, or events are in scope.
- No authentication or per-user authorization is designed beyond a trusted single-tenant boundary. If this API becomes public or multi-tenant, auth and object-ownership checks become P1 requirements.
- Production readiness is not claimed from this design alone. Implementation still needs runnable tests, persistence evidence, and a concurrency test against the actual database.

