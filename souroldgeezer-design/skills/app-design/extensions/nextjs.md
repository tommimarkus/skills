# Extension - Next.js App Design

This extension adds Next.js app-router and pages-router mechanics to the
framework-neutral app-design workflow. Load `react.md` first, then this
extension. It covers frontend app structure, route/layout ownership, rendering
boundaries, navigation, caching, forms, metadata, assets, and browser behavior.
HTTP API contract mechanics remain with `api-design`.

Source anchors used for this extension:

- Next.js docs overview: <https://nextjs.org/docs>.
- Next.js App Router: <https://nextjs.org/docs/app>.
- Next.js Server and Client Components:
  <https://nextjs.org/docs/app/getting-started/server-and-client-components>.
- Next.js caching guide: <https://nextjs.org/docs/app/guides/caching>.
- Next.js Route Segment Config:
  <https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config>.
- Next.js components: <https://nextjs.org/docs/app/api-reference/components>.
- Next.js forms guide: <https://nextjs.org/docs/app/guides/forms>.

Re-check those official pages when the Next.js major version, App Router
defaults, cache model, or route segment config is load-bearing.

## Detection Signals

- `package.json` with `next` in dependencies.
- `next.config.{js,ts,mjs,cjs}` or `src/next.config.*`.
- App Router files: `app/**/{layout,page,template,loading,error,not-found,forbidden,unauthorized}.{js,jsx,ts,tsx}`.
- Pages Router files: `pages/**/*.{js,jsx,ts,tsx}` excluding `pages/api/**`
  when the request is purely API-contract work.
- Next components or APIs: `next/link`, `next/image`, `next/font`, `next/script`,
  `next/navigation`, `next/headers`, metadata exports, route groups, parallel
  routes, intercepting routes, or Server/Client Component directives.
- Server Action / Server Function usage that affects a frontend form or
  mutation flow. Public API shape still delegates to `api-design`.

## Scope

Own Next.js-specific app-design interpretation for:

- App Router and Pages Router route/screen ownership;
- layouts, templates, loading/error/not-found/forbidden/unauthorized files;
- Server and Client Component boundaries, serialization, hydration, streaming,
  Suspense, and route segment configuration;
- navigation and URL state via `Link`, redirects, route params, search params,
  router hooks, and progressive route transitions;
- data/cache behavior as it affects UI freshness, user-specific rendering,
  loading states, and invalidation;
- form UX, Server Action handoff, optimistic UI, pending states, and recovery;
- Next image/font/script/metadata primitives, responsive/accessibility/i18n,
  and Core Web Vitals posture.

Route Handlers, Pages API routes, public HTTP APIs, problem details, auth
semantics, idempotency, retries, and observability belong to `api-design`.
Generic React component rules still come from `react.md`.

## Composition Rule

1. Load `react.md` first for component, Hook, state, hydration, browser, and
   generic form/rendering rules.
2. Load this extension second for Next.js file-system routing, Server/Client
   Component boundaries, cache/navigation behavior, Next primitives, and
   framework-specific carve-outs.
3. When a target includes API routes or Route Handlers, compose with
   `api-design`; do not review HTTP contract behavior through app-design.

## Project Assimilation

Inspect these Next.js-specific signals after React and core app assimilation:

- `package.json`: Next/React versions, scripts, package manager, lint/build
  commands, auth/i18n/form/data-cache libraries, and deployment hints.
- `next.config.*`: output mode, base path, asset prefix, images, headers,
  redirects, rewrites, typed routes, React compiler, web vitals attribution,
  server actions config, and proxy/body-size settings.
- App Router tree: route groups, nested layouts, pages, templates, loading,
  error, not-found, forbidden, unauthorized, parallel/intercepting routes, and
  metadata/viewport exports.
- Pages Router tree: `_app`, `_document`, page-level data functions, custom
  error pages, and shared layouts.
- Server/Client boundaries: `'use client'`, `'use server'`, `server-only`,
  `client-only`, `next/headers`, `next/navigation`, and props crossing the
  server/client boundary.
- Data/cache wiring: `fetch` options, route segment config, revalidation calls,
  tags, cache handlers, user-specific dynamic APIs, and invalidation after
  mutation.
- Browser/UI primitives: `next/link`, `next/image`, `next/font`, `next/script`,
  form components, focus management, scroll preservation, viewport metadata,
  analytics/Web Vitals hooks, and i18n routing.

## Route And Layout Defaults

- App Router route segments own page intent, route params, loading, error,
  not-found/unauthorized states, metadata, and layout inheritance. Do not hide
  these responsibilities in shared leaf components.
- Layouts own persistent chrome, landmarks, skip links, navigation state,
  focus/scroll continuity, and shared provider scope. Templates are for state
  reset semantics; use them deliberately.
- Pages Router projects need explicit layout ownership in `_app`, page
  wrappers, or a documented layout pattern. Do not mix one-off page layouts
  without a route-map rationale.
- Route groups, parallel routes, and intercepting routes are app-design choices
  because they change mental model, navigation recovery, and browser history.
  Use them only when the user workflow needs the composition.

## Rendering, Data, And Cache Defaults

