# Boring Backend Skill

[한국어](README.ko.md)

Boring Backend is a compact skill for AI coding agents that design, implement, or review API/service reliability work.

## Design Bias

Boring Backend is built for AI coding agents that can over-design, miss edge cases, or overstate confidence. It intentionally blends:

- Test-aware problem framing: start from failure modes, not happy paths. Every material risk control should end in runnable evidence when possible. Static review and checklists help, but missing tests or smoke runs lower confidence.
- Agent hygiene: keep changes surgical, name assumptions, choose the smallest working path, and define success in commands the agent can run.
- SOLID + YAGNI balance: separate real responsibilities such as routing, domain rules, persistence, DTOs, and error mapping only when the current contract needs it. Avoid interfaces, factories, strategies, or plugin layers for future variants.

The intended advantage is one clear trigger with internal modes for design, implementation, and review. That keeps discovery simple while still protecting correctness, security, data integrity, status codes, performance, and operational safeguards.

## Skill

- `boring-backend`: design, implement, or review API/service reliability for auth, data integrity, idempotency, concurrency, performance, distributed behavior, and operational risk.

The skill uses one trigger with three internal modes:

- Design: define contracts, invariants, risk controls, tradeoffs, and evidence targets before implementation.
- Implementation: make scoped API/service changes with tests and evidence for those controls.
- Review: report reliability, security, data-integrity, performance, compatibility, and operations findings in impact order.

Explicit environment-specific evidence requests load a conditional safety reference before any invasive action.

## Layout

- `skills/boring-backend/`: source skill package.
- `.agents/skills/boring-backend/`: project-local Codex and Antigravity mirror.
- `.claude/skills/boring-backend/`: project-local Claude Code mirror.
- `validation/`: repository-level behavior, trigger, and fairness evaluation inputs; intentionally outside the installed runtime skill.
- `scripts/verify_all.py`: runs mirror and repository checks.
- `scripts/verify_boring_backend_skill_mirrors.py`: verifies source and mirror packages stay in sync.

## Install

With Codex `skill-installer`, install only the runtime skill folder:

```text
--repo dd3ok/boring-backend --ref v1.2.1 --path skills/boring-backend
```

Unless a destination is supplied, `skill-installer` installs the package at `$CODEX_HOME/skills/boring-backend` (usually `~/.codex/skills/boring-backend`).

The install target contains the complete runtime package:

```text
boring-backend/
|-- SKILL.md
|-- LICENSE
|-- agents/openai.yaml
`-- references/*.md
```

These files are sufficient for the full skill behavior. `SKILL.md` routes to the bundled references only when needed; repository tests, evaluation inputs, and verification scripts are not runtime dependencies.

For a manual install, copy the entire `skills/boring-backend` folder into a destination below. Do not copy only `SKILL.md`, because its linked references are part of the behavior.

Common destination paths for the same folder:

| Runtime | Project scope | User scope |
|---|---|---|
| Codex | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity IDE | `.agents/skills/boring-backend` | `~/.gemini/config/skills/boring-backend` |
| Antigravity CLI | `.agents/skills/boring-backend` | `~/.gemini/antigravity-cli/skills/boring-backend` |

Current path references: [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills), [Antigravity IDE](https://antigravity.google/docs/skills?app=antigravity-ide), and [Antigravity CLI](https://antigravity.google/docs/cli-plugins).

Do not install the repository root. `.agents/`, `.claude/`, `.github/`, `validation/`, `tests/`, `scripts/`, and `requirements-dev.txt` are repository maintenance files, not runtime skill contents.

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

GitHub Actions runs the same entrypoint on CPython 3.14 for Ubuntu, macOS, and Windows, and on CPython 3.11, 3.12, and 3.13 for Ubuntu.

## Evaluation

Use an external provider-specific runner for behavior cases when runtime instructions or expected outputs change, and for trigger cases when discovery metadata or activation boundaries change. This repository stores evaluation inputs and isolation rules, not a runner or generated results.

- Use `validation/trigger-eval-cases.json` to check implicit activation boundaries.
- Use `validation/behavior-eval-cases.json` as the canonical machine-readable prompts, inputs, and grader expectations after explicitly selecting the skill.
- Follow `validation/experiment-fairness.md` for isolation, grading, and comparisons with no skill or a previous version.

## License

MIT. See `LICENSE`; the installable runtime subtree includes the same terms at `skills/boring-backend/LICENSE`.
