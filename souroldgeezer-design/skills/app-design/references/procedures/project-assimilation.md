# App Project Assimilation

Load when existing routes, screens, layouts, components, design tokens,
component libraries, state/data patterns, forms, browser storage, rendering
boundaries, navigation shell, visual/runtime evidence, or diffs are in scope.

Direction is one-way: assimilate the project to the app-design reference, not
the reference to the project. Reuse compliant app primitives, flag
non-compliant primitives as legacy debt, and never extend a broken route,
component, state, rendering, or browser pattern into added code.

## Discovery

Inspect source-readable locations before deciding:

1. Route map: route files, layout shells, nested routes, navigation config,
   auth/unauthorized states, and recovery paths.
2. Screen and workflow owners: page/route components, feature containers,
   form controllers, loading/error/empty/offline states, and focus behavior.
3. Component system: design tokens, theme config, component library, shared
   primitives, public props/events, and existing accessibility semantics.
4. State and data: local UI state, shared app state, server cache/query keys,
   invalidation, optimistic updates, retries, and API delegation points.
5. Browser surface: storage keys, history state, service worker/offline code,
   capability checks, navigation guards, and user preference handling.
6. Rendering and baseline layers: SSR/static/client-only boundaries, hydration
   islands, responsive primitives, WCAG posture, i18n/direction, media/font
   sizing, and frontend observability.
7. Architecture pairing: `docs/architecture/<feature>.dediren/` when route,
   screen, workflow, or ownership changes may affect architecture views.
8. Stack signals: load React, Next.js, or Blazor WebAssembly extensions when
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

## Footer Block

Use this shape when assimilation applies:

```text
Project assimilation:
  Reused: <compliant local routes/components/tokens/state patterns and evidence>
  Legacy debt: <file:line - rule or finding family - reason not migrated>
  Migrations performed: <file:line - rule or finding family fixed>
```
