# Extension: python build lane

Implementation detail for [the Python ASGI / WSGI core](../python.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

## Stack-specific primitives

### Hosted ASGI

- Deploy one ASGI callable behind a selected ASGI server and reverse proxy or
  platform router. Keep listener configuration in the selected host/deployment
  contract; do not make the application choose an unrequested server.
- Use the ASGI lifespan protocol when the server supports it to initialize
  process-scoped clients, pools, telemetry, and configuration once, then close
  or flush them on shutdown. Startup failure should fail readiness rather than
  leave a partly initialized application accepting traffic.
- An `async def` handler must not call blocking filesystem, network, database,
  or CPU-heavy work directly. Use an async client where available; otherwise
  offload a short, bounded operation with an explicit timeout and a bounded
  executor/concurrency policy. CPU-heavy or unbounded work belongs in a worker.
- For streams, stop reading when the client disconnects or cancellation arrives,
  close upstream resources in `finally`, and let cancellation propagate after
  cleanup. A response body must have an explicit byte/time policy.

### Hosted WSGI

- Deploy one WSGI callable behind a selected WSGI gateway and reverse proxy or
  platform router. WSGI's synchronous callable contract is not an excuse to
  run unbounded work in the request; use the core 202-and-worker pattern for
  durable or long-running effects.
- Put reusable clients/pools in application/process ownership, not request
  construction. Give the gateway a documented graceful-shutdown sequence that
  drains requests and closes those resources.
- Streaming iterables must release files, cursors, and upstream responses when
  iteration ends early. Use iterator `close()` where the gateway calls it, and
  make cleanup idempotent for abnormal termination.

### Serverless handlers and adapters

- Use the platform's documented Python handler or HTTP adapter as the deployed
  entrypoint. Reuse immutable configuration and safe clients across warm
  invocations only; auth claims, request bodies, correlation context, and
  response state remain invocation-scoped.
- An ASGI/WSGI adapter translates platform events; it does not call a hosted
  listener. Check response buffering and streaming support against the chosen
  platform before promising streaming semantics.
- Before returning `202` or another success response, write required work to a
  durable queue, workflow, or transactionally recorded outbox. Do not rely on
  a detached coroutine, thread, timer, or process after the invocation returns
  unless the platform documents a suitable lifetime primitive and its delivery
  contract satisfies the requirement.

### Contract and observability

- Initialize logging and telemetry at process startup/lifespan or documented
  warm-instance initialization, not per request. Carry `traceparent`, route,
  operation identifier, and authenticated subject through request-scoped
  context; flush exporters during hosted shutdown where the provider requires it.
- Choose one OpenAPI 3.1 authority: a reviewed source document or a generator
  driven by declared routes/schemas. Pin generator inputs, normalize ordering,
  keep `operationId` stable, publish the generated output at a stable path, and
  make CI lint, diff, and contract-test it. Generation is not proof that a
  handler still conforms.

## Stack-specific patterns

### `pyapi.PAT-hosted-asgi` `[Hosted ASGI]`

Hosted ASGI API: deployment starts the selected ASGI server; application
lifespan validates configuration, initializes shared clients and telemetry,
installs the common problem-details boundary, exposes readiness only after
startup, and closes clients/exporters during graceful shutdown. Maps §3.5,
§3.14, §3.15, §3.16.

### `pyapi.PAT-hosted-wsgi` `[Hosted WSGI]`

Hosted WSGI API: deployment starts the selected WSGI gateway; application
initialization creates shared resources, the gateway has a documented drain and
shutdown path, and response iterables close resources on complete or abandoned
iteration. Maps §3.5, §3.14, §3.15, §3.16.

### `pyapi.PAT-serverless-adapter` `[Serverless]` `[Adapter]`

Serverless HTTP handler or ASGI/WSGI adapter validates the platform request,
creates invocation-scoped context, calls the same API service boundary used by
hosted code, returns problem+json on errors, and never starts a listener. Maps
§3.5, §3.14, §3.15.

### `pyapi.PAT-lifespan-resources` `[Hosted ASGI]`

Lifespan startup builds process-scoped clients/pools and telemetry; shutdown
first stops readiness/acceptance, then drains work as the host allows, closes
clients, and flushes telemetry. Request data is never stored in these shared
objects. Maps §3.14, §3.16.

### `pyapi.PAT-bounded-blocking-offload` `[Hosted ASGI]`

An async handler uses asynchronous libraries first. When a short legacy call
cannot be replaced, it sends that call to a bounded executor with a deadline,
propagates cancellation intent where the dependency supports it, and records
queue/wait time. It does not use unbounded default offload for sustained work.
Maps §2.6, §3.9, §3.14.

### `pyapi.PAT-durable-async-work` `[Both]`

Mutation records/enqueues durable work before responding `202 Accepted` with a
status `Location`; a worker or workflow performs the job and updates that
status resource. Idempotency covers retryable acceptance. Maps §3.6, §3.9,
§5.3.

### `pyapi.PAT-cancellation-aware-stream` `[Hosted ASGI]`

Streaming response watches for disconnect/cancellation, applies byte and time
limits, and closes its upstream iterator/file/connection in `finally` before
re-raising cancellation. The equivalent WSGI iterator has an idempotent close
path for early termination. Maps §3.12, §3.14.

### `pyapi.PAT-stable-openapi` `[Both]`

One OpenAPI 3.1 authority produces a deterministic artifact with stable
operation identifiers. CI lints the artifact, rejects an unreviewed generated
diff, and contract-tests handlers; release output publishes the approved spec.
Maps §2.1, §4.5.
