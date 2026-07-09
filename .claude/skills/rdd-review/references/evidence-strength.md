# Evidence Strength

Read this file only when choosing required evidence, grading confidence, or preventing local checks from being reported as production readiness.

Do not add a new phase. Use the lowest evidence level that can actually prove the relevant guard, and name any higher-level gap instead of overclaiming.

## Levels

| Level | Evidence | Proves |
|---|---|---|
| L0 Static | lint, typecheck, compile, import, test collection | the artifact is syntactically/loadable enough to inspect or run tests |
| L1 Unit/domain | pure rule, validation, error mapping, state transition unit tests | local behavior for isolated logic |
| L2 Integration | real DB/repository/API smoke/framework wiring tests | components work together in the target stack |
| L3 Risk-specific | concurrency, idempotency replay, authz bypass, migration compatibility, contract, duplicate event/consumer tests | the named P1/P2 guard holds under its failure mode |
| L4 Production-readiness | load test, query plan, canary metric, SLO dashboard, restore drill, rollback rehearsal, failure injection | operational behavior is evidenced, not inferred from local tests |

## Use

- Low-risk local-only work can stop at L0/L1 if it names local-only assumptions.
- API, persistence, auth, migration, concurrency, or event work usually needs L2 plus any relevant L3 guard.
- Production-ready claims need L4 evidence or explicit gaps.
- Missing runnable evidence downgrades confidence. It becomes a finding when a required guard, contract, or production-readiness claim depends on it.

## Review Lens

- Does each P1/P2 guard map to evidence at the level that can prove it?
- Is static inspection being mislabeled as a test?
- Are unit tests being used to claim DB, concurrency, distributed, SLO, or rollback safety?
- Are unavailable checks reported as named gaps rather than success?
