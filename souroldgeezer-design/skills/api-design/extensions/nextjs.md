# Extension: Next.js hosted HTTP APIs

Stack-specific additions to the `api-design` skill for hosted Next.js API
surfaces. Load [`nodejs.md`](nodejs.md) first, then this extension. The core
reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md)
stays framework-neutral; this extension adds Next.js Route Handler, Pages API,
Server Action, instrumentation, and self-hosting mechanics without overriding
core or Node.js rules.

Source anchors used for this extension:

- Next.js Route Handlers:
  <https://nextjs.org/docs/app/getting-started/route-handlers>.
- Next.js Route Segment Config:
  <https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config>.
- Next.js Self-Hosting:
  <https://nextjs.org/docs/app/guides/self-hosting>.
- Next.js Instrumentation:
  <https://nextjs.org/docs/app/guides/instrumentation>.
- Next.js Server Functions / Server Actions:
  <https://nextjs.org/docs/app/getting-started/updating-data>.

Re-check those official pages when the Next.js major version, hosting model, or
route/runtime config is load-bearing.

## Name and detection signals

The skill loads this extension, after `nodejs.md`, when any of the following
match:

- `package.json` with `next` in `dependencies`.
- `next.config.{js,ts,mjs,cjs}` at the project root.
- `app/**/route.{js,ts}` or `src/app/**/route.{js,ts}`.
- `pages/api/**/*.{js,ts}` or `src/pages/api/**/*.{js,ts}`.
- `instrumentation.{js,ts}` or `src/instrumentation.{js,ts}` in a Next.js
  project.
- Source containing `'use server'` in `app/**` / `src/app/**` with a Next.js
  dependency.

This extension is for **hosted Next.js**: `next start`, standalone output,
Docker, Kubernetes, App Service, VM, or another long-lived Node.js server
shape. Vercel / Netlify / AWS / Azure serverless adapters can still be detected
by `nodejs.md`, but platform-specific serverless Next.js limits are out of
scope unless a future extension adds that platform.

## Composition rule

Next.js depends on the Node.js extension:

1. Load `nodejs.md` first for runtime, package, observability, body-size,
   hosted-process, and generic serverless-handler rules.
2. Load `nextjs.md` second for file-system routing, Route Handler semantics,
   Server Actions, Next instrumentation, cache/deployment mechanics, and
   hosted Next.js carve-outs.
3. `nextjs.*` smells may carve out `nodejs.*` smells only at exact Next.js
   platform boundaries (`next/server`, Route Handlers, Pages API routes,
   Server Actions, `instrumentation.ts`, `next.config.*`). They do not weaken
   core contract, auth, reliability, or observability baselines.

## Hosting-model surface

Rules are tagged `[HostedNext]`, `[RouteHandler]`, `[PagesApi]`,
`[ServerAction]`, `[NodeRuntime]`, or `[BothRouters]`.

- **`[HostedNext]`** — long-lived Next.js Node server. Reverse proxy, cache
  coordination, deployment ID/build ID consistency, process lifecycle, and
  shared secret configuration are deployment concerns that must be reviewed.
- **`[RouteHandler]`** — `app/**/route.ts|js` using Web `Request` / `Response`
  APIs plus `NextRequest` / `NextResponse`. This is the preferred API surface
  for App Router.
- **`[PagesApi]`** — `pages/api/**` default-export handler using Node
  `IncomingMessage` / `ServerResponse` style. Supported, but not the preferred
  greenfield shape for App Router projects.
- **`[ServerAction]`** — `'use server'` mutation functions. These are UI
  mutation endpoints, not partner/public HTTP APIs; still apply auth,
  validation, idempotency, and observability when they mutate state.
- **`[NodeRuntime]`** — route or page explicitly runs in the Node.js runtime
  (`export const runtime = 'nodejs'`) or inherits the default. Edge runtime API
  mechanics are out of scope for this hosted extension.

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

## Project assimilation (Next.js-specific)

Run this after Node.js project assimilation; results feed into the assimilation
footer.

1. **Next version and router flags** — parse `package.json#dependencies.next`;
   record App Router (`app/`) and Pages Router (`pages/`) presence.
2. **API route surface** — enumerate `app/**/route.*`, `pages/api/**`, method
   exports, and route segment collisions (`route.*` beside `page.*`).
3. **Runtime config** — inspect `runtime`, `dynamic`, `revalidate`,
   `fetchCache`, `preferredRegion`, and `maxDuration` exports in API route
   segments.
4. **Server Actions** — grep `'use server'` and identify durable mutations,
   public form actions, and action files used as API surfaces.
5. **Contract source** — OpenAPI document/generator, route schemas, or none.
6. **Error shape** — problem helper vs `NextResponse.json({ error })` /
   `res.status(...).json({ error })`.
7. **Auth** — `proxy.ts` / legacy `middleware.ts`, route-local checks,
   session/auth library, OAuth/OIDC middleware, or none.
8. **Caching** — `cacheHandler`, `cacheHandlers`, `cacheMaxMemorySize`,
   `revalidatePath`, `revalidateTag`, `use cache`, `use cache: remote`, ISR,
   and multi-instance deployment evidence.
9. **Instrumentation** — `instrumentation.ts|js`, `register`, `onRequestError`,
   OpenTelemetry packages, and Node-vs-Edge runtime split.
10. **Hosted deployment** — `output: "standalone"`, Dockerfile, Kubernetes,
    process manager, reverse proxy, deployment ID/build ID, and
    `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`.

### Mapping reference defaults to Next.js idioms

