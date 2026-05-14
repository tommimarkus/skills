# API Design Red Flags

Load before final output in Build and Review. If any matching item remains in
added code, new IaC, emitted contract, or the reviewed scope, stop and fix or
report it as a finding.

- Secret in app-settings literals, committed `local.settings.json`, committed
  `.env*`, connection string literal, access key literal, or token in a URL.
- Per-invocation HTTP/data client construction inside a handler body.
- Anonymous or key-only authorization on an endpoint that handles non-public
  data.
- Error path returns string, HTML, or plain JSON instead of
  `application/problem+json`.
- Retryable POST mutation lacks an `Idempotency-Key` or equivalent replay guard.
- `429` response lacks `Retry-After` or extension-specific retry metadata
  mapping.
- Outbound HTTP/dependency call lacks trace propagation.
- Workflow/orchestration runtime is used where queue-backed `202` plus polling
  would satisfy the force with less coupling.
- Long-running work stays inside a synchronous HTTP request past known runtime
  timeout.
- Added endpoint has no OpenAPI 3.1 contract entry.
- CORS wildcard is used on an authenticated endpoint.
- Loaded extension high-confidence smell remains in added code or new IaC.
- Large upload/download streams through the API runtime without a documented
  memory and timeout budget.
- Static review claims p95, cold-start, error-rate, RU charge, storage latency,
  or dependency latency as verified.
- Preview/non-baseline platform feature is used without feature detection,
  fallback, or documented preview dependency.
