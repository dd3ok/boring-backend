# Boring Backend Skill Repo Instructions

Scope: this file applies only inside this repository.

Use the local project skill before global skills:

- `skills/boring-backend/SKILL.md`: use for API/service reliability design, implementation, review, guard evidence, and production-readiness risk checks.

Vendor-local mirrors are kept in `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/`. Do not edit mirrors directly. Edit `skills/boring-backend` first, then sync mirrors and run:

```powershell
python .\scripts\verify_boring_backend_skill_mirrors.py
```

Do not install skills, plugins, packages, or test tools globally from this repository. Keep any generated verification output under `reports/`.
