# Contributing

## Skill Changes

- Edit `skills/boring-backend/` first. Do not make source changes in the mirrors.
- Sync each changed source file to `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/` before submitting.
- Keep evaluation inputs under `validation/`, executable tooling under `scripts/`, and deterministic fixtures/tests under `tests/`; all stay outside the runtime skill. Generated output belongs under `reports/`.

## Verification

Use a project-local virtual environment, install `requirements-dev.txt`, and run:

```text
python scripts/verify_all.py
```

Add or update tests for behavior changes. Report any verification command that could not be run.

The repository verifier provides structural and lexical drift guards. Use clean external evaluations for trigger rates or agent-behavior claims.

The check names in `.github/workflows/verify.yml` are bound to the repository's `main` ruleset. Update the ruleset in the same change whenever a required job is renamed or removed.

## Pull Requests

Keep changes scoped and explain their evidence. Do not commit secrets, credentials, tokens, or sensitive report data.
