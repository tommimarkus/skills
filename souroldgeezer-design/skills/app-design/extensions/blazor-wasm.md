# Extension - Blazor WebAssembly App Design

This extension adds Blazor WebAssembly app and component mechanics to the
framework-neutral app-design workflow. It covers standalone Blazor WebAssembly
apps and Blazor Web App `.Client` projects that run interactive WebAssembly
components in the browser.

## Detection Signals

- `*.razor`, `*.razor.css`, or `*.razor.cs` in the target.
- `.csproj` using `Microsoft.NET.Sdk.BlazorWebAssembly`.
- `Program.cs` using `WebAssemblyHostBuilder.CreateDefault(args)`.
- `wwwroot/index.html` referencing `blazor.webassembly.js`.
- Blazor Web App server setup using `AddInteractiveWebAssemblyComponents()` or
  `AddInteractiveWebAssemblyRenderMode()` with a sibling `.Client` project.
- `wwwroot/index.html` or host output referencing `blazor.web.js`.
- `@rendermode`, `InteractiveWebAssembly`, or `InteractiveAuto` directives.

## Scope

Own Blazor-specific app-design interpretation for:

- route and layout ownership in `.razor` files;
- component architecture, component-library reuse, parameters, cascading
  values, event callbacks, and render lifecycle boundaries;
- standalone WASM boot behavior versus Blazor Web App render modes;
- state containers, local component state, browser storage, persistent state,
  optimistic UI, and invalidation surfaces;
- API client placement and the boundary where HTTP contract design delegates to
  `api-design`;
- JS interop modules for browser APIs, dialogs/popovers, viewport preferences,
  storage, and frontend metrics;
- focus restoration, navigation behavior, forms, validation, loading/error
  states, and browser storage;
- responsive layout, CSS isolation, accessibility, i18n, and Core Web Vitals
  posture.

Security review of C# code belongs to `devsecops-audit`; generic C# module
design belongs to `software-design`.

## Project Assimilation

Inspect these Blazor-specific signals after the core app-design assimilation:

- `Program.cs`: hosting model, services, root components, HTTP clients,
  authentication/session services, and render-mode registration.
- `App.razor` / `Components/App.razor`: route table, `Routes`, `HeadOutlet`,
  default `@rendermode`, and global loading/error boundaries.
- `Routes.razor`, `Router`, and `@page` directives: route ownership, layouts,
  `NotFound`, unauthorized handling, route parameters, and lazy assemblies.
- `MainLayout.razor` and `.razor.css`: landmarks, skip link, `<main>`, focus
  restoration, navigation collapse, sticky chrome, and logical CSS.
- Feature `.razor` files: component roles, `Parameter`/`EventCallback`
  contracts, cascading values, edit models, loading/error/empty states, and
  data ownership.
- `.csproj`: package references for MudBlazor, FluentUI Blazor, Radzen,
  Blazorise, AntDesign Blazor, trimming, AOT, lazy-loaded assemblies, and
  scoped CSS configuration.
- `wwwroot/index.html`, `HeadContent`, and host assets: viewport meta,
  `color-scheme`, theme color, preloads, app CSS, script order, service worker,
  and WebAssembly boot posture.
- `wwwroot/js` / `.mjs`: existing JS interop modules for `matchMedia`,
  `visualViewport`, storage, dialogs, and Web Vitals. Extend compliant modules
  instead of adding parallel ones.

Reuse project components and libraries only when they satisfy the core
app-design rule. A library dialog, tooltip, menu, input, or layout primitive is
not compliant merely because it exists.

## App Architecture Defaults

- Standalone Blazor WebAssembly has no server render handoff; every component
  must account for WebAssembly boot and client-only readiness.
- Blazor Web App `.Client` projects can mix static SSR, InteractiveServer,
  InteractiveWebAssembly, and InteractiveAuto. Render mode is an app-design
  decision because it affects first content, hydration, event readiness, and
  bundle cost.
- Route components own route parameters, screen readiness, authorization state,
  and top-level error/empty handling. Leaf components should not own
  navigation, API clients, and validation at the same time.
- Layouts own landmarks, navigation chrome, skip links, focus restoration,
  responsive navigation, and sticky-header offsets.

## Component And State Defaults

- Use `[Parameter]` for inputs and `EventCallback` for user intent. Avoid child
  components mutating parent state or services directly unless they are
  explicitly state-container components.
- Use cascading values sparingly for stable cross-cutting context such as theme,
  auth/user display context, locale, or form context. Do not use them as an
  untraceable event bus.
- Keep edit models and `EditContext` ownership close to the form workflow.
  Surface validation summary, field errors, server errors, disabled/pending
  state, and focus on failure.
- Use state containers only when multiple routes/screens coordinate. State
  containers need reset rules, subscription disposal, and testable mutation
  methods.
- Browser storage access belongs behind a small service that names key owner,
  retention, serialization version, quota/failure behavior, and privacy limits.

## Rendering And Browser Boundaries

