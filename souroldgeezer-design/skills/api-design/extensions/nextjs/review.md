# Extension: nextjs review lane

Review classifications and carve-outs for [the nextjs core](../nextjs.md).

## Load condition

Read relevant finding criteria, positive signals, or carve-outs for the requested judgment.
A narrow question may consult this lane without changing mode; factual Extract
does not acquire an unsolicited compliance verdict. Do not preload the whole
lane or unrelated stacks. Patterns illustrate strong defaults; preserve a
compatible project contract unless actual safety or protocol requirements rule
it out. A missing preferred format or tool alone is not a finding.

## Smell codes

### High-confidence

- **`nextjs.HC-1`** — Route Handler or Pages API error path breaks the declared
  stable failure contract or leaks secrets/internal traces; a compatible
  established JSON envelope is valid. *Layer:* static + contract.
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
  successful 2xx responses. Errors follow the stable project contract; problem+json is the new-contract default.
- Server Actions used only by first-party UI forms, provided they are not
  documented as partner/public API and still enforce auth/validation.
- Static/cached GET Route Handlers for genuinely public, read-only, non-user
  specific data with documented cache policy.
- Single-instance self-hosted Next.js with persistent disk may use default
  cache behavior if deployment docs state the single-instance constraint.
- Edge runtime routes when the user explicitly asks for Edge API design. This
  extension does not review Edge mechanics; stop and ask for a future/alternate
  extension or proceed with core-only HTTP contract guidance.
