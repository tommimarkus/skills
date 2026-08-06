# Extension: nextjs build lane

Implementation detail for [the nextjs core](../nextjs.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

## Stack-specific primitives

### Route Handlers

- **File shape** — `app/**/route.ts|js` exports HTTP method functions such as
  `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, and `OPTIONS`. The official
  Next.js docs state Route Handlers are available only in the `app` directory
  and use Web `Request` / `Response` APIs.
- **No colocated page** — a `route.ts|js` file cannot sit at the same route
  segment level as `page.tsx|jsx|js|ts`.
- **Caching** — Route Handlers are not cached by default. GET may opt into
  caching; mutating methods are not cached. A user-specific or authenticated
  GET must be dynamic or explicitly `no-store`.
- **Error contract** — `Response.json(...)` is fine for successful responses,
  but error paths set `application/problem+json` explicitly and include the
  core problem fields.

### Route Segment Config

- **`export const runtime = 'nodejs'`** — Node.js runtime is the hosted default
  and the right choice for Node APIs, database SDKs, OpenTelemetry exporters,
  and process-local clients. Edge runtime is a different platform surface.
- **`export const maxDuration = N`** — platforms can consume this from Next's
  build output. Use it as documentation even when self-hosting, but treat real
  enforcement as deployment-platform evidence.
- **`dynamic` / `revalidate` / `fetchCache`** — these control static vs dynamic
  behavior and cache semantics. Never opt authenticated or request-specific API
  responses into public/static caching.

### Hosted self-management

- **Reverse proxy** — official Next.js self-hosting docs recommend a reverse
  proxy in front of the Next server for malformed requests, slow connections,
  payload limits, rate limiting, and other security concerns.
- **Shared cache** — multi-instance / pod deployments need external cache
  coordination for cached pages, data, and revalidation. The default local
  memory/disk cache is per-instance.
- **Build/deployment consistency** — use the same build across instances and
  configure build ID / deployment ID for rolling deployments when needed.
- **Server Actions encryption key** — multi-instance deployments using Server
  Actions need a consistent `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`; otherwise one
  instance may not decrypt another instance's action payload.

### Instrumentation

- **`instrumentation.ts|js`** — Next.js calls `register()` once when a new
  server instance starts. Use it to register OpenTelemetry or other server-side
  observability.
- **`onRequestError`** — optional export for captured server errors. Await any
  async reporting work and avoid leaking private request data into telemetry.
- **Runtime split** — if the project uses both Node and Edge runtime code,
  dispatch by `process.env.NEXT_RUNTIME` in instrumentation.

### Server Actions

- **Server Function shape** — official Next.js docs define Server Functions as
  async functions callable from the client through a network request; Server
  Actions are the mutation-oriented use. They use POST under the hood.
- **API boundary** — Server Actions are not a stable partner/public API
  contract. For third-party or non-UI clients, expose a documented Route
  Handler instead.
- **Mutation discipline** — when a Server Action mutates durable state, apply
  the same auth, validation, idempotency, and observability expectations as a
  POST Route Handler.

## Stack-specific patterns

### `nextjs.PAT-route-handler-problem-details` `[RouteHandler]`

Route Handler delegates success and error construction to helpers. Error
helper returns `new Response(JSON.stringify(problem), { status, headers:
{ "content-type": "application/problem+json" } })`, includes a stable `type`
URI, and uses the Node.js request context for correlation. Maps §3.5.

### `nextjs.PAT-hosted-node-runtime` `[HostedNext]`

Hosted Next.js runs in the Node.js runtime behind a reverse proxy. API routes
export `runtime = 'nodejs'` when Node-only SDKs or OpenTelemetry exporters are
used, `maxDuration` documents expected handler duration, and deployment config
handles TLS, body caps, rate limiting, and health probes. Maps §3.15.

### `nextjs.PAT-shared-cache` `[HostedNext]`

Multi-instance Next.js deployment using cached Route Handlers, ISR,
`revalidatePath`, `revalidateTag`, or `'use cache'` configures an external cache
handler and disables unsafe in-memory-only assumptions. Maps §3.7 / §3.15.

### `nextjs.PAT-server-action-mutation` `[ServerAction]`

Server Action validates `FormData`, checks authorization, applies idempotency or
natural-key dedup for retryable mutations, performs the mutation, revalidates
cache tags/paths, and logs with correlation. Public/partner clients use a
Route Handler instead. Maps §3.4 / §3.6 / §5.6.

### `nextjs.PAT-instrumentation` `[HostedNext]`

`instrumentation.ts` registers OpenTelemetry once per server instance and
exports `onRequestError` to report route/action/render/proxy errors with
sanitized request context. Maps §3.14.

### `nextjs.PAT-route-handler-openapi` `[RouteHandler]`

OpenAPI 3.1 contract enumerates every Route Handler / Pages API operation.
Route schemas and response helpers are kept in sync with the document through
CI lint and contract tests. Maps §2.1 / §4.5.
