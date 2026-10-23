# API Design Red Flags

Use relevant items before claiming the affected change is ready. Check the
actual project contract and consequences: reference differences alone are not
findings. Fix within authority or report the risk; read-only Review continues
its remaining analysis rather than pausing for migration scope.

- Secret in app-settings literals, committed `local.settings.json`, committed
  `.env*`, connection string literal, access key literal, or token in a URL.
- Per-invocation construction of an unpooled HTTP handler, dispatcher, or expensive data pool; or a singleton/concurrently shared `DbContext`.
- HTTP-to-storage N+1 round trips, unnecessary transfer, or unbounded intermediate materialization on a concrete access path.
- Anonymous or key-only authorization on an endpoint that handles non-public
  data.
- Error behavior breaks the declared stable contract or exposes secrets/internal
  traces. A compatible established JSON envelope is not itself a red flag.
- Retryable POST mutation lacks an `Idempotency-Key` or equivalent replay guard.
- `429` response lacks `Retry-After` or extension-specific retry metadata
  mapping.
- A consequential distributed failure path loses correlation required for
  actual support or operational needs.
- Workflow/orchestration runtime is used where queue-backed `202` plus polling
  would satisfy the force with less coupling.
- Long-running work stays inside a synchronous HTTP request past known runtime
  timeout.
- Added endpoint has no reviewable compatible contract, or its declared contract
  source/generation is stale or contradicts handler behavior.
- CORS wildcard is used on an authenticated endpoint.
- Loaded extension high-confidence smell remains in added code or new IaC.
- Large upload/download streams through the API runtime without a documented
  memory and timeout budget.
- Static review claims p95, cold-start, error-rate, RU charge, storage latency,
  or dependency latency as verified.
- Preview/non-baseline platform feature is used without feature detection,
  fallback, or documented preview dependency.
