# Experiment Fairness

Use this only when maintaining or evaluating the boring-backend skill. It is not runtime guidance.

- Start every run from a clean context and a new or empty workspace outside the skill repository. Copy only the selected candidate skill; do not use a symlink or path back to this checkout. Keep source and grader data outside the evaluated process, and record any isolation gap.
- For behavior cases, stage only the files listed in `input_files`, send only `prompt` to the evaluated agent, and keep `expected_behavior`, case labels, and grader instructions outside agent context.
- For trigger cases, send only `query` to the activation surface and keep `should_trigger`, `rationale`, case labels, and grader instructions outside agent context.
- Respect the requested mode and workspace boundary. Design and review cases do not edit; implementation cases write only in the assigned workspace; production actions still require explicit approval.
- Grade only observable output, artifacts, command evidence, and vendor-provided traces or telemetry. Treat unrun tests and unavailable environments or production evidence as gaps, not success.
- For review fixtures, verify input hashes before and after the run.
- Disable every discoverable same-name skill except the selected variant and record how isolation was verified.
- Compare the current skill with no skill or a previous snapshot under the same prompt, input files, model, reasoning settings, tools, and attempt budget.
- Repeat cases only when measuring a rate; record the run count instead of treating one run as deterministic.
- Record the runner, vendor/model, Git commit, skill/input hashes, run count, and environment deviations with each result set.
- Leave unavailable activation, catalog, or usage telemetry unknown; never infer it from final-answer wording.
- Keep generated results, traces, transcripts, and workspaces outside the repository.
