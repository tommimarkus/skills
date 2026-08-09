# Extension - React App Design

This extension adds React app and component mechanics to the
framework-neutral app-design workflow. It covers browser React applications and
React component trees embedded in framework apps. Framework-specific routing,
server rendering, and deployment mechanics belong to their own overlays.

Source anchors used for this extension:

- React reference overview: <https://react.dev/reference/react>.
- React Hooks reference: <https://react.dev/reference/react/hooks>.
- React Effect reference: <https://react.dev/reference/react/useEffect>.
- React external-store reference: <https://react.dev/reference/react/useSyncExternalStore>.
- React purity rules:
  <https://react.dev/reference/rules/components-and-hooks-must-be-pure>.
- React Rules of Hooks: <https://react.dev/reference/rules/rules-of-hooks>.
- React DOM hydration:
  <https://react.dev/reference/react-dom/client/hydrateRoot>.
- React Suspense: <https://react.dev/reference/react/Suspense>.

Re-check those official pages when React major version, compiler behavior, or
server-component support is load-bearing.

## Detection Signals

- `package.json` with `react` and usually `react-dom` dependencies.
- `src/main.{js,jsx,ts,tsx}`, `src/index.{js,jsx,ts,tsx}`, or a framework
  entrypoint that renders React.
- `*.jsx` / `*.tsx` files with React components, JSX, Hooks, Context,
  Suspense, portals, or error boundaries.
- Vite, Create React App, Remix, Next.js, Gatsby, Astro React integration, or
  another build manifest that clearly renders React in the browser.
- React state/data libraries such as React Router, TanStack Query, Redux,
  Zustand, Jotai, React Hook Form, Formik, or XState.

## Scope

Own React-specific app-design interpretation for:

- component boundaries, props, composition, slots/children, and context;
- Hook placement, custom Hook ownership, reducer/state-machine boundaries, and
  external-store subscriptions;
- rendering purity, memoization posture, Suspense/loading/error boundaries, and
  hydration risk;
- browser APIs, effects, portals, focus, dialogs, forms, storage, and
  navigation state;
- client-side data ownership, query cache invalidation, optimistic UI, and API
  client placement;
- responsive, accessibility, i18n, and Core Web Vitals posture for React
  components and routes.

React Native is out of scope. HTTP endpoint contracts, problem details,
idempotency, and API observability belong to `api-design`. Generic TypeScript
module/package design belongs to `software-design`.

## Project Assimilation

Inspect these React-specific signals after core app-design assimilation:

- `package.json` and lockfile: React version, framework, router, form library,
  data-fetching/cache library, state libraries, component library, compiler,
  lint scripts, and build/test commands.
- Entry points: `createRoot`, `hydrateRoot`, provider tree, strict mode, router,
  query client, i18n provider, theme provider, error reporting, and Web Vitals
  hooks.
- Route/screen files: route ownership, loading/error/empty/unauthorized states,
  route params, data source, and layout ownership.
- Components: prop contracts, composition shape, key usage, controlled versus
  uncontrolled inputs, event ownership, and whether a leaf component owns too
  many concerns.
- Hooks and state: custom Hook boundaries, reducer ownership, context scope,
  external store subscription semantics, query cache invalidation, optimistic
  update rollback, state identity/keys, derived values, and cleanup.
- Browser/runtime code: `useEffect`, `useLayoutEffect`, portals, focus helpers,
  storage, media queries, resize/scroll listeners, timers, and observer cleanup.
- CSS and assets: logical properties, container-aware sizing, focus states,
  reduced-motion handling, text expansion, RTL, image/font loading, and
  component-library theme overrides.

Reuse existing project providers, components, hooks, and state libraries only
when they satisfy the core app-design rule. A component library primitive is
not compliant merely because it exists.

## App Architecture Defaults

- Route/screen components own route params, top-level loading/error/empty
  states, and navigation intent. Leaf components should render a focused role
  and emit intent through props/callbacks or a narrow store boundary.
- Prefer composition and explicit props for local UI variation. Use Context for
  stable cross-cutting values such as theme, locale, auth display state, or
  form context; do not turn it into an implicit event bus.
- Keep render pure. Side effects belong in event handlers or effects, with
  cleanup and capability checks where browser APIs are used.
- Development-only Strict Mode may re-run render and Effect setup/cleanup to
  expose unsafe lifecycle assumptions. Calibrate diagnostics against that
  behavior; do not suppress it or mistake it for a production interaction.
- Hooks live at the top level of React function components or custom Hooks.
  Conditional behavior belongs inside Hook bodies, reducers, or state machines.
- Suspense, loading skeletons, and error boundaries are app-design choices
  because they affect perceived readiness, focus, layout stability, and recovery.

## Component And State Defaults

- Split components by user workflow and state ownership, not by arbitrary UI
  layers. A good component has a clear input contract, output events, and a
  single rendering role.
- Use reducers or explicit state machines when a screen has multi-step,
  async, undo/rollback, or mutually exclusive states. Avoid scattered boolean
  flags that can represent impossible UI combinations.
- Server/cache data and local draft state need separate ownership. Query/cache
  libraries should own fetched server state; forms should own draft state until
  submit/commit.
- Derive values from current props/state during render when possible. Introduce
  state only for user-editable, asynchronous, historical, or externally owned
  values; an Effect that merely copies render-derived state obscures ownership.
- State identity follows its position in the rendered tree. Use stable keys for
  intentional preservation or reset across data items, routes, and workflow
  steps; do not use incidental array position when identity can change.
