## Summary

Describe the change and the evidence used to verify it.

## Checklist

- [ ] If skill files changed, source-first edits were made under `skills/boring-backend/`; otherwise N/A.
- [ ] If skill files changed, mirrors under `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/` are synchronized; otherwise N/A.
- [ ] Tests were added or updated where behavior changed, and `python scripts/verify_all.py` passes.
- [ ] If runtime behavior or activation boundaries changed, relevant external evaluations followed `validation/experiment-fairness.md` and the runner/results are identified; otherwise N/A.
- [ ] If the runtime package changed, both READMEs target the planned immutable release and the tag/release step is noted; otherwise N/A.
- [ ] The runtime `skills/boring-backend/LICENSE` matches the root `LICENSE`.
- [ ] Install guidance still targets only `skills/boring-backend/`; repository tooling and mirrors remain outside the package.
- [ ] No secrets, credentials, tokens, or sensitive report data are included.
