# RDD Skills

RDD means Reliability-Driven Design: a three-layer skill workflow for AI coding agents.

## Skills

- `rdd-design`: design API/service reliability contracts before implementation.
- `rdd-implementation`: implement the smallest guarded solution with tests and named assumptions.
- `rdd-review`: review API/service code for P0-P4 reliability gaps with evidence.

## Layout

- `skills/`: source skill packages.
- `.agents/skills/`: project-local Codex/Antigravity-style mirrors.
- `.claude/skills/`: project-local Claude Code mirrors.
- `scripts/verify_rdd_skill_mirrors.py`: verifies source and mirror packages stay in sync.
- `reports/`: forward-test reports and a tiny runnable implementation test artifact.

Each RDD skill bundles its own `references/` directory so a single skill folder can be copied or installed without broken cross-skill links.

## Install

Install only the skill folders, not the repository root. With Codex `skill-installer`, use these arguments:

```powershell
--repo dd3ok/rdd-skills --path skills/rdd-design skills/rdd-implementation skills/rdd-review
```

Manual install is also path-only: copy `skills/rdd-design`, `skills/rdd-implementation`, and `skills/rdd-review` into your runtime's skills directory.

Do not install `.agents/`, `.claude/`, `reports/`, or `scripts/` as runtime skills. They are development mirrors, test artifacts, and verification utilities.

## Verification

```powershell
python .\scripts\verify_rdd_skill_mirrors.py
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s .\reports\rdd-forward-test-implementation -p 'test_*.py'
```
