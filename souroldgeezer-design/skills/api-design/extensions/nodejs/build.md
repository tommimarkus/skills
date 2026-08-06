# Extension: nodejs build lane

Implementation detail for [the nodejs core](../nodejs.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

## Stack-specific primitives

### Runtime and package surface

- **Supported Node.js version** — record `package.json#engines.node`, Docker
  base image, `.nvmrc`, `.node-version`, `volta`, and platform runtime config.
  Do not author new API code for an end-of-life runtime. If relying on native
  `fetch`, confirm the deployed Node.js version supports it per the official
  Node.js globals docs.
- **Module system** — record `"type": "module"`, `.mjs` / `.cjs`, and TypeScript
  transpilation output. Mixed ESM/CommonJS is allowed only when the entrypoint
  and deployment platform agree.
- **Lockfile** — `package-lock.json`, `npm-shrinkwrap.json`, `pnpm-lock.yaml`,
  `yarn.lock`, or `bun.lockb` should travel with the package manager used in
  CI. Node.js security guidance prefers deterministic install behavior (`npm ci`
  for npm projects).

### Hosted Node.js HTTP server

- **`http.createServer(...)` / framework listener** — if the app listens
  directly, configure `requestTimeout`, `headersTimeout`, body-size caps, and
  graceful shutdown. Node's `http` docs document parser limits such as
  `maxHeaderSize`, `headersTimeout`, `requestTimeout`, and `requireHostHeader`.
- **Reverse proxy contract** — public hosted APIs should sit behind nginx,
  Envoy, ALB, App Gateway, Front Door, API Management, or an equivalent edge
  that owns TLS, malformed request handling, request-size caps, rate limiting,
  and slow-client protection. Source-only review records this as `iac` /
  `security-tool` unless deployment config is present.
- **Graceful shutdown** — trap `SIGTERM` / `SIGINT`, stop accepting new
  requests, drain in-flight requests, close idle keep-alive connections when
  supported, and fail health checks before process exit.

### Serverless Node.js handler

- **Azure Functions Node.js v4** — code-centric `app.http("name", { methods,
  authLevel, handler })` with `@azure/functions`. Microsoft Learn ties the
  programming model version to the `@azure/functions` package and warns not to
  mix v3 `function.json` and v4 code-centric functions in the same function
  app.
- **AWS Lambda Node.js** — prefer async handlers
  `export const handler = async (event, context) => { ... }`. AWS docs state
  the invocation runs until the handler returns, exits, or times out; callback
  handlers are not the forward path for newer Node runtimes.
- **Module-scope reuse** — SDK clients, schema validators, compiled route
  tables, and OpenTelemetry providers may be initialized at module scope for
  warm invocations. Request-specific data, auth claims, body bytes, and
  correlation state must not live in module-level mutable state.
- **No post-response work unless the platform has a lifetime primitive** —
  enqueue durable work before returning 202, or use the platform's documented
  `waitUntil` / background-task primitive when one exists. Unawaited promises
  after return are lost on freeze, timeout, or scale-in.

### Request context and observability

- **`AsyncLocalStorage`** — Node's official context primitive for request-local
  state across async callbacks. Use `asyncLocalStorage.run(store, callback)` at
  the request boundary for `traceId`, `operationId`, and auth subject. Avoid
  `enterWith()` for request setup unless there is a specific reason.
- **OpenTelemetry** — initialize once during process startup or serverless
  module load; instrument inbound HTTP, outbound `fetch` / Undici / framework
  handlers, and database clients. Keep exporter shutdown in the hosted
  graceful-shutdown path.
- **Outbound HTTP** — native `fetch` is Undici-backed in current Node.js. Use
  `AbortSignal.timeout(...)` or equivalent request timeouts, honor
  `Retry-After`, propagate `traceparent`, and do not create a new Agent /
  dispatcher per request.
- **Structured logs** — use named fields (`operationId`, `traceId`, `route`,
  `subject`, `status`, `durationMs`), not interpolated strings. Every
  problem+json response includes a correlation field.

### HTTP contract helpers

- **Problem details middleware/helper** — one helper maps validation,
  authorization, domain, throttle, and unexpected errors to RFC 9457
  `application/problem+json`. Express / Koa / Nest middleware, Fastify error
  handlers, and Hono `onError` are all valid; route-local ad hoc JSON errors
  are not.
- **Boundary validation** — validate body, query, params, and headers before
  handler logic. JSON Schema / OpenAPI-aligned validation (Ajv, TypeBox,
  Zod-to-OpenAPI, Fastify schema, Nest pipes) is the usual Node.js shape.
- **Raw body access** — inbound webhooks verify signatures over the raw bytes
  before JSON parsing. Configure the framework body parser to expose raw bytes
  for that route only and keep an explicit size cap.
- **Body-size limits** — every JSON/form parser and raw-body route has a
  documented cap. Large uploads use direct object-store upload per core §3.12.

## Stack-specific patterns

### `nodejs.PAT-hosted-server` `[Hosted]`

Hosted Node.js API behind a reverse proxy: process startup validates config,
initializes OpenTelemetry and shared clients, installs problem+json middleware,
sets request/body/header limits, starts listening, and registers graceful
shutdown. Maps §3.5, §3.10, §3.14, §3.15, §3.16.

### `nodejs.PAT-serverless-handler` `[Serverless]`

Serverless handler validates the event/request, creates request context,
executes the same service boundary used by hosted code, returns problem+json on
errors, and enqueues long-running work before returning 202. It never calls
`app.listen(...)` and never relies on unawaited work after response. Maps
§3.5, §3.9, §3.14, §5.3.

### `nodejs.PAT-problem-details` `[Both]`

Single problem helper:

- Sets `Content-Type: application/problem+json`.
- Maps validation to 400 / 422, auth to 401 / 403, precondition failure to 412,
  conflict to 409, throttle to 429 with `Retry-After`, and unexpected faults
  to 500.
- Includes a stable `type` URI and correlation field.
- Is used by every route or framework error hook. Maps §3.5 / §6.

### `nodejs.PAT-async-context` `[Both]`

Request boundary creates `{ traceId, operationId, route, subject? }` via
`AsyncLocalStorage.run(...)`; loggers and downstream clients read from that
store rather than from globals. Serverless handlers create one context per
invocation. Maps §3.14.

### `nodejs.PAT-resilient-fetch` `[Both]`

Outbound calls use a shared fetch/client wrapper with timeout, bounded retry
with jitter for retryable statuses, `Retry-After` honor, `traceparent`
propagation, and structured retry logs. Idempotency is required before retrying
mutations. Maps §2.6 / §3.10 / §3.14.

### `nodejs.PAT-idempotent-post` `[Both]`

POST mutation accepts `Idempotency-Key`, stores `(key, requestHash, status,
headers, body)` in a TTL replay cache, returns cached responses on retry, and
returns 409 when the same key is reused with a different request body. Maps
§3.6 / §5.6.

### `nodejs.PAT-webhook-receive` `[Both]`

Webhook route reads raw bytes, verifies timestamp freshness, computes HMAC,
compares with `crypto.timingSafeEqual`, deduplicates by event ID, enqueues
work, and returns 202 quickly. Maps §5.5b plus Node.js security guidance for
constant-time comparison.

### `nodejs.PAT-openapi` `[Both]`

Contract-first Node.js surface uses an OpenAPI 3.1 document checked in at a
stable path or generated deterministically from route schemas. CI lints the
document and contract-tests handlers against it. Maps §2.1 / §4.5.

### `nodejs.PAT-otel-startup` `[Hosted]`

Hosted app registers OpenTelemetry before importing route modules that create
clients; shutdown flushes exporters after draining HTTP. Serverless variant
initializes at module load and avoids per-invocation provider setup. Maps
§3.14.
