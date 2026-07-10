# Contributing

## Skill Changes

- Edit `skills/boring-backend/` first. Do not make source changes in the mirrors.
- Sync each changed source file to `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/` before submitting.
- Keep lightweight evaluation inputs under `validation/`, verification tooling under `scripts/`, and deterministic repository tests under `tests/`; all stay outside the runtime skill.
- Run behavior cases for runtime instruction or expected-output changes and trigger cases for discovery metadata or activation-boundary changes. Follow `validation/experiment-fairness.md`.
- Keep `skills/boring-backend/LICENSE` identical to the root `LICENSE` so path-only installations retain the license terms.
- Keep distribution path-only. Do not add plugin or marketplace packaging.

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

For a release, publish only from a reviewed `main` commit after required checks and release-relevant evaluations pass. Prefer a signed annotated `vX.Y.Z` tag, never move or reuse a published tag, and enable GitHub immutable releases when the repository supports them.
