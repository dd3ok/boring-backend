# Experiment Fairness

Use this only when maintaining or evaluating the boring-backend skill. It is not runtime guidance.

- Start every run from a clean context.
- Compare the current skill with no skill or a previous snapshot under the same prompt, input files, model, reasoning settings, tools, and attempt budget.
- Do not give first-run variants postmortem traps learned from earlier failures.
- Use the same pre-registered guards and assertions for every variant.
- Repeat cases only when measuring a rate; record the run count instead of treating one run as deterministic.
- Record any harness or environment deviation with the result.
