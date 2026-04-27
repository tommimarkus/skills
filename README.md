# souroldgeezer

Claude Code and Codex plugin marketplace by Sour Old Geezer. Currently ships two plugins:

- **souroldgeezer-audit** — rubric-driven audits for DevSecOps posture and
  test quality, with per-stack extensions and matching Claude Code subagents.
- **souroldgeezer-design** — reference-driven design for sustainable software,
  modern web UIs, serverless HTTP APIs, and ArchiMate® architecture models. For
  software design (build, extract, review, lookup): shapes code/module
  boundaries, dependency direction, responsibility placement, semantic
  coherence, coupling control, and evolutionary design, with a .NET™ extension.
  For UIs (build, review, lookup): enforces W3C® WCAG™ 2.2 AA,
  internationalization (LTR + RTL + text expansion), and Core Web Vitals, with
  a Blazor™ WebAssembly extension. For serverless APIs (build, review,
  lookup): enforces security (Microsoft® Entra ID™ / managed identities /
  Azure® Key Vault™ / data-plane RBAC), contract discipline
  (OpenAPI™ 3.1, RFC 9457 problem+json), reliability (idempotency,
  429 + Retry-After), and observability (structured logs, W3C® traceparent),
  with composable extensions for Azure® Functions™ on .NET™, Azure® Cosmos DB™,
  and Azure® Blob Storage™. For architecture (build, extract, review, lookup): enforces
  ArchiMate® 3.2 layer discipline and Appendix B relationship well-formedness;
  serialises models as **OEF XML** per The Open Group ArchiMate® Model
  Exchange File Format 3.2 (loadable in ArchiMate®-conformant tools);
  lifts Application + Technology + Implementation & Migration layers from
  .NET™ / Bicep™ / GitHub Actions™ and the Business layer's Process / Event /
  Interaction from Durable Functions + Logic Apps (as `LIFT-CANDIDATE`s the
  architect confirms); marks the rest of Business and all Motivation /
  Strategy as forward-only; supports macro Business Process Cooperation and
  UI-aware Service Realization diagram kind (§9.3 Process-rooted modality); dispatches from the sibling
  skills' Review mode to flag drift between code and the architect's
  model. Each skill has a matching Claude Code subagent; Codex consumes the
  bundled `skills/**/SKILL.md` workflows directly from the plugin.

## Install

### Claude Code

Add this marketplace and enable the plugins you want:

```
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
```

Or, for local development against a clone:

```json
// ~/.claude/settings.json
{
  "extraKnownMarketplaces": {
    "souroldgeezer": {
      "source": { "source": "directory", "path": "/absolute/path/to/skills" }
    }
  },
  "enabledPlugins": {
    "souroldgeezer-audit@souroldgeezer": true,
    "souroldgeezer-design@souroldgeezer": true
  }
}
```

### Codex

Codex can read the same Claude-style repo marketplace at
`.claude-plugin/marketplace.json`. Add the marketplace, then open the plugin
browser and install or enable the plugins you want:

```
codex plugin marketplace add tommimarkus/skills
codex
/plugins
```

For local development against a clone, pass the clone root as the marketplace
source:

```
codex plugin marketplace add /absolute/path/to/skills
codex
/plugins
```

The repo intentionally does not duplicate the catalog under
`.agents/plugins/marketplace.json`; the existing `.claude-plugin/marketplace.json`
is the shared marketplace for both Claude Code and Codex.

### Documentation Basis