| Reference default | Next.js idiom |
|---|---|
| §3.5 problem+json | Route Handler / Pages API problem helper |
| §3.6 idempotency | Route Handler middleware/helper or Server Action dedup |
| §3.7 pagination | Cursor envelope from Route Handler plus optional `Link` |
| §3.9 async 202 | Route Handler enqueues job and returns 202 + `Location` |
| §3.10 throttling | Reverse proxy / edge tier plus route 429 helper |
| §3.14 observability | `instrumentation.ts`, `onRequestError`, Node request context |
| §3.15 hosting | Hosted Node runtime, reverse proxy, shared cache, deployment ID |
| §3.17 secrets | Runtime environment / secret manager; no committed literals |

## Smell codes

### High-confidence

- **`nextjs.HC-1`** — Route Handler or Pages API error path returns bare JSON
  / string instead of `application/problem+json`. *Layer:* static + contract.
- **`nextjs.HC-2`** — Public mutating Route Handler / Pages API / Server Action
  lacks authz check or explicit public-write declaration. *Layer:* static.
- **`nextjs.HC-3`** — Server Action exposed or documented as a partner/public
  API instead of a UI mutation surface with a Route Handler contract. *Layer:*
  static + contract.
- **`nextjs.HC-4`** — Multi-instance hosted deployment uses cached routes,
  revalidation, or Server Actions with only per-instance memory/disk cache and
  no external cache handler / remote cache decision. *Layer:* static + iac.
- **`nextjs.HC-5`** — Multi-instance Server Action deployment lacks a stable
  `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`. *Layer:* iac.
- **`nextjs.HC-6`** — Large upload streams through a Route Handler / Pages API
  without a documented size cap and direct object-store handoff. *Layer:*
  static + contract.
- **`nextjs.HC-7`** — API route sets `runtime = 'edge'` while using Node-only
  APIs, hosted Node clients, or this extension's Node runtime patterns. *Layer:*
  static.
- **`nextjs.HC-8`** — Authenticated or user-specific GET Route Handler is made
  static/cacheable (`force-static`, public `revalidate`, or equivalent) without
  a private cache key. *Layer:* static + contract.
- **`nextjs.HC-9`** — Hosted public API relies on `next start` directly exposed
  to the internet, with no reverse proxy / ingress / platform router evidence.
  *Layer:* iac.
- **`nextjs.HC-10`** — API-heavy hosted app lacks `instrumentation.ts|js` or
  equivalent process-level observability startup. *Layer:* static.
- **`nextjs.HC-11`** — Long-running Route Handler / Server Action performs
  required work synchronously instead of 202 + queue/job, and has no
  `maxDuration` / timeout contract. *Layer:* static + contract.
- **`nextjs.HC-12`** — Added Route Handler / Pages API operation missing from
  OpenAPI. *Layer:* static + contract.
- **`nextjs.HC-13`** — `route.ts|js` and `page.tsx|jsx|js|ts` are colocated at
  the same route segment level. Official routing docs reject this shape. *Layer:*
  static.

### Low-confidence

- **`nextjs.LC-1`** — New App Router project adds `pages/api/**` instead of a
  Route Handler. Supported, but review whether migration compatibility is the
  reason. *Layer:* static.
- **`nextjs.LC-2`** — API route with Node-only database SDK relies on inherited
  runtime instead of explicitly exporting `runtime = 'nodejs'`. *Layer:* static.
- **`nextjs.LC-3`** — Server Action mutates state without a visible
  idempotency/natural-key story; may be acceptable for one-shot human forms.
  *Layer:* static.
- **`nextjs.LC-4`** — `onRequestError` reports full headers/cookies/body to an
  external sink. Context-dependent but high privacy risk. *Layer:* static.
- **`nextjs.LC-5`** — Multi-container deployment does not document build ID /
  deployment ID consistency. *Layer:* iac.

### Positive signals

- **`nextjs.POS-1`** — Route Handlers use shared problem+json and validation
  helpers.
- **`nextjs.POS-2`** — API routes explicitly export `runtime = 'nodejs'` and a
  documented `maxDuration` when Node runtime behavior matters.
- **`nextjs.POS-3`** — `instrumentation.ts` registers OpenTelemetry and
  `onRequestError` sanitizes error telemetry.
- **`nextjs.POS-4`** — Hosted deployment has reverse proxy / ingress, health
  probes, body caps, and rate limiting in IaC or platform config.
- **`nextjs.POS-5`** — Multi-instance deployment configures shared cache /
  remote cache and deployment ID/build ID consistency.
- **`nextjs.POS-6`** — Server Actions are limited to UI mutations; external API
  consumers use Route Handlers documented in OpenAPI.
- **`nextjs.POS-7`** — Authenticated GET handlers are dynamic/no-store or use a
  private cache key.
- **`nextjs.POS-8`** — Large uploads use direct object-store upload grants
  rather than streaming through the Next.js server.

## Carve-outs

Do not flag the following:

- `Response.json(...)`, `NextResponse.json(...)`, or `res.json(...)` on
  successful 2xx responses. The problem+json requirement applies to errors.
- Server Actions used only by first-party UI forms, provided they are not
  documented as partner/public API and still enforce auth/validation.
- Static/cached GET Route Handlers for genuinely public, read-only, non-user
  specific data with documented cache policy.
- Single-instance self-hosted Next.js with persistent disk may use default
  cache behavior if deployment docs state the single-instance constraint.
- Edge runtime routes when the user explicitly asks for Edge API design. This
  extension does not review Edge mechanics; stop and ask for a future/alternate
  extension or proceed with core-only HTTP contract guidance.

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.4, §3.5, §3.6, §3.7, §3.9,
§3.10, §3.11, §3.12, §3.13, §3.14, §3.15, §3.17, §4.5, §5.3, §5.6, §5.8,
§5.9, §5.10, §6, §7.
