# Experiment Fairness

Use this only when maintaining or evaluating the boring-backend skill. It is not runtime guidance.

- Start every run from a clean context.
- Keep execution workspaces outside the skill repository. Reject ancestors with a same-name skill in a known vendor discovery root, disable same-name user/admin/managed skills outside the selected variant, and record the adapter's isolation method.
- Compare the current skill with no skill or a previous snapshot under the same prompt, input files, model, reasoning settings, tools, and attempt budget.
- Do not give first-run variants postmortem traps learned from earlier failures.
- Use the same pre-registered guards and assertions for every variant.
- Repeat cases only when measuring a rate; record the run count instead of treating one run as deterministic.
- Randomize case/trial blocks and variant order deterministically, and use the same paired seed for every variant in a block.
- Treat adapters as trusted local programs, not sandboxed code. They must run the evaluated agent in the request workspace, send only the request query to it, attest the requested skill isolation, never inspect suite semantics or labels, create no background descendants, and write only inside the run directory. Otherwise, treat the resulting metrics as untrusted.
- Record runner metadata and keep unavailable activation, catalog, or usage telemetry as `null`; never infer it from final-answer wording.
- Record the Git commit, dirty worktree/diff digest, harness hash, skill hashes, and resolvable runner-command file hashes with the result.
- Record any harness or environment deviation with the result.
