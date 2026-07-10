# Experiment Fairness

Use this only when maintaining or evaluating the boring-backend skill. It is not runtime guidance.

- Start every run from a clean context.
- Use an isolated workspace outside the skill repository. Disable every discoverable same-name skill except the selected variant and record how isolation was verified.
- Compare the current skill with no skill or a previous snapshot under the same prompt, input files, model, reasoning settings, tools, and attempt budget.
- Do not give first-run variants postmortem traps learned from earlier failures.
- Use the same pre-registered guards and assertions for every variant.
- Repeat cases only when measuring a rate; record the run count instead of treating one run as deterministic.
- When running repeated comparisons, randomize case and variant order reproducibly and give each paired variant the same seed.
- Record the vendor, model, tool versions, Git commit, skill hash, and environment deviations with the result.
- Leave unavailable activation, catalog, or usage telemetry unknown; never infer it from final-answer wording.
