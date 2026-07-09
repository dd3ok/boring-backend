# RDD Skill Repo Instructions

Scope: this file applies only inside this repository.

Use local project skills before global skills:

- `skills/rdd-design/SKILL.md`: use for API/service reliability contract and architecture design before implementation.
- `skills/rdd-implementation/SKILL.md`: use for API/service implementation with reliability guards, tests, and named assumptions.
- `skills/rdd-review/SKILL.md`: use for API/service review or self-review for P0-P4 reliability gaps.

Vendor-local mirrors are kept in `.agents/skills/` and `.claude/skills/`. Do not edit mirrors directly. Edit `skills/rdd-*` first, then sync mirrors and run:

```powershell
python .\scripts\verify_rdd_skill_mirrors.py
```

Do not install skills, plugins, packages, or test tools globally from this repository. Keep any generated verification output under `reports/`.

