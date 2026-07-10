## Summary

Describe the change and the evidence used to verify it.

## Checklist

- [ ] If skill files changed, source-first edits were made under `skills/boring-backend/`; otherwise N/A.
- [ ] If skill files changed, mirrors under `.agents/skills/boring-backend/` and `.claude/skills/boring-backend/` are synchronized; otherwise N/A.
- [ ] Tests were added or updated where behavior changed, and `python scripts/verify_all.py` passes.
- [ ] If runtime instructions or expected outputs changed, behavior evaluations were run from an external workspace; otherwise N/A.
- [ ] If discovery metadata or activation boundaries changed, trigger evaluations were run from an external workspace; otherwise N/A.
- [ ] If evaluations are claimed as release evidence, only a copied candidate skill and declared behavior prompt/inputs or trigger query reached the evaluated process, and source/grader paths were unreadable; otherwise N/A.
- [ ] The runtime `skills/boring-backend/LICENSE` matches the root `LICENSE`.
- [ ] If `.codex-plugin/plugin.json` changed, its schema and component paths were validated; otherwise N/A.
- [ ] No secrets, credentials, tokens, or sensitive report data are included.
