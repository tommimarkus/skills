---
name: app-design
description: >-
  Use when building, extracting, reviewing, or looking up frontend app design: routes/screens, user-flow mapping, adaptive screen layout, components, state/data flow, rendering, forms, navigation, browser behavior, responsive/a11y/i18n/performance, Vite, React, Next.js, and Blazor™ WebAssembly. Defer software, API, infra, architecture, security, and test-quality work.
---

# App Design

## Purpose

Shape frontend app user flows, routes, adaptive screen layouts, components,
state/data, rendering, browser behavior, and baseline layers. Use
[../../docs/app-reference/app-design.md](../../docs/app-reference/app-design.md).

## Contract

Own Build, Extract, Review, and Lookup for frontend user-flow mapping,
routes/screens, adaptive screen layout, components, state/data, forms,
navigation, screen composition, rendering, browser runtime, interaction states,
and responsive/a11y/i18n/performance.

Delegate engineering/API/infra/ArchiMate/security/test-quality to
`software-design`, `api-design`, `infra-design`, `architecture-design`,
`devsecops-audit`, and `test-quality-audit`.
When a paired architecture model exists, the coupling path is
`docs/architecture/<feature>.dediren/`.

Inputs: files, diffs/proposals, workflow, route/screen, state/data/rendering
constraints, and runtime/visual/a11y/performance evidence. Do not infer browser,
visual, a11y-tool, performance, or user facts from static source. If ambiguous,
ask the user when mode, scope, workflow, evidence cost, destructive edits, or
sibling ownership lack a safe default; otherwise continue.

Modes: Build new/refactored app design; Extract existing design; Review app
code/PRs/proposals/plans; Lookup app tradeoffs.

## Load Map

Read relevant core principles/defaults/checklist sections and these procedures
when they inform the decision:
[references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
when existing routes, screens, layouts, components, design tokens, state/data
patterns, forms, browser storage, rendering boundaries, navigation shell,
runtime evidence, or diffs are in scope;
[references/procedures/layout-and-flow.md](references/procedures/layout-and-flow.md)
for Build, Extract, or Review involving a multi-screen flow, material layout
redesign, dashboard/workspace composition, or unresolved layout direction,
including substantial work with an approved direction. Keep flow analysis
proportionate; routine component/state work and narrow approved-layout changes
can skip the procedure. Approved direction skips alternatives. For authorized
implementation, choose a sensible reversible layout unless the user requests
selection or a material product decision cannot safely be inferred;
the [operation-feedback default](../../docs/app-reference/app-design.md#39-loading-error-empty-offline-and-unauthorized-states)
for an operation that crosses about one second, and keep its
status, progress semantics, cancellation/recovery, and blocking decision in the
flow-state contract;
[extensions/vite.md](extensions/vite.md) for `vite.config.*`, `vite` scripts,
`import.meta.env`, Vite entry/build/SSR/worker signals, and load it before the React extension;
[extensions/react.md](extensions/react.md) for React component, hook, state,
rendering, hydration, or browser-runtime signals; [extensions/nextjs.md](extensions/nextjs.md)
for Next.js App Router or Pages Router app surfaces, and load it after the React extension;
[extensions/blazor-wasm.md](extensions/blazor-wasm.md) for `*.razor`, Blazor
WebAssembly project/host/render-mode signals, or Blazor app-shell/component
work; [extensions/README.md](extensions/README.md) only when editing extensions.
Unknown stacks use core only.

Detection identifies available guidance. In every mode, read only relevant core
and extension sections; expand for dependencies, uncertainty, or material risk.
Lookup may combine multiple needed stack excerpts without changing mode or
asking merely because more than one stack is involved. Vite precedes React, and React precedes Next.js, when their combined mechanics
are relevant. Vite works alone.

Before changing trigger metadata, workflow, extension selection, grounding, or
evals, load [references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md); keep evals
synthetic/paraphrased.

## Workflow

1. Select mode, scope, actor outcome, app type, workflow, route/screen boundary,
   and question.
2. Prefer `rg`; inspect inputs, detect runtime, read relevant extension sections.
3. Assimilate user flows, routes, layouts, screens, components, state/data,
   forms, storage, navigation, screen composition, baseline primitives, build
   config, and observability; apply project assimilation before generating,
   reviewing, migrating, or extending app structure.
4. When layout-and-flow guidance applies, derive screens from the user flow and
   preserve relevant route, state, layout, DOM, reading, and focus-order links.
   Use alternatives or formal traceability artifacts when they help the task;
   do not pause routine reversible design choices for approval.
   Classify operations that cross about one second, including housekeeping, by
   their status onset, total, blocking scope, terminal transition, and recovery.
5. Check for a paired `docs/architecture/<feature>.dediren/` package when app
   route, screen, or workflow changes may affect architecture views.
6. Separate fact from inference, choose the smallest move, include available
   validation, then report the result and material limits.

## Mode Outputs

- Build: workflow, target flow map, routes/screens, components, state/data,
  rendering/browser, interaction states, screen composition, rough alternatives
  when required, selected layout contract, responsive transformation, baselines,
  validation, delegations.
- Extract: relevant current flow, entry/exit points, recovery and resumption,
  routes, ownership, and rendering facts. Add debt judgments only when requested.
- Review: actionable findings with concrete usability, accessibility, ownership,
  state, or rendering consequences. Missing runtime evidence limits the claim
  requiring it; it does not itself block a source-only review. Locate layout
  findings in the affected source, flow step, or region.
- Lookup: default, tradeoff, citation, delegation, one-line footer.

Lead with the result, relevant findings or changes, validation, and material
limits. Keep Lookup direct. Give a detailed mode/extension/layer/assimilation
inventory only when requested or needed by an actual consumer. Formal findings
retain their defined codes, file evidence, severity, consequence, and action;
omit unused fields and routine negative disclosures.

## Stop Conditions

<!-- lean-audit:sync-intentional: App and infra entries each retain the capability/evidence boundary inline so independently selected skills need not load one another. -->
<!-- lean-audit:sync-intentional -->

Stop the affected action when authority or essential evidence is missing, or
when it would introduce a concrete unsafe or incompatible change. Disclose the
limited conclusion and continue useful independent work. Missing runtime,
visual, a11y, performance, or cloud evidence limits only the claim requiring it;
a reference difference or unavailable optional tool is not itself a task stop.
