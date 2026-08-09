---
name: app-design
description: >-
  Use when building, extracting, reviewing, or looking up frontend app design: routes/screens, components, state/data flow, rendering, forms, navigation, browser behavior, responsive/a11y/i18n/performance, Vite, React, Next.js, and Blazor™ WebAssembly. Defer software, API, infra, architecture, security, and test-quality work.
---

# App Design

## Purpose

Shape frontend app workflows, routes, components, state/data, rendering, browser
behavior, and baseline layers. Use
[../../docs/app-reference/app-design.md](../../docs/app-reference/app-design.md).

## Contract

Own Build, Extract, Review, and Lookup for frontend workflows, routes/screens,
components, state/data, forms, navigation, rendering, browser runtime,
interaction states, and responsive/a11y/i18n/performance.

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

Load what applies: core reference principles/defaults/checklist;
[references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
when existing routes, screens, layouts, components, design tokens, state/data
patterns, forms, browser storage, rendering boundaries, navigation shell,
runtime evidence, or diffs are in scope;
[extensions/vite.md](extensions/vite.md) for `vite.config.*`, `vite` scripts,
`import.meta.env`, Vite entry/build/SSR/worker signals, and load it before the React extension;
[extensions/react.md](extensions/react.md) for React component, hook, state,
rendering, hydration, or browser-runtime signals; [extensions/nextjs.md](extensions/nextjs.md)
for Next.js App Router or Pages Router app surfaces, and load it after the React extension;
[extensions/blazor-wasm.md](extensions/blazor-wasm.md) for `*.razor`, Blazor
WebAssembly project/host/render-mode signals, or Blazor app-shell/component
work; [extensions/README.md](extensions/README.md) only when editing extensions.
Unknown stacks use core only.

<!-- lean-audit:sync-intentional -->
The four stack extensions above load for Build, Extract, and Review — every
extension whose detection signals match the in-scope stack. In Lookup, do not
load full stack extensions on detection alone: answer from the core reference
matched section, and pull a single stack extension only when the question is
specifically about that stack's runtime mechanics. Vite + React loads Vite then React; React + Next.js stays React then Next.js. Vite works alone. In Lookup,
if an answer needs a composed stack pair, load in that order; never load the
whole detected-stack set. If it genuinely needs more than the matching pair's
mechanics, escalate to Review or Build (which load every matching extension) or
ask — do not under-answer from a single extension.

Before changing trigger metadata, workflow, extension selection, grounding, or
evals, load [references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md); keep evals
synthetic/paraphrased.

## Workflow

1. Select mode, scope, app type, workflow, route/screen boundary, and question.
2. Prefer `rg`; inspect inputs, detect runtime, load and announce extensions.
3. Assimilate routes, layouts, screens, components, state/data, forms, storage,
   navigation, baseline primitives, build config, observability; apply project
   assimilation before generating, reviewing, migrating, or extending app
   structure.
4. Check for a paired `docs/architecture/<feature>.dediren/` package when app
   route, screen, or workflow changes may affect architecture views.
5. Separate fact from inference, choose the smallest move, include available
   validation, then emit contract/footer.

## Mode Outputs

- Build: workflow, routes/screens, components, state/data, rendering/browser,
  interaction states, baselines, validation, delegations.
- Extract: signals, route/screen map, ownership, rendering, baselines, debt,
  next move.
- Review: actionable findings only; `block` unusable/inaccessible/unresponsive
  flow, broken route/component ownership, state/data ambiguity, unsafe rendering,
  or unvalidated runtime behavior.
- Lookup: default, tradeoff, citation, delegation, one-line footer.

Every final answer reports mode, extensions, reference path, verification layer
(`static`, `dom`, `behaviour`, `visual`, `a11y-tool`, `runtime`, `human`),
assimilation, delegations, and limits. Findings use
`[APP-<family>-<n>] <file>:<line>` with bucket, layer, severity, evidence,
action, and citation. If none, say so with limits.

## Stop Conditions
<!-- lean-audit:sync-intentional -->

Stop when source/scope is missing, sibling ownership dominates, required
runtime/visual/a11y/performance evidence is absent, load-bearing debt has no
smaller safe move, extension validation is unavailable, or output would copy a
broken legacy route/component/state/rendering pattern.
