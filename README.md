# Boring Backend Skill

[한국어](README.ko.md)

Boring Backend is a compact skill for AI coding agents that design, implement, or review API/service reliability work.

## Design Bias

Boring Backend is built for AI coding agents that can over-design, miss edge cases, or overstate confidence. It intentionally blends:

- Test-aware problem framing: start from failure modes, not happy paths. Every guard should end in runnable evidence when possible. Static review and checklists help, but missing tests or smoke runs lower confidence.
- Agent hygiene: keep changes surgical, name assumptions, choose the smallest working path, and define success in commands the agent can run.
- SOLID + YAGNI balance: separate real responsibilities such as routing, domain rules, persistence, DTOs, and error mapping only when the current contract needs it. Avoid interfaces, factories, strategies, or plugin layers for future variants.

The intended advantage is one clear trigger with internal modes for design, implementation, and review. That keeps discovery simple while still protecting correctness, security, data integrity, status codes, performance, and operational guardrails.

## Skill

- `boring-backend`: design, implement, or review API/service reliability for auth, data integrity, idempotency, concurrency, performance, distributed behavior, and operational risk.

The skill uses one trigger with three internal modes:

- Design: define contracts, invariants, guard strategy, tradeoffs, and evidence targets before implementation.
- Implementation: make scoped API/service changes with tests and guard evidence.
- Review: check code for P0-P4 reliability, security, data integrity, performance, compatibility, and operations risks.

Explicit environment-specific evidence requests use a conditional safety reference; they are not a fourth development mode.

## Layout

- `skills/boring-backend/`: source skill package.
- `.agents/skills/boring-backend/`: project-local Codex/Antigravity-style mirror.
- `.claude/skills/boring-backend/`: project-local Claude Code mirror.
- `.codex-plugin/plugin.json`: separate plugin packaging manifest; not part of the runtime skill subtree.
- `validation/`: repository-level behavior, trigger, and fairness evaluation inputs; intentionally outside the installed runtime skill.
- `scripts/verify_all.py`: runs mirror and repository checks.
- `scripts/verify_boring_backend_skill_mirrors.py`: verifies source and mirror packages stay in sync.

## Install

With Codex `skill-installer`, install only the runtime skill folder:

```text
--repo dd3ok/boring-backend --ref v1.1.0 --path skills/boring-backend
```

Manual install is also path-only: copy `skills/boring-backend` into your runtime's skills directory.

Path-only installation is the direct install boundary. `.codex-plugin/plugin.json` packages the same `skills/` tree for a Codex plugin marketplace, but this repository does not publish a marketplace. `agents/openai.yaml` is skill metadata, not a plugin manifest.

Common path-only local targets:

| Runtime | Project scope | User scope |
|---|---|---|
| Codex / Agents | `.agents/skills/boring-backend` | `$HOME/.agents/skills/boring-backend` |
| Claude Code | `.claude/skills/boring-backend` | `~/.claude/skills/boring-backend` |
| Antigravity | `.agents/skills/boring-backend` | `~/.gemini/config/skills/boring-backend` |

Do not install `.agents/`, `.claude/`, `validation/`, or `scripts/` as runtime skills. They are development mirrors, evaluation assets, and verification utilities.

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

Run behavior cases when runtime instructions or expected outputs change, and trigger cases when discovery metadata or activation boundaries change. Cross-provider harnesses and evaluation CI are optional and are not included.

- Use `validation/trigger-eval-cases.json` to check implicit activation boundaries.
- Use `validation/behavior-eval-cases.json` as the canonical machine-readable prompts, inputs, and grader expectations after explicitly selecting the skill.
- Follow `validation/experiment-fairness.md` for isolation, grading, and comparisons with no skill or a previous version.

## License

MIT. See `LICENSE`; the installable runtime subtree includes the same terms at `skills/boring-backend/LICENSE`.
