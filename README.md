# Boring Backend Skill

[한국어](README.ko.md)

Boring Backend is a compact skill for AI coding agents that design, implement, or review API/service reliability work.

## Design Bias

Boring Backend is built for AI coding agents that can over-design, miss edge cases, or overstate confidence. It intentionally blends:

- Test-aware problem framing: start from failure modes, not happy paths. Every guard should end in runnable evidence when possible. Static review and checklists help, but missing tests or smoke runs lower confidence.
- Agent hygiene: keep changes surgical, name assumptions, choose the smallest working path, and define success in commands the agent can run.
- SOLID + YAGNI balance: separate real responsibilities such as routing, domain rules, persistence, DTOs, and error mapping only when the current contract needs it. Avoid interfaces, factories, strategies, or plugin layers for future variants.

The intended advantage is one clear trigger with internal modes for design, implementation, review, and production-evidence runs. That keeps discovery simple while still protecting correctness, security, data integrity, status codes, performance, and operational guardrails.

## Skill

- `boring-backend`: design, implement, or review API/service reliability for auth, data integrity, idempotency, concurrency, performance, distributed behavior, and operational risk.

The skill uses one trigger with four internal modes:

- Design: define contracts, invariants, guard strategy, tradeoffs, and evidence targets before implementation.
- Implementation: make scoped API/service changes with tests and guard evidence.
- Review: check code for P0-P4 reliability, security, data integrity, performance, compatibility, and operations risks.
- Production evidence: separate local evidence from load, query-plan, latency, saturation, rollout, rollback, and observability evidence.

## Layout

- `skills/boring-backend/`: source skill package.
- `.agents/skills/boring-backend/`: project-local Codex/Antigravity-style mirror.
- `.claude/skills/boring-backend/`: project-local Claude Code mirror.
- `validation/`: repository-level behavior, trigger, and fairness evaluation inputs; intentionally outside the installed runtime skill.
- `scripts/run_skill_eval.py`: runs opt-in provider adapters against the trigger suite and writes bounded protocol output under `reports/`.
- `scripts/verify_all.py`: runs mirror and repository checks.
- `scripts/verify_boring_backend_skill_mirrors.py`: verifies source and mirror packages stay in sync.
- `reports/`: ignored workspace for generated evaluation output; retained only as an empty local target.

## Install

With Codex `skill-installer`, install only the runtime skill folder:

```text
--repo dd3ok/boring-backend --path skills/boring-backend
```

Manual install is also path-only: copy `skills/boring-backend` into your runtime's skills directory.

Common local targets:

| Runtime | Project scope | User scope |
|---|---|---|
| Codex / Agents | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity | `.agents/skills/boring-backend` | `~/.gemini/config/skills/boring-backend` |

Do not install `.agents/`, `.claude/`, `validation/`, `reports/`, or `scripts/` as runtime skills. They are development mirrors, evaluation assets, generated output, and verification utilities.

## Verification

Verification supports CPython 3.11 through 3.14. Newer CPython versions are unverified.

Install the development dependency in a project-local Python 3 virtual environment:

```text
python -m pip install -r requirements-dev.txt
```

Then run the verification entrypoint from the repository root with the active environment or the platform's Python 3 launcher:

```text
python scripts/verify_all.py
python3 scripts/verify_all.py  # macOS/Linux
py -3 scripts/verify_all.py    # Windows
```

GitHub Actions runs the same entrypoint on CPython 3.14 for Ubuntu, macOS, and Windows, plus CPython 3.11 on Ubuntu.

## Evaluation

Real agent evaluations are opt-in and stay outside CI. Adapters are trusted local programs; the harness validates its protocol but is not a sandbox. An adapter must not create background descendants or write outside the request's run directory. Timeout cleanup terminates the adapter process tree on a best-effort basis.

The harness starts the adapter from the repository root, so relative adapter arguments resolve there. The adapter receives `--request` and `--response` JSON paths, must run the evaluated agent in the request's `paths.workspace`, and must send only the request's top-level `query` to that agent. It must not inspect the evaluation suite, labels, case ids, rationale, or expected result. Metrics from an adapter that violates these rules are untrusted. Activation, catalog reads, and usage must come from vendor traces or APIs and remain `null` when unavailable.

Case/trial blocks and per-block variant order are deterministically randomized from `--seed`; every variant in a block receives the same paired seed. The response object accepts `activation` (`bool|null`), `catalogs` (`string[]|null`), `usage` (`object|null`), run-relative `artifacts`, and adapter `metadata`. Each usage value must be `null` or an integer from 0 through 9,007,199,254,740,991. The harness discards stdout, concurrently drains stderr while retaining at most a 2 KiB excerpt, limits JSON nesting to 100, reads at most 64 KiB plus one byte from the response, and accepts at most 32 declared artifact files totaling 16 MiB.

Each output includes the request/response run artifacts, bounded stderr excerpts, JSONL results, summary, and a manifest. The manifest records the Git commit and dirty state, a worktree/diff digest when dirty, the harness hash, skill hashes, and hashes for runner command arguments that resolve to files.

```text
python scripts/run_skill_eval.py --output reports/eval/run-001 --trials 3 --seed 17 --variant current=skills/boring-backend --variant baseline --runner-exe python --runner-arg path/to/vendor_adapter.py --runner-meta vendor=example --runner-meta model=example
```

The repository includes only a deterministic test fixture for the protocol, not a real vendor adapter. A fixture run proves harness behavior, not skill quality or token savings. Keep `forward-test-prompts.md` as a human or separately graded behavior rubric.

## License

MIT. See `LICENSE`.
