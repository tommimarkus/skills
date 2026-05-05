---
name: app-design
description: Use when building, extracting, reviewing, or looking up web frontend application design — routes, screens, component architecture, state and data flow, rendering boundaries, forms, navigation, browser runtime behavior, responsive behavior, accessibility, internationalization, Core Web Vitals posture, and Blazor™ WebAssembly app surfaces without duplicating generic software, API, infrastructure, architecture-model, security-audit, or test-quality specialist skills.
---

# App Design

## Overview

Shape web frontend applications so user workflows, routes, screens,
components, state, data flow, rendering boundaries, browser behavior,
responsive layout, accessibility, internationalization, and performance posture
fit together before implementation or review.

The reference is [../../docs/app-reference/app-design.md](../../docs/app-reference/app-design.md).
This skill is the workflow for applying it. Generated code and design output
embody the reference defaults; review output cites reference sections and
loaded extension codes; the skill never duplicates reference prose.

When changing trigger metadata, workflow behavior, extension selection, source
grounding, or evaluation coverage for this skill, read `references/evals` and
`references/source-grounding.md` first. Keep eval cases synthetic or originally
paraphrased; do not copy external prompts, code, examples, screenshots,
diagrams, or docs into this plugin.

## Non-Goals

- Generic software-engineering design belongs to `software-design`; this skill
  calls on it for decomposition, dependency direction, helper/library
  extraction, state-machine shape, adapter boundaries, and coupling risks
  underneath frontend features.
- HTTP API contracts, auth semantics, versioning, reliability behavior, and API
  observability belong to `api-design`.
- Infrastructure, hosting topology, environment promotion, IaC, runtime
  platform operations, and deployment handoff belong to `infra-design`.
- ArchiMate/OEF models, rendered architecture diagrams, and architecture drift
  belong to `architecture-design`.
- Security posture and test-quality classification belong to `devsecops-audit`
  and `test-quality-audit`.
- Native mobile adaptive design, cross-platform native frameworks, email HTML,
  and print stylesheets are out of scope unless a future extension explicitly
  adds them.

## Modes

### Build Mode

Use for designing or implementing a frontend app feature, route, screen,
component set, form flow, navigation path, interaction, or browser-facing
workflow.

### Extract Mode

Use when adapting to an existing frontend app or when the user asks what app
design already exists.

### Review Mode

Use for frontend app structure, route/screen/component architecture, state/data
behavior, responsive/accessibility/performance posture, and browser runtime
review questions.

### Lookup Mode

Use for narrow app-design questions: component split, route shape, state
placement, loading/error-state pattern, rendering boundary, browser storage, or
responsive/accessibility default.

## Default Dispatch

- Existing frontend app with no requested change: Extract.
- New frontend feature, screen, route, component set, form flow, or interaction:
  Build.
- Existing UI/app code, proposal, or "review/audit/is this sound" wording:
  Review.
- Narrow principle or tradeoff question: Lookup.
- Ambiguous request: ask the user to choose.

## Extensions

Load extensions only when source signals match. Multiple extensions may compose
on the same target.

| Extension | Applies to | Loaded when target matches |
|---|---|---|
| [extensions/blazor-wasm.md](extensions/blazor-wasm.md) | Blazor WebAssembly application and component design | `*.razor` / `*.razor.css` / `*.razor.cs`, `.csproj` with `Microsoft.NET.Sdk.BlazorWebAssembly`, Blazor Web App `.Client` projects, `AddInteractiveWebAssemblyComponents()` / `AddInteractiveWebAssemblyRenderMode()`, `wwwroot/index.html` referencing `blazor.webassembly.js` / `blazor.web.js`, or `@rendermode` directives |

Unknown stacks proceed with the core reference only. Extensions never override
core rules.

## Pre-Flight

Before Build, Extract, or Review:

1. Identify mode and frontend scope: app, route, screen, component set,
   workflow, or narrow question.
2. Identify app type: SPA, MPA, SSR, static, hosted app shell, embedded widget,
   or unknown.
3. Detect framework/runtime and load matching extensions. Unknown stacks
   proceed with the core reference only.
4. Identify user workflow and route/screen boundary.
5. Identify component architecture scope and component ownership.
6. Identify state/data ownership: local state, shared UI state, server cache,
   browser storage, API data, optimistic behavior, and invalidation.
7. Identify rendering and browser boundaries: server/client split, hydration,
   offline/capability constraints, storage, navigation, and history behavior.
8. Treat responsive behavior, accessibility, i18n, and Core Web Vitals posture
   as mandatory baseline checks.
9. Check API pairing and delegate to `api-design` when API contract behavior is
   in scope.
10. Check architecture pairing at `docs/architecture/<feature>.oef.xml` and
    delegate model drift to `architecture-design` when present.
11. Check whether an engineering slice needs `software-design` support.

If required user, workflow, route, data, rendering, or validation constraints
are missing and materially change the design, ask. Otherwise default to the
smallest coherent app design and disclose assumptions.

## Project Assimilation

Assimilation is one-way: the project is brought up to the reference; the
reference is not weakened to match local drift.

