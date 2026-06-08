# App Design Reference

This reference covers web frontend application design: routes, screens,
component architecture, state and data ownership, rendering boundaries, form
flows, navigation, browser runtime behavior, responsive layout, accessibility,
internationalization, and Core Web Vitals posture.

Responsive design remains a mandatory layer of app design rather than a
standalone public skill.

Use this reference for Build, Extract, Review, and Lookup work. It is not a
scanner rulebook: findings still need evidence, the weakest honest verification
layer, and a smallest useful correction.

## 1. Scope

App design owns the user-facing browser application surface:

- route trees, app shells, layouts, screens, navigation, and history behavior;
- component roles, composition boundaries, props/events/contracts, and reuse;
- local UI state, shared app state, server cache, browser storage, optimistic
  behavior, invalidation, and data-fetching placement;
- server/client rendering boundaries, hydration risks, offline/capability
  constraints, browser APIs, and storage;
- forms, validation, submission, recovery, and error presentation;
- loading, error, empty, offline, unauthorized, and permission states;
- responsive behavior, accessibility, internationalization, visual behavior,
  Core Web Vitals posture, and frontend observability.

## 2. Principles

### 2.1 Workflow before widgets

Start from the user workflow and route/screen boundary. A component split that
looks tidy but hides the workflow state, validation path, or recovery path is
not a good app design.

### 2.2 Ownership is explicit

Every route, screen, component, state object, data cache, form, browser storage
key, and rendering boundary has one owner. Shared ownership must be modeled as
a contract, not a convention.

### 2.3 Baseline layers are mandatory

Responsive behavior, WCAG 2.2 AA posture, keyboard and focus behavior,
internationalization, text expansion, RTL direction, visual state, and Core Web
Vitals posture are design inputs, not late acceptance criteria.

### 2.4 Runtime claims need runtime evidence

Static source can reveal likely design failures, but it cannot prove DOM
behavior, visual layout, accessibility-tool results, real user performance, or
browser runtime behavior. Use the verification layers in §7.

### 2.5 Compose sibling skills

App design delegates HTTP API contracts to `api-design`, engineering-only
decomposition to `software-design`, deployment topology to `infra-design`,
architecture models to `architecture-design`, security posture to
`devsecops-audit`, and test-quality classification to `test-quality-audit`.

## 3. Decision Defaults

### 3.1 Route and screen ownership

Default: each route has a named user intent, one primary screen owner, declared
loading/error/empty/unauthorized states, and a navigation recovery path. Nested
routes own nested workflow state only when the URL can restore that state.

### 3.2 Component roles and composition

Default: split components by role: route/page orchestration, layout shell,
feature container, form/workflow controller, reusable interaction primitive,
and presentational leaf. Avoid components that both fetch data, own browser
storage, validate forms, and render dense layout unless the feature is tiny.

### 3.3 Props, events, and component contracts

Default: parent components pass stable data and explicit callbacks; child
components emit intent, not implementation details. Public component contracts
name loading, disabled, validation, and error states instead of smuggling them
through optional CSS classes.

### 3.4 Local state, shared UI state, server cache, and browser storage

Default: keep ephemeral control state local; share UI state only when multiple
routes/screens coordinate; store server data in a cache with invalidation rules;
use browser storage only for durable user choices or offline drafts. Never use
storage as an implicit cross-component event bus.

### 3.5 Data fetching, invalidation, and optimistic updates

Default: route-level data loads define screen readiness; component-level loads
are for independent islands. Every mutation states invalidation, rollback,
retry, and duplicate-submit behavior. Optimistic UI needs a visible recovery
path and API semantics delegated to `api-design`.

### 3.6 Client/server rendering boundaries and hydration

Default: put content needed for first comprehension as close to initial render
as the stack allows. Hydration-sensitive components must avoid layout shift,
double fetches, duplicate event handlers, and state flicker. Boundary crossings
carry a clear serialization contract.

### 3.7 Form workflow and recovery

Default: forms name field ownership, validation timing, submit disabling,
server-error placement, focus target after failure, unsaved-change behavior,
draft persistence, and success navigation. Use native form semantics and input
hints before custom controls.

### 3.8 Navigation, focus restoration, history, and unsaved changes

Default: navigation restores focus to the new main content, preserves or
resets scroll intentionally, records meaningful state in history, and protects
unsaved work. Sticky app chrome must not obscure keyboard focus.

### 3.9 Loading, error, empty, offline, and unauthorized states

Default: every async surface has a skeleton or progress state, an actionable
error, an empty state that explains next action, offline behavior when relevant,
and an unauthorized state that does not strand the user.

### 3.10 Responsive sizing, layout, and container behavior

Default: design content-first and fluid. Use intrinsic sizing, `clamp()`,
container queries for reusable components, logical properties, content-derived
breakpoints, touch-first target sizing, and mobile-first cascade. Reflow must
work at 320 CSS px without two-dimensional scrolling except where the content
semantically requires it, such as wide data tables with an accessible fallback.

