# App Project Assimilation

Load when existing user flows, routes, screens, layouts, components, design
tokens, component libraries, state/data patterns, forms, browser storage,
rendering boundaries, navigation shell, visual/runtime evidence, or diffs are
in scope.

Direction is one-way: assimilate the project to the app-design reference, not
the reference to the project. Reuse compliant app primitives, flag
non-compliant primitives as legacy debt, and never extend a broken route,
component, state, rendering, or browser pattern into added code.
Discover and classify current user flows, recovery and resumption, layout
family, and adaptive order before proposing a redesign.

## Discovery

Inspect source-readable locations before deciding:

1. Current user flows: actor and goal, entry and observable completion, main
   path, branches, cancellation, external touchpoints, dead ends, and recovery
   and resumption across back, reload, offline, and expired authentication.
2. Route map: route files, layout shells, nested routes, navigation config,
   auth/unauthorized states, and recovery paths.
3. Screen and workflow owners: page/route components, feature containers,
   form controllers, loading/error/empty/offline states, and focus behavior.
4. Layout behavior: content priority, layout family, wide placement, narrow
   adaptive order, DOM/reading/focus order, size constraints, and state-specific
   reflow, reveal, reposition, or presentation changes.
5. Component system: design tokens, theme config, component library, shared
   primitives, public props/events, and existing accessibility semantics.
6. State and data: local UI state, shared app state, server cache/query keys,
   invalidation, optimistic updates, retries, and API delegation points.
7. Browser surface: storage keys, history state, service worker/offline code,
   capability checks, navigation guards, and user preference handling.
8. Rendering and baseline layers: SSR/static/client-only boundaries, hydration
   islands, responsive primitives, WCAG posture, i18n/direction, media/font
   sizing, and frontend observability.
9. Architecture pairing: `docs/architecture/<feature>.dediren/` when route,
   screen, workflow, or ownership changes may affect architecture views.
10. Stack signals: load React, Next.js, or Blazor WebAssembly extensions when
   their manifests, file types, or framework APIs are present.

Loaded extensions own deeper framework-specific discovery and carve-outs.

## Reuse Or Migrate

| Asset | Reuse when | Flag or migrate when |
|---|---|---|
| Route / layout shell | Owns workflow state, landmarks, loading/error recovery, and navigation behavior | Route hides multiple workflows, recreates shell behavior, or strands users on error/unauthorized states |
| Component primitive | Has clear role, stable contract, accessible semantics, and token-compatible styling | Fetches data, owns storage, validates forms, and renders layout without one owner |
| Design tokens / theme | Express project conventions while satisfying responsive, contrast, i18n, and state needs | Fixed English-only widths, inaccessible colors, or tokens that force layout failure |
| State/data pattern | Names owner, invalidation, rollback, retry, and reset behavior | Browser storage acts as event bus or API retry/cache policy is hidden in leaves |
| Rendering boundary | Has serialization contract and avoids avoidable hydration shift/flicker | Broad client boundary, duplicate fetches, or unverified runtime claims |
| Form workflow | Handles validation, duplicate submit, server errors, focus recovery, dirty state, and success navigation | Field components own submission policy or failures have no recovery path |
| Screen/form composition | Order and grouping follow a user task sequence with a clear primary action | Layout mirrors API schema order, ungrouped field dumps, or uniform width/emphasis |
| User flow | Names a user goal, entry, observable completion, branches, recovery, resumption, and external touchpoints | Maps implementation structure, hides dead ends, or cannot explain cancellation, back/reload, and interrupted work |
| Adaptive layout | Keeps region priority and essential content while wide/narrow visual, DOM, reading, and focus order preserve meaning | Supporting content displaces the primary task or adaptive order changes meaning or loses recovery |

## Conflict Handling

Classify conflicts as `reused`, `legacy debt`, `blocking debt`, or
`migration performed`.

- Added app code must comply with the core reference and loaded extensions.
- Existing visual or component conventions can be reused only when they preserve
  responsive, accessibility, i18n, and interaction-state requirements.
- If requested work would depend on or extend blocking debt, stop and ask for
  migration scope or propose the smallest safe app migration move.
- If a legacy pattern is not migrated, name the file, violated rule or finding
  family, and reason it remains out of scope.
- `blocking debt` is a stop-and-ask state, not a footer line: once resolved it is
  disclosed as `Migrations performed` (if migrated) or `Legacy debt` (if the user
  accepts the smallest safe move without migrating). The footer discloses those
  end states; `reused` needs no debt line.

## Footer Block

Use this shape when assimilation applies:

```text
Project assimilation:
  Reused: <compliant local routes/components/tokens/state patterns and evidence>
  Legacy debt: <file:line - rule or finding family - reason not migrated>
  Migrations performed: <file:line - rule or finding family fixed>
```
