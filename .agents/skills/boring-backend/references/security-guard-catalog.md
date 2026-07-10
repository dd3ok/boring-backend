# Security Guard Catalog

Read this file only when the task touches authentication/authorization, roles, ownership, sensitive business flows, public field binding, server-owned fields, secrets, logs, CORS/TLS, user-controlled URLs, or third-party API responses.

## Implementation Lens

| Risk | Implement |
|---|---|
| Object authorization | Enforce caller/tenant scope at a trusted server-side boundary for every object read, update, delete, and state transition. Scope list/search queries before retrieval; never rely on UI filtering or post-fetch filtering for authorization. |
| Property authorization | Use request/response DTO allowlists. Do not bind public input directly onto persistence entities when fields include role, owner, price, balance, status, internal notes, or audit fields. |
| Function authorization | Protect privileged routes and admin functions independently from UI visibility. Tests should call the endpoint directly with insufficient privileges. |
| Sensitive business-flow abuse (OWASP API6:2023) | Identify business-specific high-value flows that valid users or automation can abuse, such as purchase/reservation, signup/referral, transfer, posting, or resource consumption. Select proportional server-side controls from the threat and impact: actor/resource limits, velocity or state rules, anti-automation or step-up controls, and abuse telemetry. Do not require every mechanism or rely on UI friction alone. |
| Auth failure mode | Invalid, expired, malformed, missing, or tampered credentials fail closed with the expected 401/403. Disable unused framework auth fallbacks or prove they cannot authenticate protected APIs. |
| Sensitive data exposure | Keep secrets, tokens, passwords, PII, stack traces, internal paths, and raw upstream payloads out of API responses and logs. Prefer stable non-sensitive IDs in logs. |
| User-controlled URL fetch | Treat URL-fetching APIs as SSRF risk. Prefer allowlisted hosts/schemes, block private/link-local/metadata destinations, and apply timeout and size limits. |
| Unsafe API consumption | Validate third-party API responses like user input. Enforce schema, size, content type, auth, TLS, timeout, and failure handling before trusting upstream data. |
| Untrusted input to interpreters | Parameterize SQL/NoSQL/search queries. Validate path, header, template, expression, and command inputs before passing them to interpreters or shell/process APIs. |
| Security misconfiguration | Avoid permissive CORS, verbose production errors, unnecessary HTTP methods, default credentials, missing TLS assumptions, and exposed debug/admin endpoints. |
| API inventory | Name deprecated, debug, test, or versioned endpoints that remain exposed. Untracked endpoints are a review finding when security behavior differs. |

## Review Lens

- Can a caller access another user's object by changing an ID, or see out-of-scope rows through a read/list/search query?
- Can public input set server-owned fields by mass assignment?
- Can a non-admin call an admin function by skipping the UI?
- Can valid users or automation abuse a sensitive flow through replay, concurrency, hoarding, enumeration, or quota evasion?
- Do token failures and auth fallback attempts return the intended status?
- Are secrets or sensitive properties exposed in responses, query strings, logs, or errors?
- Does any endpoint fetch a user-supplied URL or trust a third-party response without validation?
- Does untrusted input reach SQL, NoSQL, search, path, header, template, expression, command, or shell interpreters unsafely?
- Are CORS, debug endpoints, verbose errors, and legacy endpoints explicitly safe or out of scope?
- For public, multi-user, or protected APIs, report missing authentication, authorization, or ownership enforcement as a high-impact security-boundary failure; otherwise require an explicit trusted/local-only assumption.