- External stores need selectors, reset rules, subscription cleanup, and testable
  mutations. A concurrent-safe subscription should use a
  `useSyncExternalStore`-style subscribe/snapshot contract so React can detect
  consistent snapshots; do not store per-route ephemeral state globally without
  a retention and invalidation rule.
- Optimistic UI needs pending, success, failure, retry, and rollback behavior
  visible in the component contract.

## Rendering And Browser Boundaries

- `hydrateRoot` implies the client tree must match server-rendered markup.
  Treat hydration mismatches as bugs; do not hide them with client-only patches
  unless a framework-specific extension documents the escape hatch.
- Browser-only reads such as `window`, `document`, storage, media queries, and
  observers need effect-time access, capability checks, and fallback UI.
- Portals, dialogs, popovers, and overlays need focus trap/restoration,
  keyboard behavior, inert/background handling, and scroll locking that works
  across breakpoints.
- Effects that subscribe to events, timers, observers, sockets, or external
  stores need cleanup. Effects should synchronize with external systems, not
  duplicate render-derived state. Async work needs a cleanup-owned cancellation
  or stale-result guard such as `AbortSignal`; an old request must not overwrite
  the current screen after dependencies change or the component unmounts.
- Lazy-loaded components and Suspense fallbacks should preserve layout geometry
  and reachable names so loading states do not cause layout shift or a11y drift.

## API Client Delegation

React app-design owns where API clients are called in the frontend, how data
loading appears, how mutations affect UI state, and how error/retry states map
to screens. Delegate endpoint shape, auth semantics, problem details, retries,
idempotency, conditional requests, and API observability to `api-design`.

Smell: a presentational component builds raw URLs, interprets error schemas,
owns retry semantics, mutates a global cache, and renders form controls. Move
API contract semantics behind a client/service boundary and delegate the
contract review.

## Responsive, Accessibility, I18n, And Performance

- Component CSS still needs logical properties, content-derived breakpoints,
  container queries where components are reused, `:focus-visible`, reduced
  motion, forced-colors behavior, and text-expansion room.
- Headless/component libraries can provide accessible primitives, but project
  composition and theme overrides can break names, roles, contrast, focus, and
  target size. Verify rendered DOM or disclose that it was not checked.
- Forms need labels, descriptions, validation timing, server-error mapping,
  duplicate-submit guards, and focus on failure.
- Client bundle cost, hydration, lazy loading, image/font loading, and
  third-party scripts affect Core Web Vitals. Static review can flag posture
  only; runtime metrics require browser tooling or RUM.
- Memoization is a measured optimization, not a correctness mechanism. Preserve
  pure rendering and stable contracts first; never assume a React compiler is
  available or will remove a measured bottleneck. The compiler availability and
  profiling evidence decide whether to keep, add, or remove memoization.

## Positive Signals

- `react.POS-APP-1`: route/screen component owns workflow state and delegates
  reusable rendering to narrower child components.
- `react.POS-APP-2`: provider tree is explicit, stable, and scoped to values
  that genuinely cross route or feature boundaries.
- `react.POS-APP-3`: form workflow exposes draft, pending, validation,
  server-error, success, retry, and focus-recovery states.
- `react.POS-APP-4`: custom Hooks isolate browser subscriptions or external
  systems and clean up every listener/timer/observer.
- `react.POS-APP-5`: Suspense/loading/error boundaries preserve layout,
  accessible names, and recovery paths.
- `react.POS-APP-6`: Effects synchronize a named external system with cleanup,
  stale-work cancellation, and a Strict Mode-calibrated lifecycle test; derived
  values remain in render and state identity is intentional.

## Smell Codes

- `react.APP-CMP-1`: leaf component owns route navigation, API calls, storage,
  form workflow, cache invalidation, and dense rendering at once.
- `react.APP-STATE-1`: context or external store acts as a hidden event bus
  without reset, selector, or retention rules.
- `react.APP-RENDER-1`: component performs non-idempotent work, DOM mutation,
  or browser reads during render.
- `react.APP-HOOK-1`: Hook call is conditional, nested, behind early return, or
  hidden inside a callback/factory where React cannot preserve call order.
- `react.APP-FORM-1`: controlled/uncontrolled form workflow lacks validation
  timing, server-error mapping, duplicate-submit guard, or focus recovery.
- `react.APP-BROWSER-1`: effect, portal, storage, observer, or global event
  listener has no cleanup, capability fallback, or ownership boundary.
- `react.APP-EFFECT-1`: Effect copies render-derived state, lacks cleanup or an
  `AbortSignal`/stale-result guard for async work, or relies on a lifecycle that
  development-only Strict Mode intentionally replays.
- `react.APP-RSP-1`: component styling relies on fixed viewport/device
  breakpoints, physical properties, hover-only affordances, or brittle heights.
- `react.APP-PERF-1`: bundle, hydration, Suspense, image/font, or script cost
  is treated as verified without browser or RUM evidence.

## Carve-Outs

- Do not flag Context for stable cross-cutting values when update frequency is
  low and provider scope is narrow.
- Do not flag route-owned data loading when the route delegates rendering and
  API contract semantics to narrower components/services.
- Do not require every async screen to use Suspense when the project uses an
  explicit loading-state pattern that preserves layout and recovery behavior.
- Do not flag a component library primitive when rendered DOM evidence confirms
  accessible name, keyboard support, focus behavior, contrast, and target size.
