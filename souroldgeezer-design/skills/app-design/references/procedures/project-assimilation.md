# App Project Assimilation

Load when existing user flows, routes, screens, layouts, components, design
tokens, component libraries, state/data patterns, forms, browser storage,
rendering boundaries, navigation shell, visual/runtime evidence, or diffs are
in scope.

Start from the user's outcome and the project's actual contracts. Bundled
conventions are strong defaults, not authority to redesign a compatible project.
Reuse justified local structure; a reference difference alone is not debt.
Identify concrete incompatibility, unsafe behavior, or a substantiated
maintenance consequence before recommending migration. Factual Extract records
behavior and uncertainty without unsolicited compliance judgments.

## Discovery

Inspect the relevant source-readable locations before deciding; do not require
a complete project inventory for a bounded change:

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

- Preserve compatible local contracts and explain a material departure from a
  reference default once when it changes the recommendation.
- Judge candidate debt by evidence and consequence. Existing debt is fixed only
  within the authorized scope; do not expand a routine task to satisfy a rubric.
- Stop only the affected implementation action when a concrete unsafe or
  incompatible change cannot be avoided within authority. Ask for the material
  decision or propose the smallest safe move; continue independent work.
- Read-only Review reports load-bearing or blocking debt and continues its
  remaining analysis. Missing runtime or human evidence limits the conclusion
  needing it, not unrelated source-grounded findings.

## Footer Block

Use this optional shape for a requested formal report or a real handoff
consumer. Ordinary answers summarize only material reuse, migration, and limits;
they do not need an assimilation inventory or routine debt footer.

```text
Project assimilation:
  Reused: <compatible local routes/components/tokens/state patterns and evidence>
  Legacy debt: <file:line - rule or finding family - reason not migrated>
  Migrations performed: <file:line - rule or finding family fixed>
```
