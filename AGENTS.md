# Boring Backend Skill Repo Instructions

Scope: this file applies only inside this repository.

For applicable API/service work, use the repository-discovered `boring-backend` skill. Codex and Antigravity discover `.agents/skills/boring-backend/`; Claude Code discovers `.claude/skills/boring-backend/`. If a same-named user/global copy is also present, prefer the repository path and do not read both copies.

Treat `skills/boring-backend/` as the canonical editable source, not a discovery path. Do not edit the vendor-local mirrors directly. Install `requirements-dev.txt` only in a project-local virtual environment, then sync mirrors and run:

```text
python scripts/verify_all.py
python3 scripts/verify_all.py  # macOS/Linux
py -3 scripts/verify_all.py    # Windows
```

Do not install packages or test tools globally from this repository. When release evidence uses an external evaluation runner, follow `validation/experiment-fairness.md` and identify the runner in the PR. Do not commit generated evaluation output or workspaces.

When the runtime package changes, choose the next immutable release, update the `--ref` value in both READMEs in the same change, and tag only the verified merge commit after CI passes.

Always preserve path-only distribution: only `skills/boring-backend/` is installable. Keep repository mirrors, evaluation assets, tests, and verification tooling outside that boundary.
