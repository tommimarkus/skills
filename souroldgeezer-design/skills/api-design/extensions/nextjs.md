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

Frontend app concerns remain delegated to `app-design`: route layout, screen
composition, Server/Client Component placement for UI, navigation UX, form
interaction states, image/font/script posture, responsive behavior,
accessibility, and browser performance posture. This extension owns Route
Handlers, Pages API routes, Server Actions when they act as mutation/API
surfaces, and the HTTP contract/reliability/observability implications around
those boundaries.

## Composition rule

Load `nodejs.md` first, then `nextjs.md`. `nextjs.*` smells may carve out `nodejs.*` smells only at exact Next.js platform boundaries; they do not weaken core baselines. If the same change includes frontend app behavior, load `app-design` with React and Next.js extensions.

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

## Mode lanes

This core file is the always-loaded nextjs stack surface. Load exactly one
mode lane when the task requires it:

- **Build:** read [`nextjs/build.md`](nextjs/build.md) for detailed primitives and `*.PAT-*` implementation patterns.
- **Review:** read [`nextjs/review.md`](nextjs/review.md) for `*.HC-*`, `*.LC-*`, and `*.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Route Handlers
- Route Segment Config
- Hosted self-management
- Instrumentation
- Server Actions

Detailed signatures and implementation guidance live in [`nextjs/build.md`](nextjs/build.md).

## Shared safety invariants

- Keep API contracts at Route Handlers or Pages API boundaries; do not treat UI rendering behavior as an API contract.
- Bound request bodies and duration, make mutation retries idempotent, and move long-running work to durable queues.
- Emit RFC 9457 problem details on error paths and preserve Node.js runtime safeguards from the composed base.
- Keep deployment secrets and Server Action encryption keys out of source and consistent across instances.

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

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.4, §3.5, §3.6, §3.7, §3.9,
§3.10, §3.11, §3.12, §3.13, §3.14, §3.15, §3.17, §4.5, §5.3, §5.6, §5.8,
§5.9, §5.10, §6, §7.
