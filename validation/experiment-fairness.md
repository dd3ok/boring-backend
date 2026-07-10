# Experiment Fairness

Use this only when maintaining or evaluating the boring-backend skill. It is not runtime guidance.

- Start every run from a clean context.
- Use a new or empty isolated workspace outside the skill repository for execution and results. Copy only the selected candidate skill into an isolated skill root; do not load it through a symlink or path back to this checkout. Deny the evaluated process read access to the source repository and grader store. If the runtime cannot enforce that boundary, record the isolation gap and do not count the run as clean. Do not commit generated results, traces, transcripts, or agent workspaces.
- For behavior cases, stage only the files listed in `input_files`, send only `prompt` to the evaluated agent, and keep `expected_behavior`, case labels, and grader instructions outside agent context.
- For trigger cases, send only `query` to the activation surface and keep `should_trigger`, `rationale`, case labels, and grader instructions outside agent context.
- Respect the requested mode and workspace boundary. Design and review cases do not edit; implementation cases write only in the assigned workspace; production actions still require explicit approval.
- Grade only observable output, artifacts, command evidence, and vendor-provided traces or telemetry. Treat unrun tests and unavailable environments or production evidence as gaps, not success.
- For review fixtures, verify input hashes before and after the run.
- Disable every discoverable same-name skill except the selected variant and record how isolation was verified.
- Compare the current skill with no skill or a previous snapshot under the same prompt, input files, model, reasoning settings, tools, and attempt budget.
- Do not give first-run variants postmortem traps learned from earlier failures.
- Use the same pre-registered guards and assertions for every variant.
- Repeat cases only when measuring a rate; record the run count instead of treating one run as deterministic.
- Randomize case and variant order reproducibly. Only when the vendor supports an agent seed, give each paired variant the same agent seed; otherwise record the seed as unsupported or `null` and do not claim seeded determinism.
- Record the result schema version; grader name, version, and configuration; vendor and model identifier/version or snapshot; tool and runner versions; Git commit; skill and input hashes; and environment deviations with every result set.
- Leave unavailable activation, catalog, or usage telemetry unknown; never infer it from final-answer wording.