This packaging is cross-checked against both runtime doc sets. Claude Code's
documented surfaces are `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `skills/`, and plugin-root `agents/`; Codex
adds `.codex-plugin/plugin.json`, consumes the same bundled
`skills/**/SKILL.md` workflows, reads optional per-skill
`skills/<skill>/agents/openai.yaml` metadata, and supports project-scoped
custom agents in `.codex/agents/*.toml`. Codex currently also documents support
for reading a Claude-style repo marketplace at
`.claude-plugin/marketplace.json`, which is why this repo keeps one shared
catalog instead of adding `.agents/plugins/marketplace.json`.

Primary references: Claude Code [plugin creation](https://code.claude.com/docs/en/plugins),
[marketplace distribution](https://code.claude.com/docs/en/plugin-marketplaces),
and [plugin reference](https://code.claude.com/docs/en/plugins-reference);
Codex [plugins](https://developers.openai.com/codex/plugins),
[plugin building](https://developers.openai.com/codex/plugins/build),
[skills](https://developers.openai.com/codex/skills), and
[subagents](https://developers.openai.com/codex/subagents).

## What's in `souroldgeezer-audit`

Two audit skills, each with a matching one-shot Claude Code subagent:

| Skill | Audits | Stack extensions |
|---|---|---|
| [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | Pipelines, IaC, release artifacts, code-level security smells | [bicep](souroldgeezer-audit/skills/devsecops-audit/extensions/bicep.md), [dockerfile](souroldgeezer-audit/skills/devsecops-audit/extensions/dockerfile.md), [dotnet-security](souroldgeezer-audit/skills/devsecops-audit/extensions/dotnet-security.md), [github-actions](souroldgeezer-audit/skills/devsecops-audit/extensions/github-actions.md) |
| [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | Unit, integration, and E2E test quality (dispatches on detected test type) | [dotnet-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [dotnet-core](souroldgeezer-audit/skills/test-quality-audit/extensions/dotnet-core.md); [nodejs-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [nodejs-core](souroldgeezer-audit/skills/test-quality-audit/extensions/nodejs-core.md); [nextjs-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [nextjs-core](souroldgeezer-audit/skills/test-quality-audit/extensions/nextjs-core.md) (strict superset of nodejs) |

Claude Code subagents live alongside in [souroldgeezer-audit/agents/](souroldgeezer-audit/agents/)
and invoke the same skills, making them usable as delegated one-shots. Codex
installs the bundled skills through the plugin manifest, reads per-skill
metadata from each `skills/<name>/agents/openai.yaml`, and has matching
project-scoped custom-agent wrappers in [.codex/agents/](.codex/agents/).

## What's in `souroldgeezer-design`

Four design skills, each with a matching one-shot Claude Code subagent:

| Skill | Covers | Stack extensions |
|---|---|---|
| [software-design](souroldgeezer-design/skills/software-design/SKILL.md) | Sustainable software design for code/module changes - Build, Extract, Review, and Lookup across boundary placement, dependency direction, responsibility assignment, semantic coherence, coupling control, evolutionary design, lightweight tradeoffs, and socio-technical fit | [.NET™](souroldgeezer-design/skills/software-design/extensions/dotnet.md) (solution/project references, namespaces, assembly visibility, dependency injection, persistence model leakage, hosted services, and common .NET™ design ceremony) |
| [responsive-design](souroldgeezer-design/skills/responsive-design/SKILL.md) | Modern responsive web UI in HTML / CSS / JS — enforces WCAG 2.2 AA, internationalization (LTR + RTL + text expansion), and Core Web Vitals (LCP / CLS / INP) as hard baselines | [blazor-wasm](souroldgeezer-design/skills/responsive-design/extensions/blazor-wasm.md) (covers both standalone Blazor WebAssembly and Blazor Web App `.Client` hosting) |
| [serverless-api-design](souroldgeezer-design/skills/serverless-api-design/SKILL.md) | Modern serverless HTTP APIs — enforces security (Entra ID / managed identities / Key Vault / data-plane RBAC, `disableLocalAuth`, `allowSharedKeyAccess=false`), contract discipline (OpenAPI 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 ETag), reliability (idempotency on mutations, safe retries, 429 + Retry-After, poison / dead-letter), and observability (structured logs, W3C traceparent, correlation ID, RU / request-charge visibility) as hard baselines | [azure-functions-dotnet](souroldgeezer-design/skills/serverless-api-design/extensions/azure-functions-dotnet.md), [azure-cosmosdb](souroldgeezer-design/skills/serverless-api-design/extensions/azure-cosmosdb.md), [azure-blob-storage](souroldgeezer-design/skills/serverless-api-design/extensions/azure-blob-storage.md) — **compose** on the same target |
| [architecture-design](souroldgeezer-design/skills/architecture-design/SKILL.md) | ArchiMate® 3.2 enterprise / solution architecture models — enforces ArchiMate® 3.2 layer discipline, relationship well-formedness, Core-vs-extension defaults, and professional OEF/view readiness (`model-valid`, `diagram-readable`, `review-ready`); serialised as **OEF XML** (ArchiMate® Model Exchange File Format), loadable in ArchiMate®-conformant tools. 4-mode shape: Build (intent → model), Extract (code + IaC + workflows → model with per-layer lifting; Business Process / Event / Interaction lift from Durable Functions + Logic Apps as `LIFT-CANDIDATE`s, rest of Business / Motivation / Strategy are forward-only), Review (professional readiness, artefact findings, and drift detection including process drift against current repo state), Lookup (notation Q&A, domain discovery, reverse lookup from code or UI symbol → owning process) | Per-input-source lifting procedures (not extensions): [.NET](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-dotnet.md), [Bicep](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-bicep.md), [GitHub Actions](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-gha.md), [Durable Functions + Logic Apps](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-process.md), plus [professional-readiness](souroldgeezer-design/skills/architecture-design/references/procedures/professional-readiness.md) and the deterministic [Sugiyama-v1 three-tier layout engine](souroldgeezer-design/skills/architecture-design/references/procedures/layout-strategy.md) introduced in 0.8.0 (Tier 0 architect-position preservation; Tier 1 cycle handling, layered ordering, A* edge routing, bbox normalisation; Tier 2 per-viewpoint specialisations: hosting tower / hub-and-spoke / Plateau timeline / tile grid / Process-rooted realisation stack / Motivation tree / process-flow lanes) invoked by Build / Extract and restated as `AD-Q*` / `AD-L*` / `AD-B-*` checks in Review |

References live at [souroldgeezer-design/docs/software-reference/software-design.md](souroldgeezer-design/docs/software-reference/software-design.md), [souroldgeezer-design/docs/ui-reference/responsive-design.md](souroldgeezer-design/docs/ui-reference/responsive-design.md), [souroldgeezer-design/docs/api-reference/serverless-api-design.md](souroldgeezer-design/docs/api-reference/serverless-api-design.md), and [souroldgeezer-design/docs/architecture-reference/architecture.md](souroldgeezer-design/docs/architecture-reference/architecture.md).
Matching Claude Code subagents are at [souroldgeezer-design/agents/software-design.md](souroldgeezer-design/agents/software-design.md), [souroldgeezer-design/agents/responsive-design.md](souroldgeezer-design/agents/responsive-design.md), [souroldgeezer-design/agents/serverless-api-design.md](souroldgeezer-design/agents/serverless-api-design.md), and [souroldgeezer-design/agents/architecture-design.md](souroldgeezer-design/agents/architecture-design.md). Codex installs the bundled skills through the plugin manifest, reads per-skill metadata from each `skills/<name>/agents/openai.yaml`, and has matching project-scoped custom-agent wrappers in [.codex/agents/](.codex/agents/).

The canonical path `docs/architecture/<feature>.oef.xml` remains the coupling mechanism for UI/API code-to-architecture drift: `responsive-design` and `serverless-api-design` auto-dispatch to `architecture-design` Review when a paired model is present.

## How the audits work

- **Rubric-driven.** The skills are *workflows* that apply an external rubric.
  Findings cite smell codes (e.g. `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`); the prose
  lives in the rubric, not in the skill.
- **Rubric ships with the plugin.** No setup in the audited repo required. The
  rubric docs live at:
  - [souroldgeezer-audit/docs/security-reference/devsecops.md](souroldgeezer-audit/docs/security-reference/devsecops.md) for `devsecops-audit`
  - [souroldgeezer-audit/docs/quality-reference/unit-testing.md](souroldgeezer-audit/docs/quality-reference/unit-testing.md) (and siblings for integration / E2E) for `test-quality-audit`

  The skill reads these by relative path from its own location, so they travel
  with the installed plugin.
- **Quick vs Deep modes.** Every audit exposes both. *Quick* = single file or PR
  diff, per-finding output. *Deep* = whole-repo, sectioned rollup, optional MCP
  live-state probes. If the request is ambiguous, the skill asks.
- **Per-stack extensions.** Detected on demand. Extensions **add** namespaced
  smells or **carve out** core smells for idiomatic framework patterns — they
  never override core rules. See each skill's `extensions/README.md` for the
  authoring convention.
- **Disclosure footer.** Every report ends with a footer listing which
  extensions loaded, MCP availability, cost stance (where applicable), and the
  rubric path. This is how you audit the auditor.

## How `responsive-design` works

- **Reference-driven.** Like the audit skills, it's a workflow that applies
  an external reference. Output cites reference sections (e.g. `§3.11`,
  `§5.8`) and WCAG Success Criteria (e.g. `SC 1.4.10`, `SC 2.5.8`); the
  prose lives in the reference, not in the skill.
- **Three modes.** **Build** produces code embodying the reference's
  decision defaults. **Review** walks the §7 checklist and emits per-finding
  output. **Lookup** answers a narrow question with a citation. If the
  request is ambiguous, the skill asks.
- **Verification-layer tags.** Every §7 checklist item carries a tag —
  `[static]` (grep / lint), `[dom]` (DevTools / Playwright), `[behaviour]`
  (keyboard / focus / interaction), `[visual]` (RTL / theme / zoom /
  non-Latin), `[a11y-tool]` (axe / Pa11y / Lighthouse), `[runtime]`
  (RUM / CrUX / Lighthouse-CI). The skill never claims a runtime
  Core Web Vitals pass from a static review.
- **Project assimilation — one-way.** Used in an existing project, the
  skill pulls the project *up to* the reference. New code is always
  reference-compliant; compliant existing infrastructure is reused;
  non-compliant infrastructure is flagged as legacy debt, never silently
  extended.
- **Per-stack extensions.** `blazor-wasm` covers both standalone Blazor
  WebAssembly and Blazor Web App `.Client` projects, plus component-library
  reuse rules (MudBlazor / FluentUI Blazor / Radzen / Blazorise — reuse
  conditional on each library's primitive actually satisfying the
  reference rule it would replace).
- **Disclosure footer.** Every output ends with a footer listing which
  extensions loaded, self-check counts by verification layer,
  project-assimilation summary (tokens reused, legacy debt flagged,
  migrations performed), and the reference path.

## How `serverless-api-design` works

- **Reference-driven.** Same shape as `responsive-design` — a workflow
  applying an external reference. Output cites reference sections (e.g.
  `§3.6`, `§5.6`), RFCs (`RFC 9457`, `RFC 9110`), and MSFT Learn slugs;
  extension-specific findings cite extension codes (`afdotnet.HC-11`,
  `cosmos.HC-4`, `blob.HC-2`). The prose lives in the reference
  ([souroldgeezer-design/docs/api-reference/serverless-api-design.md](souroldgeezer-design/docs/api-reference/serverless-api-design.md)),
  not in the skill.
- **Three modes.** **Build** produces OpenAPI fragments + handler code +
  `Program.cs` DI + IaC snippets embodying the reference's decision defaults.
  **Review** walks the §7 checklist (Contract / Security / Reliability /
  Observability / Performance) and emits per-finding output with layer
  tags. **Lookup** answers a narrow question with a citation. If the
  request is ambiguous, the skill asks.
- **Verification-layer tags.** Every §7 checklist item carries a tag —
  `[static]` (source-readable), `[iac]` (Bicep / Terraform review),
  `[contract]` (OpenAPI review), `[runtime]` (Azure Monitor / RUM),
  `[security-tool]` (OWASP ZAP / API Management policies), `[load]` (Azure
  Load Testing / k6). The skill never claims runtime SLIs (p95, cold-start,
  error rate, RU charge) from a static review.
- **Project assimilation — one-way.** Used in an existing project, the
  skill pulls the project *up to* the reference. Added code is always
  reference-compliant; compliant existing infrastructure (shared auth
  module, DI-registered Cosmos client, OpenTelemetry pipeline,
  problem+json middleware) is reused; non-compliant infrastructure
  (account keys, `allowSharedKeyAccess=true`, `HttpClient` per invocation)
  is flagged as legacy debt, never silently extended.
- **Composable per-stack extensions.** `azure-functions-dotnet` (isolated
  worker only — in-process retired 2026-11-10), `azure-cosmosdb` (NoSQL API
  with Provisioned vs Serverless surface), and `azure-blob-storage` (Block
  Blobs with SAS-direct vs API-proxy surface) **load together** when the
  target spans all three layers. Each extension owns a distinct smell-code
  namespace (`afdotnet.*`, `cosmos.*`, `blob.*`) so findings never collide,
  and each contributes stack-specific patterns without overriding the core.
- **Disclosure footer.** Every output ends with a footer listing which
  extensions loaded (subset of `azure-functions-dotnet`, `azure-cosmosdb`,
  `azure-blob-storage`), self-check counts by verification layer,
  project-assimilation summary, the reference path, and an explicit note
  that runtime-verified metrics need Azure Load Testing, Application
  Insights, and Azure Monitor.

## How `architecture-design` works

- **Reference-driven.** Same shape as the sibling design skills — a workflow
  applying an external reference ([souroldgeezer-design/docs/architecture-reference/architecture.md](souroldgeezer-design/docs/architecture-reference/architecture.md)).
  Output cites reference sections (e.g. `§4.2`, `§9.3`) and ArchiMate® 3.2
  chapters / Appendix B entries; findings cite smell codes (`AD-*` for
  artefact, `AD-Q*` for professional OEF/view quality, `AD-DR-*` for drift,
  `AD-L*` for layout); the prose lives in
  the reference, not in the skill.
- **Four modes** (deliberately distinct from the sibling 3-mode shape).
  **Build** produces an OEF XML model at the canonical path from architect
  intent. **Extract** lifts a model from existing code, IaC, and workflows
  — with per-layer asymmetry: Application is lifted from `*.csproj` /
  solution, Technology from Bicep, Implementation & Migration from
  `.github/workflows/`, and the Business layer's Process / Event /
  Interaction from Durable Functions orchestrators and Logic Apps workflow
  definitions (each emitted with a per-element `LIFT-CANDIDATE — architect
  confirms` XML comment carrying `source=` and `confidence=`). The rest of
  the Business layer (Actor / Role / Collaboration / Object / Contract /
  Product / Service / Function), plus Motivation / Strategy / Physical,
  stay forward-only inside `FORWARD-ONLY — architect fills in` comment
  blocks. UI entry points in §9.3 Service Realization views (Process-rooted modality) are hand-authored
  (Blazor idiom in v1). **Review** leads with professional readiness
  (`model-valid`, `diagram-readable`, or `review-ready`) and has two
  sub-behaviours: artefact review (ArchiMate® 3.2 well-formedness +
  `AD-*` / `AD-Q*` / `AD-B-*` smells) and drift
  detection (model vs current repo state, emitting `AD-DR-*` findings
  including process drift `AD-DR-11` / `AD-DR-12`). **Lookup** answers a
  narrow notation question, a domain-discovery question ("what processes
  exist in this feature area"), or a reverse-lookup question ("which
  process does this code symbol or UI component belong to") with a citation
  or a ranked list.
- **Verification-layer tags.** Every §10 checklist item carries a tag —
  `[static]` (readable from the `.oef.xml` source alone) or `[runtime]`
  (requires reading the current code / IaC / workflow state). Drift
  findings are always `[runtime]` against the repository; live-deployment
  drift (IaC vs. what's actually running in Azure) is out of scope and
  requires Azure Resource Graph / Defender for Cloud.
- **Canonical path coupling.** `docs/architecture/<feature>.oef.xml` is
  the single filesystem convention. `responsive-design` and
  `serverless-api-design` Review mode check for a matching model at this
  path and auto-dispatch to `architecture-design` for drift detection when
  one is found. Neither sibling reaches into the architecture-design
  surface beyond this path.
- **Per-input-source lifting procedures** live under
  [souroldgeezer-design/skills/architecture-design/references/procedures/](souroldgeezer-design/skills/architecture-design/references/procedures/) —
  `.NET` for the Application Layer, `Bicep` for the Technology Layer,
  `GitHub Actions` for the Implementation & Migration Layer, `Durable
  Functions + Logic Apps` for the Business Layer's Process / Event /
  Interaction subset (the other Business elements stay forward-only),
  plus professional-readiness and drift-detection procedures. They are consulted (read on demand)
  during Extract and Review; the harness's Skill tool loads `SKILL.md`
  only, so each procedure file is `Read` explicitly when its rules
  apply. The split is by input source (code / IaC / workflow / backend
  workflow), not by target stack choice, so this skill does not use the
  `extensions/` pattern the sibling skills do.
- **Sugiyama-v1 layout engine** (introduced in 0.8.0). A fifth procedure,
  [layout-strategy.md](souroldgeezer-design/skills/architecture-design/references/procedures/layout-strategy.md),
  governs `<view>` placement via a deterministic three-tier pipeline:
  **Tier 0** preserves architect-positioned `<node>` placements verbatim
  on every re-Extract. **Tier 1** (the Sugiyama core engine) runs six
  phases — cycle handling, layer assignment per ArchiMate® layer
  (Strategy → Physical), within-layer ordering with 4-pass barycentric
  crossing-minimisation, coordinate assignment via median heuristic,
  Manhattan A* edge routing with obstacle avoidance, and bounding-box
  normalisation to the canvas origin. **Tier 2** applies a per-viewpoint
  specialisation matching the §9 diagram kind — Capability Map tile
  grid, Application Cooperation hub-and-spoke (when one Component
  dominates by degree), Service Realization vertical-stack with
  Process-rooted modality, Technology Usage hosting tower, Migration
  Plateau timeline, Motivation hierarchical tree, Business Process
  Cooperation three-lane flow. 10-px grid, default element sizes per
  reference §6.4a, Composition / Aggregation / Realization nested over
  explicit edge when both endpoints share a layer-and-aspect cell,
  ≤ 20 elements / ≤ 30 relationships per view. Same inputs produce the
  same `x`, `y`, `w`, `h` on every run — re-extracts don't churn
  coordinates; architect hand-edits survive because only elements
  without a prior position are placed algorithmically. Review restates
  the contract as the `AD-L*` smell codes (eleven in 0.8.0:
  L1 layer-ordering, L2 overlap, L3 label truncation, L4 view budget,
  L5 edge crossings exceed `n/6`, L6 non-orthogonal routing,
  L7 nested-plus-edge, L8 off-grid, L9 hierarchy not respected,
  L10 canvas not normalised, L11 edge-through-node).
- **Process-view emission contract** (introduced in 0.9.0). Build and
  Extract always emit a complete process-view set when Business Processes
  are in scope: one §9.7 Business Process Cooperation view per feature
  (containing every top-level process — root of its Composition tree)
  plus one §9.3 Service Realization drill-down view per orchestrator-level
  Business Process (top-level + Composition-nested sub-orchestrators per
  [process-view-emission.md](souroldgeezer-design/skills/architecture-design/references/procedures/process-view-emission.md)).
  Activity-call steps stay as nodes inside the parent's §9.3 — they are
  not orchestrator-level. Architects can suppress emission per process
  via two orthogonal properties (reference §6.4b):
  `propid-coop-view-exclude` (skip §9.7 inclusion) for deprecated /
  planned / external processes, and `propid-drilldown-exclude` (skip
  §9.3 emission) for thin sub-orchestrator helpers. Under-coverage is
  findable in Review via three new smells: `AD-B-11` (single-process
  cooperation view), `AD-B-12` (sub-process without its own drill-down),
  `AD-B-13` (top-level process missing from §9.7).
- **Professional-readiness gate** (introduced in 0.10.0). Build and
  Extract target at least `diagram-readable`; Review reports whether the
  OEF/model/view set is `model-valid`, `diagram-readable`, or
  `review-ready`. The `AD-Q*` smells cover inventory views, viewpoint
  mismatch, unreviewable density, weak hierarchy, extraction leakage,
  relationship noise, orphaned decision context, thin process views, thin
  service realization, and ambiguous labels. Project packaging stays with
  the consuming project: README rows, render galleries, screenshots, and
  CI publication checks are not architecture-design success criteria.
- **Seven supported diagram kinds** (reference §9): Capability Map,
  Application Cooperation, Service Realization (with optional UI-aware
  Process-rooted modality — drill-down from a Business Process through
  the UI Application Component and Application Interface to the backend
  Application Service / Component and Technology Node), Technology Usage,
  Migration, Motivation, Business Process Cooperation (macro process-flow
  view over the Business layer — steps, events, and their Triggering /
  Flow chain). The English labels are identical to the OEF `viewpoint=`
  enum strings; every supported kind maps 1:1 to a canonical ArchiMate®
  3.2 Viewpoint. Other ArchiMate® diagram kinds are expressible in OEF
  XML (the element and relationship vocabulary is unbounded) but not
  first-class in v1.
- **OEF XML, tool-neutral.** Output is loadable by every major ArchiMate®
  tool. The skill
  does not bundle The Open Group's XSD schemas — emitted files reference
  the canonical schema URL via `xsi:schemaLocation`, and validation is
  delegated to the architect's toolchain (Archi's import, or
  `xmllint --schema`).
- **Disclosure footer.** Every output ends with a footer listing mode,
  reference path, canonical path, diagram kind, layers in scope, self-
  check result, project-assimilation summary (existing model reused /
  identifiers preserved / layers lifted vs stubbed / drift summary),
  forward-only layers stubbed, and the explicit note that live-deployment
  drift
  needs Azure Resource Graph / Defender for Cloud.

## Repository layout

```
AGENTS.md                          # thin Codex-native pointer to CLAUDE.md
.codex/agents/*.toml               # project-scoped Codex custom agents
.claude-plugin/marketplace.json    # shared Claude Code + Codex marketplace manifest
souroldgeezer-audit/               # audit plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  docs/                            # bundled rubrics
    security-reference/            # devsecops.md
    quality-reference/             # unit / integration / e2e-testing.md
  agents/*.md                      # Claude Code subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # workflow
    agents/openai.yaml             # Codex per-skill UI metadata / invocation policy
    extensions/                    # per-stack smell packs
    references/                    # smell catalog + reusable procedures
    config.yaml                    # optional, skill-specific
souroldgeezer-design/              # design plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  docs/
    software-reference/            # bundled reference (software-design.md)
    ui-reference/                  # bundled reference (responsive-design.md)
    api-reference/                 # bundled reference (serverless-api-design.md)
    architecture-reference/        # bundled reference (architecture.md)
  agents/*.md                      # Claude Code subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # workflow
    agents/openai.yaml             # Codex per-skill UI metadata / invocation policy
    extensions/                    # per-stack packs (primitives + patterns + project-assimilation)
    references/                    # smell catalogs + reusable procedures where needed
undecided/                         # skills not yet assigned to a plugin — NOT production-ready;
                                   # do not reference from published skills
```

See [CLAUDE.md](CLAUDE.md) for the full authoring conventions (shared skill
architecture, subagent pairing rules, skill-specific notes) and
[AGENTS.md](AGENTS.md) for the thin Codex-native pointer.

## Attribution

Developed with assistance from [Claude](https://www.anthropic.com/claude)
(Anthropic) via [Claude Code](https://claude.com/claude-code), and
[Codex](https://developers.openai.com/codex). Per-commit co-authorship trailers
are intentionally omitted — this repo-wide acknowledgement covers the
contribution.

## License

MIT. See plugin manifests for per-plugin metadata.
