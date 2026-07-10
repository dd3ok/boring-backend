# Compatibility Governance Guard Catalog

Read this file only when the task touches public/internal APIs, OpenAPI/Proto/GraphQL schemas, SDKs, versioning, deprecation, request/response fields, enums, status codes, pagination/filtering/sorting, idempotency semantics, or documented client behavior.

## Implementation Lens

| Risk | Implement or Report |
|---|---|
| Contract source | Keep implementation, tests, and OpenAPI/Proto/GraphQL/docs aligned. If no contract exists, state compatibility evidence is limited. |
| Change classification | Classify additive, behavior-changing, breaking, or unknown changes before editing public or cross-team API behavior. |
| Request/response fields | Do not remove fields, change meaning/type/nullability, expose new sensitive fields, or make optional input required without versioning or migration notes. |
| Enum expansion | Treat enum additions as compatibility-sensitive unless clients are documented to handle unknown values. |
| Status and error shape | Preserve status codes, error codes, retry semantics, and validation/conflict/not-found mappings unless the contract requires change. |
| Pagination/filtering/sorting | Preserve defaults, cursor semantics, ordering stability, bounds, and filter meaning for existing clients. |
| Idempotency semantics | Preserve idempotency keys, request fingerprints, replay behavior, and conflict rules for retryable clients. |
| Client matrix | For significant changes, name old-client/new-server and new-client/old-server behavior or state why it is out of scope. |
| Deprecation/versioning | Use versioning, deprecation notes, migration windows, or compatibility shims when breaking change is intentional. |
| Contract tests | Prefer consumer-driven, schema, golden response, SDK, or API smoke tests for compatibility-sensitive paths. |

## Review Lens

- Could older clients fail, misinterpret data, retry unsafely, or silently receive different meaning?
- Are undocumented consumers or SDKs affected?
- Does the report distinguish additive changes from breaking semantic changes?
- Are contract docs, tests, and implementation aligned?
