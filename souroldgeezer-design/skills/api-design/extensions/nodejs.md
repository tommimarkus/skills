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

## Mode lanes

This core file is the always-loaded nodejs stack surface. Load exactly one
mode lane when the task requires it:

- **Build:** read [`nodejs/build.md`](nodejs/build.md) for detailed primitives and `*.PAT-*` implementation patterns.
- **Review:** read [`nodejs/review.md`](nodejs/review.md) for `*.HC-*`, `*.LC-*`, and `*.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Runtime and package surface
- Hosted Node.js HTTP server
- Serverless Node.js handler
- Request context and observability
- HTTP contract helpers

Detailed signatures and implementation guidance live in [`nodejs/build.md`](nodejs/build.md).

## Shared safety invariants

- Target a supported Node.js runtime with deterministic dependency installation.
- Bound request bodies and timeouts, keep request state out of module globals, and reuse expensive clients safely.
- Emit RFC 9457 problem details on error paths; durable work must be enqueued before a serverless response returns.
- Keep secrets out of source, authenticate non-public routes, and verify webhook signatures over raw bounded bytes.

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

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.3, §3.4, §3.5, §3.6, §3.7,
§3.9, §3.10, §3.11, §3.12, §3.13, §3.14, §3.15, §3.16, §3.17, §4.5, §5.3,
§5.5b, §5.6, §5.8, §5.9, §5.10, §5.12, §6, §7.
