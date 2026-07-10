# Severity

Read this file only when assigning P0-P4 grades to risks or findings, or making an explicit release/blocking judgment.

| Grade | Meaning |
|---|---|
| P0 | A defect in a supplied or required artifact prevents build, run, import, or test collection |
| P1 | Security/data-integrity failure, or a credible direct path to data loss/corruption, security/privacy exposure, material financial loss, availability/SLO breach, unbounded spend, or irreversible rollout |
| P2 | Client-breaking API, status, schema, or semantic contract failure without P1 impact |
| P3 | Maintainability, package structure, undue complexity, or unmeasured performance, operations, migration, or compatibility risk without proven P1/P2 impact |
| P4 | Naming, style, or verbosity |

- Rank P0/P1/P2 ahead of architecture preference.
- In pseudo-only review, mark build/test evidence unavailable. Unavailable environments, tools, dependencies, services, or credentials are evidence gaps, not P0.
- A domain catalog may narrow impact assumptions, but do not raise severity without evidence for the corresponding impact.
