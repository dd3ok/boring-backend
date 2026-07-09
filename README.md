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

## Verification

```powershell
python .\scripts\verify_rdd_skill_mirrors.py
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s .\reports\rdd-forward-test-implementation -p 'test_*.py'
```
