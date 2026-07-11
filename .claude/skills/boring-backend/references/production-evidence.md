# Production Evidence

Read this file only for explicitly requested environment-specific production evidence.

## Permission Gate

Default to read-only inspection of existing dashboards, logs, traces, plans, canary results, and drill reports within current access.

Treat load or failure injection, restore or rollback rehearsal, and any mutating or disruptive action as invasive. Before execution, confirm the target environment, affected users/data/services, expected impact, time/rate/concurrency/blast-radius limits, stop thresholds, and recovery/rollback conditions. Then obtain separate explicit approval; a general production-evidence request is not execution approval.

Stop on a threshold breach, unexpected impact, loss of observability, or uncertain recovery, and execute the agreed recovery path.

## Output Contract

Report the target and claim, permission/approval basis, sources or actions, captured outputs, limits, stop conditions, recovery/rollback status, and gaps. Do not expose secrets or unnecessary production data.

## Boundary

Real DB integration is integration evidence, not production evidence. Without an explicit environment-specific request, implement or review local and risk-specific controls and name production gaps. Do not turn ordinary CRUD work into load testing.
