# Boring Backend Review Forward Test

## Scope

Reviewed pseudo implementation only:

- FastAPI order API with product list/create and order create/payment/cancel.
- SQLite persistence.
- No idempotency table.
- Product stock checked by read-then-write without transaction lock.
- List endpoint returns all rows.
- Tests only cover happy paths.
- Report claims production-ready.

No source files were edited. No build, typecheck, test, static guard, or API smoke command was run because no runnable implementation was provided and this was review-only.

## References Used

- `skills/Boring Backend-review/SKILL.md`: review order, P0-P4 severity definitions, review-only behavior, and report shape.
- `skills/Boring Backend-review/references/guard-catalog.md`: idempotency, concurrent read-then-write, stock/count invariants, pagination, error mapping, and local-only assumption checks.
- `skills/Boring Backend-review/references/security-guard-catalog.md`: object/function authorization and fail-closed auth checks for state transitions accepting user-controlled IDs.
- `skills/Boring Backend-review/references/performance-guard-catalog.md`: list endpoint bounds, payload size, query path, and resource saturation checks.
- `skills/Boring Backend-review/references/resilience-guard-catalog.md`: transaction/lock safety, retry/idempotency interaction, and local-vs-distributed safety checks.
- `skills/Boring Backend-review/references/operations-guard-catalog.md`: production-readiness evidence, observability, SLO, backup/restore, compatibility, and resource-risk checks.
- `skills/Boring Backend-review/references/forward-test-prompts.md`: expected pass signal for an Boring Backend review of the generated order API.

## Verdict

Not production-ready. Confidence is medium because the input is pseudo implementation rather than runnable code, but the described behavior is enough to identify P1 data-integrity failures and several unproven production-readiness claims.

## P0 Findings

None observed from the pseudo implementation. There is no evidence of build/import/test collection failure, but no runnable artifact was supplied, so P0 cannot be verified.

## P1 Findings

1. Missing idempotency for order create/payment/cancel can duplicate side effects.
   State-changing operations have no durable idempotency key, request fingerprint, replayed result, or payload-mismatch conflict. Retries can create duplicate orders, double-apply payment, or repeat cancellation effects. This is a data-integrity failure under the core guard catalog.

2. Stock check uses read-then-write without a transaction lock or atomic conditional update.
   Concurrent order creation can observe the same stock value and both decrement it, causing oversell or negative inventory. The core and resilience catalogs call for a DB-backed transaction/lock, constraint, atomic conditional update, serializable retry, or equivalent evidence.

3. Authorization/ownership is not evidenced for order payment/cancel.
   If this is a multi-user or public API, accepting order IDs for payment/cancel without documented object authorization lets one caller act on another caller's order. If the API is intentionally single-tenant or internal-only, that assumption must be stated. The production-ready claim is not supportable without this evidence.

## P2 Findings

1. Error mapping and invalid state transitions are not evidenced.
   Happy-path tests do not prove validation, not-found, conflict, invalid transition, idempotency replay, or auth failures map to contract status codes. Payment after cancellation, cancellation after payment, duplicate payment, nonexistent product/order, and insufficient stock should have explicit status-code expectations.

2. Idempotency conflict behavior is absent from the API contract.
   The core catalog expects same key plus same payload to replay the prior result and same key plus different payload to return conflict. The pseudo implementation has no idempotency table or described error mapping, so the API contract is incomplete for retryable clients.

## P3 Findings

1. Product list returns all rows without pagination or bounds.
   This creates memory, latency, and response-size risk as data grows. The core and performance catalogs expect bounded list endpoints, validated page limits, or an explicit documented exclusion with production risk called out.

2. SQLite production assumptions are not named.
   SQLite may be acceptable for small/local deployments, but production readiness needs explicit concurrency, backup/restore, migration, and single-writer assumptions. Local persistence alone is not production-readiness evidence.

3. Operational readiness is not evidenced.
   The pseudo report claims production-ready without request IDs, structured logs, error/latency metrics, SLO signals, backup/restore expectations, migration/rollback notes, or resource-growth bounds.

4. Test coverage is too narrow for the risk surface.
   Happy-path-only tests miss the core reliability guards: retry/replay behavior, payload mismatch, concurrent stock decrement, duplicate line items, invalid transitions, conflict responses, pagination bounds, auth failures, and not-found cases.

## P4 Findings

1. The production-ready claim is overstated.
   The report should distinguish local happy-path evidence from production readiness and name missing guards as gaps. As written, the claim is report-quality risk and could mislead reviewers.

2. Missing evidence is not separated from passing evidence.
   The report should list commands/results, guard status, and named gaps instead of implying untested behavior is safe.

## Guard Status

- Idempotency: failing gap for order create/payment/cancel.
- Stock/count invariant: failing gap under concurrent requests.
- Pagination: failing or unbounded gap for product list.
- Status codes/error mapping: unevidenced.
- Auth/ownership: unevidenced and likely P1 if public or multi-user.
- Performance/resource bounds: unevidenced and unbounded for list.
- Resilience/transaction safety: failing gap for stock mutation.
- Operations readiness: unevidenced despite production-ready claim.

## Skill Clarity

The skill was clear for this forward test. It gave a concrete review order, severity definitions, review-only stopping behavior, reference routing, and a report shape. The forward-test prompt also clearly identified the expected pass signal: read the core guard catalog, order findings by severity, treat missing runnable evidence as not success, and avoid editing files.

## Missing Guidance

- Pseudo-only reviews could use explicit guidance on how to label "not verified" versus P0 when no runnable artifact exists.
- The skill could clarify severity for missing auth when the implementation claims production-ready but the contract does not explicitly mention users, tenants, or roles.
- Pagination severity could be more explicit when pagination was not in the original feature request but the endpoint is production-facing.
- SQLite/local-only production claims could use a small severity rubric for when they are P3 operational gaps versus P1 data-integrity risks.
- The distinction between P3 operational readiness gaps and P4 report-quality overclaims could be made more explicit.