Preserved responsive defaults:

- Use `rem` for type and spacing, `ch` for measure, `%`/`fr` for layout,
  `cqi`/`cqb` inside container contexts, and `dvh`/`svh`/`lvh` for
  viewport-coupled height. Bare `px` belongs only where fixed scale is
  semantically correct, such as borders, canvas coordinates, or chart axes.
- Prefer container queries for components reused in different slots; use
  viewport queries for app-shell decisions such as primary navigation and page
  column count.
- Derive breakpoints from content failure, not named devices. More than a few
  unaligned breakpoints usually means the layout needs fluid primitives.
- Gate hover affordances behind pointer/hover capability checks, keep touch
  targets usable, and provide non-drag alternatives.
- Use logical spacing, sizing, borders, and positioning in new code. Physical
  properties need a written reason.
- Reserve layout space for media with intrinsic dimensions or `aspect-ratio`;
  do not lazy-load the LCP candidate; provide responsive image sources and
  `sizes`.
- Load fonts with layout-stable fallback strategy and script-aware subsets.
- Honor reduced motion, forced colors, color scheme, high contrast, data-saver
  and reduced-data signals where available.
- Prefer Grid for two-dimensional layout and Flexbox for one-dimensional,
  content-driven lists.

### 3.11 Accessibility and WCAG 2.2 AA posture

Default: keyboard operation, focus visibility, focus not obscured, contrast,
non-text contrast, target size, dragging alternatives, text resize/reflow, and
semantic structure are hard requirements. Use accessibility tools for what they
can detect and browser/human checks for interaction and comprehension.

### 3.12 Internationalization and direction

Default: new layout uses logical properties, `lang`, `dir`, text expansion
space, bidi isolation for user content, script-aware wrapping, mirrored
directional affordances, localized formats, and no fixed widths tuned to
English labels.

### 3.13 Core Web Vitals and frontend observability

Default: preserve LCP candidates, prevent CLS with dimensions and stable
containers, protect INP by keeping interactions light, lazy-load non-critical
code, and expose enough frontend telemetry to confirm runtime behavior. Static
review can identify posture, not real p75 outcomes.

### 3.14 Browser capabilities, storage, and network posture

Default: browser APIs are capability-checked, storage has ownership and
retention semantics, offline or degraded-network behavior is explicit, and
Save-Data / reduced-motion / forced-colors preferences are honored where the
platform exposes them.

## 4. Primitives

- **Route map:** URL, screen owner, layout shell, data owner, auth state, and
  recovery path.
- **Screen contract:** workflow goal, loading/error/empty/offline states,
  primary actions, focus target, and visual/responsive constraints.
- **Component contract:** role, inputs, outputs, state ownership, side effects,
  accessibility name/role/state, and validation surface.
- **State map:** local UI state, shared app state, server cache, optimistic
  state, browser storage, invalidation, and reset behavior.
- **Rendering boundary:** static/SSR/client-only/hydrated island, serialized
  data, hydration risk, and first-use readiness.
- **Form contract:** field model, validation timing, submit behavior, recovery,
  focus, draft persistence, and API delegation.
- **Responsive layer:** container behavior, fluid sizing, input modality,
  zoom/reflow, direction, and text expansion.
- **Fluid sizing primitives:** `clamp()`, `min()`, `max()`, intrinsic grid
  tracks, `fit-content`, `minmax()`, `auto-fit`, and `auto-fill`.
- **Container primitives:** `container-type`, named containers, `@container`,
  `cqi`/`cqb`/`cqw`/`cqh`, and component-local layout decisions.
- **Viewport primitives:** `dvh`, `svh`, `lvh`, safe-area `env()` insets, and
  `interactive-widget=resizes-content` for keyboard-aware layouts.
- **Input and preference primitives:** `(hover)`, `(pointer)`,
  `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast`, and
  `forced-colors`.
- **I18n primitives:** logical properties, `:dir()`, `:lang()`, `lang`, `dir`,
  `bdi`, script-aware wrapping, and localized form/date/number formatting.
- **Media primitives:** `srcset`, `sizes`, `picture`, `fetchpriority`,
  `loading`, `decoding`, `aspect-ratio`, font preloads, `font-display`, and
  font metric overrides.
- **Browser-runtime primitives:** `AbortController`, history state, storage,
  service worker/offline state where present, capability checks, and frontend
  telemetry hooks.
- **Verification layer:** `[static]`, `[dom]`, `[behaviour]`, `[visual]`,
  `[a11y-tool]`, `[runtime]`, or `[human]`.

## 5. Patterns

### 5.1 Route-owned screen

The route loads screen data, owns loading/error/empty state, and passes a
screen model to child components. Child components emit user intent back to the
route or feature controller.

### 5.2 App shell with route focus

The shell owns landmarks, skip link, navigation, focus restoration after route
change, sticky chrome offsets, and responsive navigation collapse. Feature
screens do not recreate shell behavior.

