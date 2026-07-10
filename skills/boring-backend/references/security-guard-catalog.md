# Security Guard Catalog

Read this file only when the task touches auth, roles, ownership, public input, field binding, secrets, logs, CORS/TLS, user-controlled URLs, or third-party API responses.

## Implementation Lens

| Risk | Implement |
|---|---|
| Object authorization | Enforce caller/tenant scope at a trusted server-side boundary for every object read, update, delete, and state transition. Scope list/search queries before retrieval; never rely on UI filtering or post-fetch filtering for authorization. |
| Property authorization | Use request/response DTO allowlists. Do not bind public input directly onto persistence entities when fields include role, owner, price, balance, status, internal notes, or audit fields. |
| Function authorization | Protect privileged routes and admin functions independently from UI visibility. Tests should call the endpoint directly with insufficient privileges. |
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
- Do token failures and auth fallback attempts return the intended status?
- Are secrets or sensitive properties exposed in responses, query strings, logs, or errors?
- Does any endpoint fetch a user-supplied URL or trust a third-party response without validation?
- Does untrusted input reach SQL, NoSQL, search, path, header, template, expression, command, or shell interpreters unsafely?
- Are CORS, debug endpoints, verbose errors, and legacy endpoints explicitly safe or out of scope?
- Missing auth or ownership is P1 for public, multi-user, or protected APIs; otherwise require a trusted/local-only assumption.
