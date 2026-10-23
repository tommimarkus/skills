# API Design Preflight

Load for Build, Extract, and Review.

Apply the listed defaults when the user and project contracts do not supply a compatible choice. Ask only when a material missing decision or authority prevents the next safe step; continue independent work and avoid unnecessary preflight questions.

## Inputs And Defaults

| Input | Default when absent | Ask when |
|---|---|---|
| Consumer scope | Inspect actual consumers; preserve compatible contracts and prefer OpenAPI, stable errors, bounded pagination, and usable retry guidance for a new surface | The endpoint is public or partner-facing and auth/contract exposure is unclear |
| Auth model | OAuth 2.0 / OIDC, maintained session/JWT middleware, or Entra ID + managed identity for Azure targets; no secrets in code | The request asks for anonymous, key-only, or shared-secret auth on non-public data |
| Framework / hosting stack | Detect from manifests and source; unknown stacks use the core reference only | Stack-specific runtime mechanics are required but no extension covers them |
| Hosting target and performance posture | Record evidence when present; do not invent runtime-specific SLO choices | The task asks for p95, cold-start, RU, storage-latency, or scale claims |
| Reliability posture | Idempotency on retryable mutations; safe retry and backoff on outbound calls | Idempotency conflicts with an explicit product contract |
| Observability target | Structured logs plus W3C `traceparent`; loaded extensions add runtime wiring | The user asks for a specific telemetry backend and no source/config evidence exists |
| Architecture pairing | In Review, auto-detect `docs/architecture/<feature>.dediren/`; in Build, update architecture only when the user opts in | More than one package could match the feature or the package is stale/invalid |

## Output Disclosure

Explain a material default or exception once when it helps the reader assess the result. Do not list skipped questions or routine defaults.
