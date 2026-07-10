# Handoff Reporting

Use this file for requested Boring Backend handoffs or multi-phase runs.

## Handoff Index

Create a handoff only when requested. Write it only when writes are allowed and only to the path designated by the user or workspace; otherwise return the requested handoff inline. Never invent a default path.

Use a compact envelope with:

- `task_id`
- `scope`
- `source_revision` (commit or stable artifact version, plus clean/dirty state and a diff or artifact digest when dirty)
- `path_base` (repository or workspace root)
- `claims`

Each `claims` entry contains:

- `claim_id`
- `claim_summary`
- `priority`
- `file:line`
- `command`
- `exit_code`
- `evidence_path`
- `gaps`

Store `file:line` and `evidence_path` relative to `path_base`.

Do not paste code, long logs, full reports, transcripts, or catalog text into the handoff. Store paths and short claim labels instead.

## Handoff-First Review

Before trusting claims, validate `task_id`, `scope`, `source_revision`, dirty-state digest, and `path_base` against the current task and checkout. Treat mismatches as gaps.

Start from the index and cited artifacts. Open fuller evidence only for unresolved material claims, prioritizing P0-P2; do not exclude a material P3/P4 claim solely by severity.

## Delta Output

Follow-up phases should reference `claim_id` values. Restate changed assumptions, disputed or material claims of any severity, unchecked evidence, and new commands/results; prioritize P0-P2.