### 5.3 Container plus leaf components

A feature container owns data, mutation, and state transitions. Leaf components
own semantics and presentation. This keeps reusable leaves free of API and
browser-storage coupling.

### 5.4 Form workflow controller

A form controller owns edit model, validation, async submit, duplicate-submit
guard, server-error mapping, focus on failure, dirty state, and success
navigation. Field components remain semantic inputs with accessible errors.

### 5.5 Server cache with explicit invalidation

The app identifies query keys, stale times, invalidation after mutation, retry
policy, and optimistic rollback. API contract details remain in `api-design`.

### 5.6 Hydrated island

Render stable content first, hydrate interactive islands later, and preserve
layout dimensions to avoid CLS. If an island cannot be used until JavaScript or
WebAssembly loads, the pending state must be visible and accessible.

### 5.7 Responsive navigation

Navigation remains reachable by keyboard and touch, names current location,
uses content-derived breakpoints, supports text expansion and RTL, and restores
focus after close or route change.

### 5.8 State-specific screen

Loading, error, empty, offline, unauthorized, and permission states are first
class screens or regions with clear user action. Avoid hiding them inside
generic toast-only feedback.

## 6. Smells

- **APP-ROUTE-1:** route has no clear screen owner or user intent.
- **APP-ROUTE-2:** URL cannot restore meaningful workflow state.
- **APP-CMP-1:** component owns unrelated data fetching, storage, validation,
  navigation, and presentation responsibilities.
- **APP-CMP-2:** child component mutates parent or global state without an
  explicit event/contract.
- **APP-STATE-1:** same state is duplicated in local state, shared store, URL,
  and browser storage without a source of truth.
- **APP-DATA-1:** mutation has no invalidation, rollback, retry, or duplicate
  submit rule.
- **APP-RENDER-1:** hydration can re-fetch, flicker, or shift layout.
- **APP-FORM-1:** form errors do not map to fields, summary, focus target, or
  recovery action.
- **APP-NAV-1:** route change leaves keyboard focus behind or hidden under
  sticky UI.
- **APP-UX-1:** loading/error/empty/offline/unauthorized states are missing or
  not actionable.
- **APP-RSP-1:** layout depends on device breakpoints instead of content and
  containers.
- **APP-RSP-2:** fixed label widths, physical properties, or bare viewport
  heights break text expansion, RTL, zoom, or mobile browser chrome.
- **APP-A11Y-1:** interactive control lacks semantic name, keyboard path,
  focus visibility, or target size.
- **APP-I18N-1:** layout assumes English text length, LTR direction, or Latin
  line breaking.
- **APP-PERF-1:** LCP/CLS/INP posture is asserted without runtime evidence.
- **APP-BROWSER-1:** browser storage, network, or capability behavior has no
  ownership or fallback.

Legacy alias: older review output may have used `RD-*` for responsive-only
findings. Treat those as migration aliases to `APP-RSP-*`; new findings use
`APP-*` or extension codes such as `blazor.APP-*`.

## 7. Checklist

- `[static]` Route/screen ownership is named and recoverable from navigation.
- `[static]` Component roles separate orchestration, state, workflow, and
  presentational leaves unless the feature is intentionally tiny.
- `[static]` State/data ownership names local state, shared state, server
  cache, browser storage, invalidation, and optimistic behavior.
- `[static]` Forms declare validation timing, submit behavior, server-error
  placement, dirty state, focus on failure, and success recovery.
- `[static]` Rendering boundaries identify SSR/static/client-only/hydrated
  surfaces and known hydration risks.
- `[static]` Responsive layer uses fluid sizing, logical properties,
  content-derived breakpoints, touch-safe targets, and text-expansion room.
- `[dom]` Landmarks, headings, form associations, dialog/popover structure, and
  live regions exist in the rendered DOM.
- `[behaviour]` Keyboard flow, focus restoration, modal trapping, unsaved
  changes, navigation history, and offline/error recovery work in a browser.
- `[visual]` Layout works at 320 CSS px, 400% zoom, RTL, long text, dark mode,
  forced colors, reduced motion, and representative narrow/wide containers.
- `[a11y-tool]` Text contrast, non-text contrast, accessible names, ARIA
  validity, and common WCAG automation checks pass with the selected tool.
- `[runtime]` LCP, CLS, INP, bundle cost, lazy loading, frontend telemetry, and
  real network/device posture are measured in runtime tooling or RUM.
- `[human]` User workflow, visual hierarchy, content comprehension, affordance
  clarity, and localization quality are understandable to a target user.

## 8. Out of Scope

- Native mobile adaptive design and native cross-platform frameworks.
- Email HTML and print stylesheet policy.
- HTTP API contract design, backend auth semantics, versioning, and reliability.
- Generic helper/library decomposition unrelated to frontend app behavior.
- Hosting topology, environment promotion, IaC, and deployment operations.
- Architecture-model authoring, drift review, and rendered architecture diagrams.
- Security posture review and test-quality classification.
