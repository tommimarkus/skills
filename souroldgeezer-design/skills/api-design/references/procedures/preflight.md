# API Design Preflight

Load for Build, Extract, and Review.

Apply the listed defaults when the user has not supplied an answer. Ask only when a default would be unsafe, contradict supplied evidence, require destructive work, add cost, or materially change public behavior.

## Inputs And Defaults

| Input | Default when absent | Ask when |
|---|---|---|
| Consumer scope | Mixed consumers; use public-contract discipline with OpenAPI, stable errors, cursor pagination, and `Retry-After` on throttling | The endpoint is public or partner-facing and auth/contract exposure is unclear |
| Auth model | OAuth 2.0 / OIDC, maintained session/JWT middleware, or Entra ID + managed identity for Azure targets; no secrets in code | The request asks for anonymous, key-only, or shared-secret auth on non-public data |
| Framework / hosting stack | Detect from manifests and source; unknown stacks use the core reference only | Stack-specific runtime mechanics are required but no extension covers them |
| Hosting target and performance posture | Record evidence when present; do not invent runtime-specific SLO choices | The task asks for p95, cold-start, RU, storage-latency, or scale claims |
| Reliability posture | Idempotency on retryable mutations; safe retry and backoff on outbound calls | Idempotency conflicts with an explicit product contract |
| Observability target | Structured logs plus W3C `traceparent`; loaded extensions add runtime wiring | The user asks for a specific telemetry backend and no source/config evidence exists |
| Architecture pairing | In Review, auto-detect `docs/architecture/<feature>.dediren/`; in Build, update architecture only when the user opts in | More than one package could match the feature or the package is stale/invalid |

## Output Disclosure

Include a `Defaults applied:` line when any default materially shaped the result.
Name any question that was skipped because a safe default existed.
