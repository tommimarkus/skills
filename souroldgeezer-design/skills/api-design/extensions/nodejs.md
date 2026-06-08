# Extension: Node.js / TypeScript HTTP APIs

Stack-specific additions to the `api-design` skill for Node.js HTTP APIs. The
core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md)
stays framework-neutral; this extension layers Node.js runtime, hosted-process,
and serverless-handler mechanics on top without overriding core rules.

Source anchors used for this extension:

- Node.js official docs: `node:http`
  <https://nodejs.org/api/http.html>, `AsyncLocalStorage`
  <https://nodejs.org/api/async_context.html>, and global `fetch`
  <https://nodejs.org/api/globals.html#fetch>.
- Node.js official security guidance:
  <https://nodejs.org/learn/getting-started/security-best-practices>.
- Microsoft Learn Azure Functions Node.js developer guide:
  <https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-node>.
- AWS Lambda Node.js handler docs:
  <https://docs.aws.amazon.com/lambda/latest/dg/nodejs-handler.html>.

Re-check those official pages when a runtime version, serverless platform, or
handler model is load-bearing.

## Name and detection signals

The skill loads this extension when any of the following match:

- `package.json` at the target root or workspace root.
- `package.json` with HTTP API runtime dependencies such as `express`,
  `fastify`, `koa`, `hono`, `@hono/node-server`, `@nestjs/core`, `restify`,
  `@azure/functions`, `aws-lambda`, `@middy/core`, `serverless-http`, or
  `@vendia/serverless-express`.
- Source files importing `node:http`, `node:https`, `http.createServer`,
  `express()`, `fastify()`, `new Koa()`, `new Hono()`, `NestFactory.create`,
  `app.http(...)` from `@azure/functions`, or `export const handler = ...`.
- Hosted-process scripts in `package.json`: `start`, `serve`, or `dev` running
  `node`, `tsx`, `ts-node`, `nodemon`, `next start` (load this extension first;
  `nextjs.md` may also load), `fastify start`, or `nest start`.
- Serverless platform files: `host.json` with `@azure/functions`, AWS SAM
  `template.yaml` / `template.yml`, `serverless.yml`, `serverless.ts`,
  `netlify/functions/**`, `api/**/*.js|ts` under a Vercel-style project, or
  code using `context.callbackWaitsForEmptyEventLoop`.

When `next` is present in `package.json`, load this extension first and then
`nextjs.md`. Next.js is a hosted framework overlay on top of Node.js for this
skill.

## Hosting-model surface

Rules are tagged `[Hosted]`, `[Serverless]`, `[Adapter]`, or `[Both]`.

- **`[Hosted]`** — long-lived Node.js process behind a reverse proxy, load
  balancer, ingress, or platform router. The app owns listener setup, graceful
  shutdown, request/header timeouts, body-size limits, process-level
  observability, and startup failure behavior.
- **`[Serverless]`** — platform invokes a handler and owns the listener,
  timeout, concurrency, and response flush. The app owns handler shape, durable
  side effects, response-before-timeout behavior, per-invocation logging, and
  safe module-scope reuse across warm invocations.
- **`[Adapter]`** — Express / Fastify / Hono / Nest adapted to a serverless
  platform through an adapter package. The framework surface remains Node.js,
  but `app.listen(...)` is not the deployed entry point.
- **`[Both]`** — rules that apply to hosted and serverless shapes.

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

## Project assimilation (Node.js-specific)

Run this after the core framework-agnostic discovery pass; results feed into
the assimilation footer.

1. **Runtime and package manager** — inspect `package.json`, lockfile,
   `engines.node`, `.nvmrc`, Dockerfile, and platform config. Record Node.js
   version and package-manager contract.
2. **Hosted vs serverless** — inspect start scripts, `app.listen`, framework
   adapters, platform files, and handler exports. Record `[Hosted]`,
   `[Serverless]`, `[Adapter]`, or mixed.
3. **HTTP framework** — Express, Fastify, Koa, Hono, Nest, raw `node:http`, or
   unknown. Record the framework error hook and validation hook.
4. **Contract source** — OpenAPI file, schema-to-OpenAPI generator, route
   annotations, or none.
5. **Error shape** — problem middleware/helper vs ad hoc JSON/string/HTML.
6. **Validation** — JSON Schema / OpenAPI / Zod / Joi / class-validator /
   framework schema. Missing boundary validation is legacy debt.
7. **Auth** — maintained OAuth/OIDC/JWT/session middleware, API key, custom
   token parser, or none. Public non-health endpoints without auth are debt.
8. **Body limits** — framework parser limits, raw-body routes, uploads, and
   reverse-proxy/request-size config.
9. **Observability** — OpenTelemetry startup, AsyncLocalStorage context,
   structured logs, request IDs, `traceparent` propagation.
10. **Secrets/config** — committed `.env*`, raw secrets in source, platform
    secret references, cloud secret manager integration.
11. **Long-running work** — queues/jobs/workers vs work held inside the HTTP
    request or serverless invocation.
12. **Hosted deployment** — reverse proxy / ingress / load balancer, health
    probes, graceful shutdown, request/header timeout settings.

### Mapping reference defaults to Node.js idioms

| Reference default | Node.js idiom |
|---|---|
| §3.5 problem+json | Framework error hook + shared problem helper |
| §3.6 idempotency | Middleware/helper + TTL replay cache |
| §3.7 cursor pagination | `{ items, nextCursor }` response + optional `Link` |
| §3.9 async 202 | Enqueue job before returning `202` + `Location` |
| §3.10 throttling | Edge/proxy limiter plus 429 helper with `Retry-After` |
| §3.14 observability | AsyncLocalStorage + OpenTelemetry + structured logs |
| §3.16 data access | Module-scope/server-scope singleton clients or DI container |
| §3.17 secrets | Platform secret manager or cloud secret reference; no literals |

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

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.3, §3.4, §3.5, §3.6, §3.7,
§3.9, §3.10, §3.11, §3.12, §3.13, §3.14, §3.15, §3.16, §3.17, §4.5, §5.3,
§5.5b, §5.6, §5.8, §5.9, §5.10, §5.12, §6, §7.
