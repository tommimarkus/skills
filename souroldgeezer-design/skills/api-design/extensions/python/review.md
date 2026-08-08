# Extension: python review lane

Review classifications and carve-outs for [the Python ASGI / WSGI core](../python.md).

## Load condition

Load this file in Review mode. In Extract, load it only when the user explicitly
requests a debt or compliance verdict. For a narrow Lookup, load it only when
the question asks for a finding code or carve-out. Do not load it in Build.

## Smell codes

### High-confidence

- **`pyapi.HC-1`** — An ASGI `async def` request path directly calls known
  blocking I/O or CPU-heavy work without an async alternative or bounded
  offload. It stalls the event loop. *Layer:* static.
- **`pyapi.HC-2`** — Required side effect is delegated to an unawaited task,
  thread, timer, or in-memory queue after a serverless response or request
  completion instead of being durably accepted first. *Layer:* static +
  contract.
- **`pyapi.HC-3`** — Long-lived outbound client, connection pool, telemetry
  provider, or credential session is created for every request/invocation.
  *Layer:* static.
- **`pyapi.HC-4`** — Request-scoped state (claims, body, correlation data,
  mutable response data) is retained in a module global, process singleton, or
  reusable warm-instance object. *Layer:* static.
- **`pyapi.HC-5`** — Streaming ASGI response/async generator has no observable
  disconnect/cancellation cleanup or upstream close path; or it swallows
  cancellation and continues streaming. *Layer:* static.
- **`pyapi.HC-6`** — Deployment is serverless/adapter-shaped but the entrypoint
  starts a hosted listener, or deployment is hosted ASGI/WSGI but only exposes
  an incompatible serverless event handler. *Layer:* static + iac.
- **`pyapi.HC-7`** — Long-lived ASGI/WSGI service initializes lifecycle-owned
  clients/resources but has no shutdown/close path for them. *Layer:* static +
  runtime.
- **`pyapi.HC-8`** — An endpoint is added/changed while the generated OpenAPI
  artifact is stale, generation is nondeterministic/unreviewed, or no CI
  contract-drift check connects the declared authority to handlers. *Layer:*
  static + contract.

### Low-confidence

- **`pyapi.LC-1`** — Python version or dependency lock/runtime declaration is
  absent for a deployable API. Libraries may legitimately defer that decision.
  *Layer:* static + iac.
- **`pyapi.LC-2`** — A long-lived WSGI/ASGI service has lifecycle-relevant
  dependencies but lifecycle behavior is owned by opaque third-party wiring;
  inspect deployment/runtime evidence before concluding shutdown is missing.
  *Layer:* static + runtime.
- **`pyapi.LC-3`** — Streaming is proposed through a serverless adapter without
  evidence that the selected platform preserves streaming and disconnect
  signals. *Layer:* static + runtime + iac.
- **`pyapi.LC-4`** — Blocking work is offloaded, but executor capacity, queue
  wait, and deadline behavior are not bounded/documented. *Layer:* static.

### Positive signals

- **`pyapi.POS-1`** — Hosted ASGI application uses a lifecycle boundary to
  initialize and close shared clients/telemetry.
- **`pyapi.POS-2`** — Hosted WSGI deployment documents gateway drain/shutdown
  and response-iterator cleanup.
- **`pyapi.POS-3`** — Serverless adapter/handler does not start a listener and
  makes required work durable before success response.
- **`pyapi.POS-4`** — Async request work uses async clients or bounded offload,
  with deadlines and cancellation-aware cleanup.
- **`pyapi.POS-5`** — Request context is isolated from process/warm-instance
  state and structured trace fields propagate outbound.
- **`pyapi.POS-6`** — Streaming has disconnect/cancellation cleanup and closes
  upstream resources.
- **`pyapi.POS-7`** — OpenAPI 3.1 artifact is deterministic, operation IDs are
  stable, and CI checks lint/diff/handler conformance.

## Carve-outs

Do not flag the following:

- A short, explicitly bounded sync-only call offloaded from an ASGI handler
  with timeout/concurrency controls; this is not `pyapi.HC-1`. A worker remains
  the default for CPU-heavy or durable work.
- Process- or warm-instance-scope clients that are immutable or concurrency
  safe, initialized once, and closed by lifecycle ownership; this is not
  `pyapi.HC-3` or `pyapi.HC-4`.
- A serverless platform's documented response-lifetime primitive when its
  delivery and shutdown guarantees satisfy the required effect. Record the
  platform evidence; otherwise use durable enqueue.
- A WSGI iterable with an idempotent resource-release `close()` path even when
  it cannot observe an ASGI-style disconnect event; this is not `pyapi.HC-5`.
- A checked-in, hand-authored OpenAPI document when CI validates it against
  handlers and reviews its diffs; generation is optional, contract drift
  prevention is not.

Security findings such as authentication mistakes, secret handling, unsafe
deserialization, and dependency vulnerability assessment belong to
`devsecops-audit`; do not relabel them as Python API lifecycle findings.
