# Production Evidence

Read this file only for explicitly requested environment-specific L4 evidence.

## Permission Gate

Default to read-only inspection of existing dashboards, logs, traces, plans, canary results, and drill reports within current access.

Treat load or failure injection, restore or rollback rehearsal, and any mutating or disruptive action as invasive. Before execution, confirm the target environment, affected users/data/services, expected impact, time/rate/concurrency/blast-radius limits, stop thresholds, and recovery/rollback conditions. Then obtain separate explicit approval; a general L4 request is not execution approval.

Stop on a threshold breach, unexpected impact, loss of observability, or uncertain recovery, and execute the agreed recovery path.

## Output Contract

Report the target and claim, permission/approval basis, sources or actions, captured outputs, limits, stop conditions, recovery/rollback status, and gaps. Do not expose secrets or unnecessary production data.

## Boundary

Real DB integration remains L2. Without an environment-specific L4 request, implement or review L2/L3 guards and name L4 gaps. Do not turn ordinary CRUD work into load testing.
