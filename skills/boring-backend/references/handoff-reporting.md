# Handoff Reporting

Use this file for requested Boring Backend handoffs or multi-phase runs.

## Handoff Index

When a run requests reports before review, write `reports/handoffs/<task>-first-handoff.json` as an index, not a narrative report.

Use compact entries with these fields:

- `claim_id`
- `claim_summary`
- `file:line`
- `evidence_path`
- `command_exit`
- `known_gap`

Do not paste code, long logs, full reports, transcripts, or catalog text into the handoff. Store paths and short claim labels instead.

## Handoff-First Review

Use handoff-first review when the handoff exists: start from the handoff index, then open cited files, evidence paths, and relevant catalogs.

Open the full first report only for a P0-P2 claim that cannot be resolved from the handoff index and cited evidence.

## Delta Output

Follow-up phases should reference `claim_id` values. Restate only changed assumptions, disputed claims, P0-P2 findings, unchecked evidence, and new commands/results.
