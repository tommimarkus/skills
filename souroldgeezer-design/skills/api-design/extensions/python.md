# Extension: Python ASGI / WSGI HTTP APIs

Stack-specific additions to the `api-design` skill for Python HTTP APIs. The
core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md)
remains framework-neutral; this extension adds Python gateway, lifecycle, and
serverless-adapter mechanics without requiring a particular framework or
application server.

Source anchors used for this extension:

- Python `asyncio` development guidance
  <https://docs.python.org/3/library/asyncio-dev.html> and coroutine/task
  guidance <https://docs.python.org/3/library/asyncio-task.html>.
- Python's WSGI specification, [PEP 3333](https://peps.python.org/pep-3333/).
- [ASGI 3.0 main specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
  and [lifespan protocol](https://asgi.readthedocs.io/en/latest/specs/lifespan.html).
- [AWS Lambda Python handler guidance](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
  and [Azure Functions Python developer reference](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python).

Re-check these primary sources when a deployed Python version, gateway,
serverless adapter, or lifetime guarantee is load-bearing.

## Name and detection signals

Load this extension when any of the following match:

- `pyproject.toml`, `requirements.txt`, `requirements/*.txt`, `setup.cfg`,
  `setup.py`, `Pipfile`, `poetry.lock`, or `uv.lock` at the target root.
- Python HTTP entrypoints or gateway call signatures: `async def app(scope,
  receive, send)`, `def application(environ, start_response)`,
  `start_response`, `lifespan.startup`, `lifespan.shutdown`, or an adapter that
  presents either callable to a platform.
- Deployment configuration that runs a Python module/callable, exposes a
  Python HTTP process, or maps a Python handler to a serverless HTTP trigger.
- Serverless manifests or source imports for an AWS Lambda Python handler,
  Azure Functions Python HTTP trigger, or another platform's Python HTTP
  adapter.

Do not load from a Python library, batch job, notebook, CLI, or data pipeline
alone. This extension owns the HTTP surface, not general Python design.

## Hosting-model surface

Rules are tagged `[Hosted ASGI]`, `[Hosted WSGI]`, `[Serverless]`, `[Adapter]`,
or `[Both]`.

- **`[Hosted ASGI]`** — a long-lived process where an ASGI server invokes the
  application. The deployment owns the process manager and network edge; the
  application owns its callable, lifespan resources, request cancellation,
  and graceful resource shutdown.
- **`[Hosted WSGI]`** — a long-lived WSGI application behind a WSGI gateway.
  The synchronous request model does not create an event-loop contract; bounded
  request work, resource lifecycle, and graceful shutdown still apply.
- **`[Serverless]`** — a platform invokes a Python handler and owns the
  listener, invocation deadline, and instance lifecycle. The application owns
  the documented handler/adapter contract and must make required work durable
  before returning.
- **`[Adapter]`** — an ASGI or WSGI callable is translated to a serverless
  event/response model. The adapter is the deployed entrypoint; a hosted
  listener is not started by the function.
- **`[Both]`** — applies to ASGI, WSGI, and serverless shapes as applicable.

## Mode lanes

This core file is the always-loaded Python stack surface. Load exactly one mode
lane when the task requires it:

- **Build:** read [`python/build.md`](python/build.md) for detailed primitives
  and `pyapi.PAT-*` implementation patterns.
- **Review:** read [`python/review.md`](python/review.md) for `pyapi.HC-*`,
  `pyapi.LC-*`, and `pyapi.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane
  only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most
  the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Python version and dependency-lock contract
- ASGI callable, `scope` / `receive` / `send`, and lifespan support
- WSGI callable, `environ` / `start_response`, and gateway configuration
- Serverless HTTP handler and ASGI/WSGI adapter boundary
- Process-scope clients, request-scoped context, and shutdown hooks
- Async cancellation, streaming cleanup, and bounded blocking offload
- Contract source and deterministic OpenAPI generation

Detailed signatures and implementation guidance live in
[`python/build.md`](python/build.md).

## Shared safety invariants

- Match one hosting model to its entrypoint: hosted ASGI/WSGI owns no
  serverless handler contract, and a serverless adapter never starts a listener.
- In ASGI request paths, await nonblocking I/O. Offload only bounded blocking
  work with a defined concurrency and deadline; move durable work to a queue or
  worker before returning `202`.
- Initialize reusable clients and telemetry once per process or documented warm
  instance, keep request state request-scoped, and close lifecycle-managed
  resources on shutdown.
- Treat disconnect and cancellation as normal streaming paths: release the
  upstream iterator/file/connection in `finally`, propagate cancellation after
  cleanup, and bound stream time and bytes.
- Keep OpenAPI 3.1 generation repeatable: one declared contract source,
  stable operation identifiers, deterministic inputs/order, and CI that fails
  on an unreviewed generated-contract diff or code/contract mismatch.
- Preserve core HTTP semantics. Delegate code-level security review and secure
  implementation choices to `devsecops-audit`.

## Project assimilation (Python-specific)

Run this after the core framework-neutral discovery pass; results feed into the
assimilation footer.

1. **Python and dependency contract** — inspect `pyproject.toml`, interpreter
   constraints, lockfiles, containers, and platform runtime declarations.
   Record the deployed Python version and deterministic install path.
2. **Gateway and entrypoint** — locate ASGI callable, WSGI callable, hosted
   gateway command, serverless handler, or adapter. Record `[Hosted ASGI]`,
   `[Hosted WSGI]`, `[Serverless]`, `[Adapter]`, or a mixed surface.
3. **Listener ownership** — inspect startup commands, container command, IaC,
   and handler wiring. Record whether the platform or the application listener
   owns the socket; do not infer this from imports alone.
4. **Lifecycle and clients** — locate lifespan/startup/shutdown hooks, process
   clients, pools, telemetry providers, and client close methods. Distinguish
   process reuse from mutable request state.
5. **Async and blocking boundaries** — inspect `async def` handlers for direct
   blocking calls, executor/thread offload, concurrency limits, deadlines, and
   cancellation propagation.
6. **Streaming** — inspect response iterators/generators, disconnect handling,
   `finally` cleanup, upstream cancellation/close, and time/byte limits.
7. **Background work** — locate queues/workers or platform lifetime APIs.
   Record whether required effects are acknowledged only after durable enqueue.
8. **Contract source** — locate checked-in OpenAPI, generator configuration,
   route/schema sources, generated artifacts, and CI diff/contract tests.
9. **Observability** — inspect startup telemetry, structured request context,
   `traceparent` propagation, and shutdown flush behavior.

### Mapping reference defaults to Python idioms

| Reference default | Python idiom |
|---|---|
| §3.5 problem+json | Shared error boundary producing `application/problem+json` |
| §3.9 async 202 | Persist/enqueue work before `202` + `Location`; worker performs it |
| §3.14 observability | Process-start telemetry, request-scoped structured fields, W3C trace propagation |
| §3.15 hosting | ASGI server, WSGI gateway, or serverless adapter selected explicitly in deployment wiring |
| §3.16 data access | Process/warm-instance client or pool, closed through lifecycle ownership |
| §4.5 OpenAPI | Checked-in or deterministically generated OpenAPI 3.1 plus CI diff/contract checks |

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §3.5, §3.6, §3.7, §3.9, §3.10, §3.11, §3.12,
§3.14, §3.15, §3.16, §4.5, §5.3, §5.5b, §5.6, §5.8, §5.9, §5.10, §5.12, §6,
§7.
