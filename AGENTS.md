# Boring Backend Skill Repo Instructions

Scope: this file applies only inside this repository.

Use the local project skill before global skills:

- `skills/boring-backend/SKILL.md`: use for API/service reliability design, implementation, review, guard evidence, and production-readiness risk checks.

Vendor-local mirrors are kept in `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/`. Do not edit mirrors directly. Edit `skills/boring-backend` first. Install `requirements-dev.txt` only in a project-local virtual environment, then sync mirrors and run:

```text
python scripts/verify_all.py
python3 scripts/verify_all.py  # macOS/Linux
py -3 scripts/verify_all.py    # Windows
```

Do not install packages or test tools globally from this repository. Follow `validation/experiment-fairness.md` for release evaluation scope and isolation. Do not commit generated evaluation output or workspaces.

Always preserve path-only distribution: only `skills/boring-backend/` is installable. Keep repository mirrors, evaluation assets, tests, and verification tooling outside that boundary.
