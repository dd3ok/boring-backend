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
- `validation/`: maintenance-only forward-test prompts; not part of the runtime skill.
- `scripts/verify_all.py`: runs mirror, repository, and forward-test implementation checks.
- `scripts/verify_boring_backend_skill_mirrors.py`: verifies source and mirror packages stay in sync.
- `reports/`: forward-test reports and a tiny runnable implementation test artifact.

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

Do not install `.agents/`, `.claude/`, `validation/`, `reports/`, or `scripts/` as runtime skills. They are development mirrors, maintenance prompts, test artifacts, and verification utilities.

## Verification

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

GitHub Actions runs the same entrypoint on Ubuntu, macOS, and Windows.