- App Router pages and layouts are Server Components by default. Add `'use client'`
  only at narrow interactive boundaries; marking a layout or broad screen as
  client-side needs a clear browser-state reason.
- Client Components are for state, event handlers, browser APIs, lifecycle
  effects, and custom Hooks. Server Components are for server-side data access,
  secret-bearing work, reduced client JavaScript, and streaming.
- Props crossing from Server to Client Components need serializable shape and
  explicit loading/error handling. Do not pass server-only clients, secrets, or
  functions across the boundary.
- Authenticated or user-specific UI must not be accidentally static or publicly
  cached. Dynamic APIs, route segment config, and fetch cache settings need to
  match the freshness/privacy contract.
- Suspense, `loading.*`, streaming, and route transitions need stable geometry,
  reachable labels, focus behavior, and recovery state.
- Hydration mismatches, client-only patches, or non-deterministic render output
  are bugs unless the extension can point to a deliberate framework escape.

## Forms, Navigation, And Browser Behavior

- Forms need labels, validation timing, pending/disabled states, duplicate-submit
  guards, server-error mapping, optimistic rollback, and focus recovery.
- Server Actions can support UI mutation flows, but public partner/client APIs,
  error DTOs, idempotency, and retry contracts still delegate to `api-design`.
- `Link`, redirects, router hooks, search params, and route params need explicit
  ownership. Preserve meaningful browser history and scroll/focus intentionally.
- `next/image`, `next/font`, and `next/script` should serve the app contract:
  stable layout, accessible alternatives, font fallback, script loading priority,
  CSP/security review handoff, and measured performance.
- Metadata and viewport exports belong near the route/layout that owns the
  user-facing screen. Avoid scattered title/description/robots behavior that
  cannot be traced from the route map.

## API Client Delegation

Next.js app-design owns how frontend screens call clients, how Server
Components feed Client Components, how mutations affect UI state, and how route
freshness is presented. Delegate Route Handlers, Pages API routes, public HTTP
API design, problem details, auth semantics, idempotency, retries, and API
observability to `api-design`.

Smell: a Server Action is treated as a public API, returns ad hoc error objects
to third-party clients, and bypasses Route Handlers or OpenAPI. Use
`api-design` for that contract and keep app-design on the form/screen behavior.

## Responsive, Accessibility, I18n, And Performance

- Route layouts and persistent chrome must work with keyboard, touch,
  coarse/fine pointers, reduced motion, forced colors, text expansion, 400%
  zoom, RTL, and localized route text.
- App Router streaming and cache behavior affect perceived readiness and
  privacy; disclose static versus runtime evidence.
- Static review can flag image/font/script/client-bundle posture only. Core Web
  Vitals, hydration cost, and route-transition performance need browser tooling
  or RUM evidence.

## Positive Signals

- `nextjs.POS-APP-1`: App Router segments have clear page/layout/loading/error
  ownership and preserve landmarks/focus.
- `nextjs.POS-APP-2`: Client Components are narrow interactive islands with
  serializable props and explicit browser-state reasons.
- `nextjs.POS-APP-3`: cache/revalidation settings are documented at the route
  or data boundary that owns freshness and privacy.
- `nextjs.POS-APP-4`: Server Action form flow exposes pending, validation,
  server-error, success, retry, and optimistic rollback states.
- `nextjs.POS-APP-5`: image/font/script primitives are configured for stable
  layout, accessible names, and measured performance.

## Smell Codes

- `nextjs.APP-ROUTE-1`: App Router segment lacks colocated loading/error/not
  found/unauthorized behavior for a user-visible route state.
- `nextjs.APP-LAYOUT-1`: layout owns persistent chrome but lacks landmarks,
  skip link, route focus/scroll strategy, or provider-scope rationale.
- `nextjs.APP-BOUNDARY-1`: broad layout/page is marked `'use client'` without a
  narrow interactivity or browser-API reason.
- `nextjs.APP-RENDER-1`: Server/Client boundary passes non-serializable props,
  server-only values, or hydration-unstable output.
- `nextjs.APP-CACHE-1`: authenticated, user-specific, or mutation-sensitive UI
  is statically cached or revalidated without a privacy/freshness rule.
- `nextjs.APP-FORM-1`: Server Action or form flow lacks pending, duplicate
  submit, validation, server-error mapping, optimistic rollback, or focus recovery.
- `nextjs.APP-NAV-1`: route/search-param updates break browser history,
  focus/scroll continuity, or loading-state recovery.
- `nextjs.APP-PERF-1`: image/font/script/client-bundle/streaming cost is
  treated as verified without browser or RUM evidence.

## Carve-Outs

- Do not flag broad Server Component use in App Router when interactivity is
  intentionally isolated in child Client Components.
- Do not require a `loading.*` file when a route has an explicit, tested
  loading pattern that preserves layout, focus, and recovery.
- Do not flag route-level data fetching in a Server Component when API contract
  semantics are delegated and the UI freshness/privacy rule is explicit.
- Do not review Route Handlers or Pages API routes as app-design findings when
  the issue is HTTP contract, auth, reliability, or observability; delegate to
  `api-design`.
