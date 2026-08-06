# Extension: nodejs review lane

Review classifications and carve-outs for [the nodejs core](../nodejs.md).

## Load condition

Load this file in Review mode. In Extract, load it only when the user explicitly
requests a debt or compliance verdict. For a narrow Lookup, load it only when
the question asks for a finding code or carve-out. Do not load it in Build.

## Smell codes

### High-confidence

- **`nodejs.HC-1`** — `app.listen(...)`, `server.listen(...)`, or `fastify.listen(...)` in a serverless handler entrypoint. Serverless platforms own the listener. *Layer:* static.
- **`nodejs.HC-2`** — Hosted raw `node:http` / framework listener exposed without request/header timeout configuration and without a documented reverse-proxy contract. *Layer:* static + iac.
- **`nodejs.HC-3`** — JSON, form, or raw body parsing without an explicit size limit on a public route. *Layer:* static.
- **`nodejs.HC-4`** — Error path returns bare JSON / string / HTML instead of `application/problem+json`. *Layer:* static + contract.
- **`nodejs.HC-5`** — POST mutation without `Idempotency-Key` support or natural-key dedup when clients may retry. *Layer:* static + contract.
- **`nodejs.HC-6`** — 429 emitted without `Retry-After`. *Layer:* static.
- **`nodejs.HC-7`** — Secret literal in source, committed `.env*`, committed serverless local settings, or token in query string. *Layer:* static.
- **`nodejs.HC-8`** — Public non-health endpoint with no authentication / authorization middleware and no explicit public-read-only declaration. *Layer:* static + contract.
- **`nodejs.HC-9`** — Unawaited promise, timer, or in-memory queue used for required work after a serverless response returns. *Layer:* static.
- **`nodejs.HC-10`** — Callback-style Lambda handler on a Node.js runtime where the official AWS docs require or recommend async handlers for the target version. *Layer:* static.
- **`nodejs.HC-11`** — Per-request construction of expensive clients (`new Agent`, DB client, queue client, OpenTelemetry provider) inside handler logic. *Layer:* static.
- **`nodejs.HC-12`** — Missing OpenAPI document / generator for an added endpoint. *Layer:* static + contract.
- **`nodejs.HC-13`** — Boundary validation absent for request body/query/params on a mutation or public endpoint. *Layer:* static + contract.
- **`nodejs.HC-14`** — Webhook signature checked after JSON parsing, compared with `===`, or accepted without timestamp freshness. *Layer:* static.
- **`nodejs.HC-15`** — Hosted API lacks graceful shutdown handling while using a long-lived listener. *Layer:* static.

### Low-confidence

- **`nodejs.LC-1`** — No `engines.node` or deployment runtime declaration. Context-dependent for libraries, but API services should declare it. *Layer:* static.
- **`nodejs.LC-2`** — No AsyncLocalStorage or equivalent request-context mechanism in an API with structured logging. *Layer:* static.
- **`nodejs.LC-3`** — Serverless adapter wraps a full hosted app for a small endpoint set where native handlers would be simpler. *Layer:* static.
- **`nodejs.LC-4`** — Hosted public API rate limiting appears only in application middleware with no edge/proxy evidence. *Layer:* static + iac.
- **`nodejs.LC-5`** — Multiple package managers / lockfiles in one deployable service. *Layer:* static.

### Positive signals

- **`nodejs.POS-1`** — `engines.node` or platform runtime targets a supported Node.js version and CI uses the matching lockfile.
- **`nodejs.POS-2`** — Problem+json helper used by every framework error hook.
- **`nodejs.POS-3`** — AsyncLocalStorage-backed request context with trace/correlation fields.
- **`nodejs.POS-4`** — OpenTelemetry initialized once at startup / module load, with exporter shutdown in hosted apps.
- **`nodejs.POS-5`** — OpenAPI 3.1 source is linted and contract-tested.
- **`nodejs.POS-6`** — Hosted listener has explicit timeouts, health checks, reverse proxy, and graceful shutdown.
- **`nodejs.POS-7`** — Serverless handler enqueues long-running work before returning 202 + `Location`.
- **`nodejs.POS-8`** — Idempotency replay cache on retryable POST mutations.
- **`nodejs.POS-9`** — Body parser limits and direct-to-object-store upload for large payloads.
- **`nodejs.POS-10`** — Webhook receiver verifies raw-body signatures with timestamp freshness and constant-time compare.

## Carve-outs

Do not flag the following:

- Module-scope singleton clients in serverless code — warm invocation reuse is
  expected when the object is not request-specific.
- Framework default body limits when the framework documents a bounded default
  and the route does not override it upward; still record the cap.
- `Response.json(...)` / `res.json(...)` on successful 2xx responses. The
  problem+json requirement applies to error paths.
- Public health, readiness, liveness, and static metadata endpoints without
  auth when they return no private data and are rate-limited.
- Next.js Route Handlers / Pages API routes when `nextjs.md` also loads; apply
  Next-specific smells for those framework boundaries.