Before Build, Extract, or Review in an existing repo, inspect source-readable
signals for routes, screens, component libraries, state stores, data-fetching
clients, form primitives, browser storage, routing/navigation primitives,
layout/theme tokens, responsive/accessibility primitives, i18n setup, build
configuration, and frontend observability.

Reuse compliant project infrastructure and names. Flag non-compliant
infrastructure as legacy debt. If legacy debt is load-bearing for the requested
change, halt and ask whether to expand scope or choose a smaller safe change.

## Build Workflow

1. Run Pre-Flight and Project Assimilation; load matched extensions.
2. Read the relevant sections of
   [../../docs/app-reference/app-design.md](../../docs/app-reference/app-design.md):
   Principles, Decision Defaults, matching Patterns, and Checklist.
3. Define the user workflow, route/screen map, component roles, state/data
   flow, rendering boundary, browser behavior, and interaction states before
   writing or changing code.
4. Reuse compliant route, token, form, component-library, state, data-fetching,
   navigation, and observability primitives. Do not copy broken legacy patterns
   into new code.
5. Apply the responsive, accessibility, i18n, and Core Web Vitals layers as
   baseline requirements, not optional polish.
6. Delegate API contract design, architecture-model drift, security posture,
   test-quality classification, or generic engineering-only design to sibling
   skills.
7. Validate only what the available layer supports; never claim browser
   behavior, visual quality, accessibility-tool results, or real Core Web
   Vitals from static source alone.
8. Emit the footer.

Output shape:

```text
Mode: Build
Scope:
User workflow:
Routes / screens:
Component architecture:
State and data flow:
Rendering and browser boundaries:
Interaction states:
Responsive / accessibility / i18n / performance layer:
Validation step:
Delegations:
Footer:
```

## Extract Workflow

1. Run Pre-Flight and Project Assimilation; load matched extensions.
2. Inspect source-readable signals for routes, layouts, screens, component
   ownership, state/data ownership, rendering boundaries, forms, navigation,
   storage, loading/error/empty/offline/unauthorized states, responsive
   primitives, accessibility posture, i18n setup, and performance posture.
3. Separate confirmed app-design structure from assumptions and missing
   runtime evidence.
4. Identify legacy debt only when it affects the requested app-design surface.
5. Name the next smallest coherent move and any sibling-skill delegation.
6. Emit the footer.

Output shape:

```text
Mode: Extract
Scope:
Signals inspected:
Route and screen map:
Component ownership map:
State and data ownership:
Rendering boundaries:
Responsive / accessibility / i18n / performance baseline:
Legacy debt:
Next smallest move:
Delegations:
Footer:
```

## Review Workflow

1. Run Pre-Flight and Project Assimilation; load matched extensions.
2. Inspect the target route, screen, component set, state/data path, rendering
   boundary, forms, navigation, browser behavior, and mandatory responsive /
   accessibility / i18n / performance layers.
3. Use the reference Checklist and Smells as the finding source. Use `APP-*`
   as the primary namespace and extension codes such as `blazor.APP-*` when a
   loaded extension owns the signal.
4. Assign the weakest honest verification layer for each claim: `static`,
   `dom`, `behaviour`, `visual`, `a11y-tool`, `runtime`, or `human`.
5. Block only when the design likely creates unusable user flows, inaccessible
   or unresponsive required behavior, broken route/component ownership,
   state/data ambiguity, unsafe rendering boundaries, or app runtime behavior
   that cannot be validated before release.
6. Delegate findings outside app-design ownership instead of stretching this
   skill to cover them.
7. Emit the footer.

Per finding:

```text
[APP-<family>-<n>] <file>:<line>
  bucket:   routes | components | state | data | rendering | forms | navigation | ux-states | responsive | accessibility | i18n | performance | browser-runtime | evolution
  layer:    static | dom | behaviour | visual | a11y-tool | runtime | human
  severity: block | warn | info
  evidence: <short snippet or observed structure>
  action:   <smallest useful app-design correction>
  ref:      app-design.md section <n.m> + extension code when applicable
```

## Lookup Workflow

1. Confirm the question is narrow enough for Lookup; otherwise switch to Build,
   Extract, or Review.
2. Load only the matching reference section and any extension section required
   by the stack.
3. Answer briefly with the default, the tradeoff, and the reference section.
4. Include a one-line footer.

## Delegation Boundaries

- `software-design`: decomposition, dependency direction, helper/library
  extraction, state-machine shape, adapter boundaries, and coupling risks
  underneath frontend features.
- `api-design`: HTTP contracts, API auth semantics, versioning, retries,
  idempotency, problem details, and backend/API observability.
- `infra-design`: hosting, deployment topology, environment promotion, IaC,
  runtime platform operations, and operational handoff.
- `architecture-design`: ArchiMate/OEF models, architecture drift, rendered
  diagrams, and reverse lookup to business processes.
- `devsecops-audit`: security posture, secrets, supply chain, and CI/CD
  hardening.
- `test-quality-audit`: unit, integration, and E2E test-quality findings.

## Footer

Every mode emits:

```text
Mode:
Extensions loaded:
Reference path: souroldgeezer-design/docs/app-reference/app-design.md
Verification layers used:
Project assimilation:
Delegations:
Limits:
```