- `@rendermode` applies only in Blazor Web App contexts. Do not add render-mode
  directives to standalone WASM components.
- `InteractiveAuto` and `InteractiveWebAssembly` components must live in the
  `.Client` project and must tolerate SSR-to-client handoff when prerendered.
- Persistent state or cached data is required when prerendered content would
  otherwise re-fetch or flicker during hydration.
- JS interop should be module-based (`IJSObjectReference`) and grouped by
  concern. Dispose modules and callbacks.
- Browser-only APIs (`matchMedia`, `visualViewport`, storage, Web Vitals,
  `showModal`, focus helpers) need capability checks and fallback behavior.

## API Client Delegation

Blazor app-design owns where API clients are used in the frontend, how loading
and error state appear, and how mutations affect UI state. Delegate endpoint
shape, problem details, authentication semantics, retries, idempotency,
conditional requests, and API observability to `api-design`.

Smell: a `.razor` leaf component constructs raw request URLs, interprets API
error schemas, owns retry semantics, and renders form fields. Move API contract
semantics behind a client/service boundary and delegate the contract review.

## Focus, Navigation, Forms, And Storage

- Layouts should restore focus to `<main>` or the route heading after
  navigation. Preserve scroll intentionally.
- Dialogs and popovers must be keyboard-operable, restore focus, and avoid
  hiding focused controls under sticky UI.
- `EditForm` workflows need `EditContext`, validation timing, server-error
  mapping, duplicate-submit guards, and visible success/failure recovery.
- Built-in input components must pass through `autocomplete`, `inputmode`,
  `enterkeyhint`, `aria-*`, and `data-*` attributes when those are part of the
  app contract.
- Local/session storage wrappers must handle unavailable storage, quota errors,
  schema migration, and logout/session clearing where relevant.

## Responsive, Accessibility, I18n, And Performance

- Isolated CSS (`*.razor.css`) still needs logical properties, fluid sizing,
  content-derived breakpoints, container queries where components are reused,
  `:focus-visible`, and text-expansion room.
- Component libraries may provide accessible primitives, but theme overrides can
  break contrast, focus visibility, target size, and RTL behavior. Verify the
  actual project configuration.
- Navigation, menus, and dialogs must work with keyboard, touch, coarse/fine
  pointers, reduced motion, forced colors, 400% zoom, and RTL.
- WebAssembly boot, lazy-loaded assemblies, AOT, trimming, image/font loading,
  and JS interop cost affect LCP/CLS/INP posture. Static review can flag
  posture only; runtime metrics require browser tooling or RUM.

## Positive Signals

- `blazor.POS-APP-1`: route component owns route params and delegates
  reusable rendering to child components.
- `blazor.POS-APP-2`: layout contains skip link, landmarks, `<main>`, and route
  focus restoration.
- `blazor.POS-APP-3`: form workflow has `EditContext`, validation summary,
  field-level errors, pending state, and server-error mapping.
- `blazor.POS-APP-4`: JS interop modules are concern-scoped and disposed.
- `blazor.POS-APP-5`: render-mode choice is documented per route or component.
- `blazor.POS-APP-6`: isolated CSS uses logical properties, container-aware
  sizing, and accessible focus states.

## Smell Codes

- `blazor.APP-ROUTE-1`: `@page` route lacks loading/error/empty/unauthorized
  state ownership.
- `blazor.APP-LAYOUT-1`: layout lacks skip link, landmarks, route focus
  restoration, or sticky-header focus offsets.
- `blazor.APP-CMP-1`: leaf `.razor` component owns API calls, storage, form
  workflow, navigation, and dense rendering at once.
- `blazor.APP-STATE-1`: cascading values or state containers act as implicit
  event buses without reset/disposal semantics.
- `blazor.APP-RENDER-1`: render mode or prerender handoff can flicker, double
  fetch, or shift layout.
- `blazor.APP-FORM-1`: `EditForm` lacks validation timing, server-error
  mapping, duplicate-submit guard, or focus recovery.
- `blazor.APP-BROWSER-1`: JS interop or browser storage has no capability
  fallback, disposal, owner, or failure behavior.
- `blazor.APP-RSP-1`: isolated CSS uses physical properties, fixed label
  widths, device breakpoints, bare viewport heights, or hover-only behavior.
- `blazor.APP-PERF-1`: WebAssembly boot, lazy assembly, image/font, or
  interop cost is treated as performance-verified without runtime evidence.

## Carve-Outs

- Do not flag missing native `<dialog>` when a project library dialog provides
  focus trap, escape close, focus restoration, semantic names, and contrast in
  the active theme.
- Do not flag route-owned data loading in a route component when the component
  delegates rendering and API contract semantics to narrower services.
- Do not flag JS interop module reuse across concerns when an existing package
  deliberately centralizes browser interop and exposes stable concern-level
  methods.
- Do not require `@rendermode` in standalone Blazor WebAssembly; it is a Blazor
  Web App concern.
