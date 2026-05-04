# souroldgeezer

Claude Code and Codex plugin marketplace by Sour Old Geezer. Currently ships three plugins:

- **souroldgeezer-audit** — rubric-driven audits for DevSecOps posture and
  test quality, with per-stack extensions and matching Claude Code subagents.
- **souroldgeezer-design** — reference-driven design for sustainable software,
  modern web UIs, HTTP APIs, and ArchiMate® architecture models. For
  software design (build, extract, review, lookup): shapes code/module/script
  boundaries, dependency direction, responsibility placement, semantic
  coherence, coupling control, and evolutionary design, with .NET™ and
  shell-script extensions.
  For UIs (build, review, lookup): enforces W3C® WCAG™ 2.2 AA,
  internationalization (LTR + RTL + text expansion), and Core Web Vitals, with
  a Blazor™ WebAssembly extension. For HTTP APIs (build, extract, review,
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
  Strategy as forward-only with seed views; shows Managed Identity / RBAC,
  deployment topology, and external trust-boundary concerns when extractable;
  supports macro Business Process Cooperation and UI-aware Service Realization
  diagram kind (§9.3 Process-rooted modality); dispatches from the sibling
  skills' Review mode to flag drift between code and the architect's
  model. Each skill has a matching Claude Code subagent; Codex consumes the
  bundled `skills/**/SKILL.md` workflows directly from the plugin.
- **souroldgeezer-ops** — operations workflows for issue, work-item, and
  pull-request lifecycle handling, with provider-agnostic `issue-ops` and
  `pr-ops` cores plus GitHub™ provider extensions for issue state, PR state,
  lifecycle comments, issue-to-PR handoff, PR creation/reuse from prepared
  branches, reviews, pending-check monitoring, branch updates, merge, and
  closure mechanics.

## Install

### Claude Code

Add this marketplace and enable the plugins you want:

```
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
/plugin install souroldgeezer-ops@souroldgeezer
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
    "souroldgeezer-design@souroldgeezer": true,
    "souroldgeezer-ops@souroldgeezer": true
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

After changing a local marketplace plugin, start a fresh Codex session and
reinstall the changed plugin from `/plugins` if the session still loads an old
materialized copy. `codex plugin marketplace upgrade <name>` currently refreshes
Git-backed marketplaces, but reports that a local marketplace is not Git-backed;
do not treat it as the local-cache refresh path. Verify the installed copy under
`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` and confirm the
expected `skills/` directories are present.

Keep `.codex-plugin/plugin.json#interface.defaultPrompt` to three or fewer
entries. Codex warns and ignores extra starter prompts.

The repo intentionally does not duplicate the catalog under
`.agents/plugins/marketplace.json`; the existing `.claude-plugin/marketplace.json`
is the shared marketplace for both Claude Code and Codex.

Skill authoring and review guidance lives in
[docs/skill-architecture.md](docs/skill-architecture.md). Use it as the
canonical craft standard for trigger metadata, `SKILL.md` workflow shape,
on-demand references, deterministic machinery, runtime parity, report contracts,
and iterative improvement checks.

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
| [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | Unit, integration, and E2E test quality (dispatches on detected test type) | [dotnet-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [dotnet-core](souroldgeezer-audit/skills/test-quality-audit/extensions/dotnet-core.md); [nodejs-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [nodejs-core](souroldgeezer-audit/skills/test-quality-audit/extensions/nodejs-core.md); [nextjs-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [nextjs-core](souroldgeezer-audit/skills/test-quality-audit/extensions/nextjs-core.md) (strict superset of nodejs); [python-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [python-core](souroldgeezer-audit/skills/test-quality-audit/extensions/python-core.md) for Python® pytest / unittest suites; [robotframework-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [robotframework-core](souroldgeezer-audit/skills/test-quality-audit/extensions/robotframework-core.md) for Robot Framework® suites |

Claude Code subagents live alongside in [souroldgeezer-audit/agents/](souroldgeezer-audit/agents/)
and invoke the same skills, making them usable as delegated one-shots. Codex
installs the bundled skills through the plugin manifest, reads per-skill
metadata from each `skills/<name>/agents/openai.yaml`, and has matching
project-scoped custom-agent wrappers in [.codex/agents/](.codex/agents/).

## What's in `souroldgeezer-design`

Four design skills, each with a matching one-shot Claude Code subagent:

| Skill | Covers | Stack extensions |
|---|---|---|
| [software-design](souroldgeezer-design/skills/software-design/SKILL.md) | Sustainable software design for code/module/script changes - Build, Extract, Review, and Lookup across boundary placement, dependency direction, responsibility assignment, semantic coherence, coupling control, evolutionary design, lightweight tradeoffs, and socio-technical fit | [.NET™](souroldgeezer-design/skills/software-design/extensions/dotnet.md) (solution/project references, namespaces, assembly visibility, dependency injection, persistence model leakage, hosted services, and common .NET™ design ceremony); [shell-script](souroldgeezer-design/skills/software-design/extensions/shell-script.md) (Bash/zsh interpreter boundaries, sourced modules, shell option/trap state, Linux® / macOS™ / Windows Subsystem for Linux™ compatibility, and `devsecops-audit` Quick validation when available); [Python®](souroldgeezer-design/skills/software-design/extensions/python.md) (repo-internal tooling — entry-point boundaries, import-time workflow, `sys.path` stitching, module-state coupling, environment backchannels, `subprocess` command-construction, stream / exit-code contracts, type-hint boundaries, reproducibility contract across Python® version + lockfile / PEP 723 inline pins, async-misuse, shell-style Python® smell, and `devsecops-audit` Quick validation when available; skips web/ASGI applications) |
| [responsive-design](souroldgeezer-design/skills/responsive-design/SKILL.md) | Modern responsive web UI in HTML / CSS / JS — enforces WCAG 2.2 AA, internationalization (LTR + RTL + text expansion), and Core Web Vitals (LCP / CLS / INP) as hard baselines | [blazor-wasm](souroldgeezer-design/skills/responsive-design/extensions/blazor-wasm.md) (covers both standalone Blazor WebAssembly and Blazor Web App `.Client` hosting) |
| [api-design](souroldgeezer-design/skills/api-design/SKILL.md) | Modern HTTP APIs — Build, Extract, Review, and Lookup across contract discipline (OpenAPI™ 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 ETag), security, reliability (idempotency on mutations, safe retries, 429 + Retry-After, poison / dead-letter), observability (structured logs, W3C® traceparent, correlation ID, request-charge visibility), and honest verification-layer disclosure | [azure-functions-dotnet](souroldgeezer-design/skills/api-design/extensions/azure-functions-dotnet.md), [azure-cosmosdb](souroldgeezer-design/skills/api-design/extensions/azure-cosmosdb.md), [azure-blob-storage](souroldgeezer-design/skills/api-design/extensions/azure-blob-storage.md) — **compose** on the same target |
| [architecture-design](souroldgeezer-design/skills/architecture-design/SKILL.md) | ArchiMate® 3.2 enterprise / solution architecture models — enforces ArchiMate® 3.2 layer discipline, relationship well-formedness, Core-vs-extension defaults, materialized OEF view geometry, change classification (semantic model / view geometry / documentation-render inventory), and professional OEF/view readiness (`model-valid`, `diagram-readable`, `review-ready`); serialised as **OEF XML** (ArchiMate® Model Exchange File Format), loadable in ArchiMate®-conformant tools. 4-mode shape: Build (intent → model), Extract (code + IaC + workflows → model with per-layer lifting; Business Process / Event / Interaction lift from Durable Functions + Logic Apps as `LIFT-CANDIDATE`s, rest of Business / Motivation / Strategy are forward-only with seed views), Review (per-view readiness matrix with Readiness + Authority axes, executable source-geometry `AD-L*` gate, packaged layout request/result/policy/provenance checks, route repair, global polish, Java™ ImageIO-based PNG validation, optional render artefacts with render gate when visual quality is requested, artefact findings, duplicate realization view detection, and drift detection including process drift, RBAC, deployment-topology, and trust-boundary checks against current repo state), Lookup (notation Q&A, domain discovery, reverse lookup from code or UI symbol → owning process), plus an explicit Review → Extract → Build → Lookup → render/compare iteration loop for user-requested render polishing | Per-input-source lifting procedures (not extensions): [.NET](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-dotnet.md), [Bicep](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-bicep.md), [GitHub Actions](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-gha.md), [Durable Functions + Logic Apps](souroldgeezer-design/skills/architecture-design/references/procedures/lifting-rules-process.md), [seed views](souroldgeezer-design/skills/architecture-design/references/procedures/seed-views.md), plus [professional-readiness](souroldgeezer-design/skills/architecture-design/references/procedures/professional-readiness.md), the executable [source-geometry gate](souroldgeezer-design/skills/architecture-design/references/scripts/validate-oef-layout.sh), optional [render script](souroldgeezer-design/skills/architecture-design/references/scripts/archi-render.sh), packaged [layout runtime](souroldgeezer-design/skills/architecture-design/references/scripts/arch-layout.sh), [layout schemas](souroldgeezer-design/skills/architecture-design/references/schemas/), [rendered PNG validation](souroldgeezer-design/skills/architecture-design/references/procedures/rendered-png-validation.md), [layout strategy](souroldgeezer-design/skills/architecture-design/references/procedures/layout-strategy.md), [backend contract](souroldgeezer-design/skills/architecture-design/references/procedures/layout-backend-contract.md), [viewpoint policies](souroldgeezer-design/skills/architecture-design/references/procedures/layout-policies-by-viewpoint.md), [routing/glossing](souroldgeezer-design/skills/architecture-design/references/procedures/routing-and-glossing.md), and [deterministic fallback](souroldgeezer-design/skills/architecture-design/references/procedures/layout-fallback.md), invoked by Build / Extract and restated as `AD-Q*` / `AD-L*` / `LAYOUT_*` / `AD-B-*` checks in Review |

References live at [souroldgeezer-design/docs/software-reference/software-design.md](souroldgeezer-design/docs/software-reference/software-design.md), [souroldgeezer-design/docs/ui-reference/responsive-design.md](souroldgeezer-design/docs/ui-reference/responsive-design.md), [souroldgeezer-design/docs/api-reference/api-design.md](souroldgeezer-design/docs/api-reference/api-design.md), and [souroldgeezer-design/docs/architecture-reference/architecture.md](souroldgeezer-design/docs/architecture-reference/architecture.md).
Matching Claude Code subagents are at [souroldgeezer-design/agents/software-design.md](souroldgeezer-design/agents/software-design.md), [souroldgeezer-design/agents/responsive-design.md](souroldgeezer-design/agents/responsive-design.md), [souroldgeezer-design/agents/api-design.md](souroldgeezer-design/agents/api-design.md), and [souroldgeezer-design/agents/architecture-design.md](souroldgeezer-design/agents/architecture-design.md). Codex installs the bundled skills through the plugin manifest, reads per-skill metadata from each `skills/<name>/agents/openai.yaml`, and has matching project-scoped custom-agent wrappers in [.codex/agents/](.codex/agents/).

The canonical path `docs/architecture/<feature>.oef.xml` remains the coupling mechanism for UI/API code-to-architecture drift: `responsive-design` and `api-design` auto-dispatch to `architecture-design` Review when a paired model is present.

## What's in `souroldgeezer-ops`

Two operations skills, each with a matching one-shot Claude Code subagent:

| Skill | Operates | Provider extensions |
|---|---|---|
| [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md) | Explicit issue and work-item lifecycle requests: triage, plan, implement, resume, close, queue processing, lifecycle state, escalation, local verification, integration handoff, and completion reporting | [github](souroldgeezer-ops/skills/issue-ops/extensions/github.md) for GitHub™ issue state, lifecycle comments, labels/projects/milestones context, GitHub™ MCP / `gh` / REST routing, `pr-ops` handoff, direct-main mode, linked pull requests, and issue closure |
| [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | Explicit pull-request lifecycle requests: create or reuse PRs from prepared branches, review, check inspection and full-cycle monitoring, feedback fixes, branch update, review request, merge, close, cleanup, escalation, verification, and completion reporting | [github](souroldgeezer-ops/skills/pr-ops/extensions/github.md) for GitHub™ PR state, prepared branches, PR creation/reuse, reviews, review threads, comments, checks, pending-check monitoring, branch protection, GitHub™ MCP / `gh` / REST routing, branch update, merge, close, and branch cleanup |

The core skills are provider-agnostic. Provider mechanics live in extensions and
load only after the tracker or PR provider is identified.

Matching Claude Code subagents: [issue-ops](souroldgeezer-ops/agents/issue-ops.md)
and [pr-ops](souroldgeezer-ops/agents/pr-ops.md). Codex installs the bundled
skills through the plugin manifest, reads per-skill metadata from each
`skills/<name>/agents/openai.yaml`, and has matching project-scoped wrappers in
[.codex/agents/issue-ops.toml](.codex/agents/issue-ops.toml) and
[.codex/agents/pr-ops.toml](.codex/agents/pr-ops.toml).

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

## How `api-design` works

- **Reference-driven.** Same shape as `responsive-design` — a workflow
  applying an external reference. Output cites reference sections (e.g.
  `§3.6`, `§5.6`), RFCs (`RFC 9457`, `RFC 9110`), and MSFT Learn slugs;
  extension-specific findings cite extension codes (`afdotnet.HC-11`,
  `cosmos.HC-4`, `blob.HC-2`). The prose lives in the reference
  ([souroldgeezer-design/docs/api-reference/api-design.md](souroldgeezer-design/docs/api-reference/api-design.md)),
  not in the skill.
- **Four modes.** **Build** produces OpenAPI™ fragments + handler code +
  runtime/data wiring + deployment snippets embodying the reference's decision
  defaults. **Extract** maps the current API baseline (contract shape, route
  surface, auth, errors, versioning, runtime stack, loaded data/storage
  extensions, legacy debt, and next smallest move). **Review** walks the §7
  checklist (Contract / Security / Reliability / Observability / Performance)
  and emits per-finding output with layer tags. **Lookup** answers a narrow
  question with a citation. If the request is ambiguous, the skill asks.
- **Verification-layer tags.** Every §7 checklist item carries a tag —
  `[static]` (source-readable), `[iac]` (Bicep™ / Terraform review),
  `[contract]` (OpenAPI™ review), `[runtime]` (Azure® Monitor / RUM),
  `[security-tool]` (OWASP ZAP / API Management policies), `[load]` (Azure
  Load Testing / k6). The skill never claims runtime SLIs (p95, cold-start,
  error rate, RU charge) from a static review.
- **Project assimilation — one-way.** Used in an existing project, the
  skill pulls the project *up to* the reference. Added code is always
  reference-compliant; compliant existing infrastructure (shared auth
  module, DI-registered Azure® Cosmos DB™ client, OpenTelemetry pipeline,
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
  that runtime-verified metrics need Azure® Load Testing, Azure® Monitor
  Application Insights, and Azure® Monitor.

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
- **Per-view readiness matrix** (introduced in 0.18.0). Quality is classified
  per `<view>` first; the artifact rollup is the worst-view minimum (capped at
  `model-valid` by any unresolved model-level blocker). Build, Extract, and
  Review emit a per-view matrix carrying Readiness (`model-valid` /
  `diagram-readable` / `review-ready`) and Authority (`lifted-from-source` /
  `forward-only-or-inferred` / `architect-approved` / `stakeholder-validated`).
  The matrix surfaces the per-view bottleneck so iterations can target the
  view that's holding the rollup back.
- **Authority dimension** (introduced in 0.18.0). Visual readiness measures
  whether the view is a polished diagram; **authority** measures who or what
  backs the architecture content shown. Defaults derived from view content
  (`lifted-from-source` when every element resolves to a current source;
  `forward-only-or-inferred` when any element is a `FORWARD-ONLY` stub or an
  unconfirmed `LIFT-CANDIDATE`); architect overrides via the view-level
  `propid-authority` property (reference §6.4b) for `architect-approved` or
  `stakeholder-validated`. A polished forward-only view is honestly
  `review-ready` for visual quality and `forward-only-or-inferred` for
  authority — both are reported. `AD-Q11` catches override-vs-content
  contradictions (claimed `architect-approved` while the view still contains
  unresolved `FORWARD-ONLY` or `LIFT-CANDIDATE` content).
- **Verification-layer tags.** Every §10 checklist item carries a tag —
  `[static]` (readable from the `.oef.xml` source alone), `[visual]`
  (requires the optional bundled render script when requested), or
  `[runtime]` (requires reading the current code / IaC / workflow state). Drift
  findings are always `[runtime]` against the repository; live-deployment
  drift (IaC vs. what's actually running in Azure) is out of scope and
  requires Azure Resource Graph / Defender for Cloud.
- **Packaged layout runtime** (introduced in 0.21.0). The skill ships
  [arch-layout.sh](souroldgeezer-design/skills/architecture-design/references/scripts/arch-layout.sh)
  as a thin launcher for a self-contained Java™ 21 runtime at
  `references/bin/arch-layout.jar`. The runtime validates the layout
  [request/result schemas](souroldgeezer-design/skills/architecture-design/references/schemas/),
  exposes runtime-honored versus advisory request fields, rejects contradictory
  hierarchy / locked-geometry / locked-route requests, produces
  generated-layout results for supported directed viewpoints,
  repairs stale or invalid routes while preserving locked node geometry,
  applies bounded global polish when route-only repair is insufficient,
  emits machine-readable warning evidence for route intersections, overlap
  defects, parent/child containment boundaries, and locked-node movement,
  materializes layout results back into OEF view geometry, emits per-view
  provenance reports for backend/fallback, materialization, source-gate,
  render-gate, post-processing, and generated response / README /
  OEF-documentation text, and validates rendered PNG invariants. Source lives
  outside the shipped skill
  runtime under `tools/architecture-layout-java/`; release packaging uses
  [package-arch-layout.sh](souroldgeezer-design/skills/architecture-design/references/scripts/package-arch-layout.sh)
  so only the JAR, shell launchers, schemas, procedures, and fixtures are
  distributed with the plugin skill.
- **Render artefacts.** OEF XML remains the architecture source of truth.
  Rendered PNGs are deployment / publication artefacts derived from the OEF.
  Users can request renders through `architecture-design`; the skill runs
  `references/scripts/archi-render.sh` after source-geometry checks, records
  the output paths, and validates every PNG with `arch-layout.sh validate-png`
  before visual inspection. ImageMagick is optional diagnostics only; the
  shipped runtime uses Java™ ImageIO for acceptance checks. The renderer
  executable is a weak dependency with no fallback renderer — missing renderer,
  `DISPLAY`, or script prerequisites are reported as
  `visual render inspection: not run`.
- **Render gate** (introduced in 0.18.0). When the user has explicitly
  requested visual quality (render request, render-polish loop, or `[visual]`
  self-check requested in pre-flight) and render did not run, the changed
  views in this run cap at `model-valid` until render runs. Unchanged views
  inherit their prior classification. When the user has not requested visual
  quality, the gate does not engage — the source-geometry gate plus
  `[static]` `AD-L*` checks remain the visual proxy. This preserves CI
  portability for installations without Archi while making "no render, no
  done" enforceable when visual quality is the architect's stated goal.
- **Render-contract discovery** (introduced in 0.18.0; disclosure-only). The
  project assimilation discovery pass detects committed render artifacts
  under `docs/architecture/**/*.png`, gallery sections in
  `README.md` / `docs/architecture/README.md`, and repo render commands in
  `Makefile` / `package.json` / workflows. The footer's `Project assimilation:`
  block lists what was found, and when the OEF changed, notes that those
  project artefacts may need refresh — the architect decides whether to
  update them in this run. The skill does not auto-update committed renders
  or gallery prose unless the user explicitly asks or the explicit
  render-polish loop is in scope.
- **Skill self-check** (introduced in 0.18.0). Build / Extract / Review step 0
  invokes
  [self-check.md](souroldgeezer-design/skills/architecture-design/references/procedures/self-check.md)
  to verify required reference files, procedures, and scripts are present and
  runnable. Missing tooling produces a degraded-mode footer entry naming the
  blocker; affected verifications are reported as "not run" rather than
  silently skipped, so a missing procedure doesn't masquerade as a clean check.
- **Change classification.** OEF work reports whether it changed architecture
  semantics, view geometry, or documentation/render inventory. View-specific
  relationship hiding is allowed when the model relationship remains intact,
  the visible connection would duplicate the story, and the view or summary
  names the relationship id and reason.
- **Canonical path coupling.** `docs/architecture/<feature>.oef.xml` is
  the single filesystem convention. `responsive-design` and
  `api-design` Review mode check for a matching model at this
  path and auto-dispatch to `architecture-design` for drift detection when
  one is found. Neither sibling reaches into the architecture-design
  surface beyond this path.
- **Per-input-source lifting procedures** live under
  [souroldgeezer-design/skills/architecture-design/references/procedures/](souroldgeezer-design/skills/architecture-design/references/procedures/) —
  `.NET` for the Application Layer, `Bicep` for the Technology Layer,
  `GitHub Actions` for the Implementation & Migration Layer, `Durable
  Functions + Logic Apps` for the Business Layer's Process / Event /
  Interaction subset (the other Business elements stay forward-only),
  seed views for forward-only Strategy / Motivation stubs,
  plus professional-readiness and drift-detection procedures. They are consulted (read on demand)
  during Extract and Review; the harness's Skill tool loads `SKILL.md`
  only, so each procedure file is `Read` explicitly when its rules
  apply. The split is by input source (code / IaC / workflow / backend
  workflow), not by target stack choice, so this skill does not use the
  `extensions/` pattern the sibling skills do.
- **Backend-neutral layout policy** (refactored in 0.20.0). The
  [layout-strategy.md](souroldgeezer-design/skills/architecture-design/references/procedures/layout-strategy.md)
  procedure
  governs materialized `<view>` placement via a viewpoint-constrained pipeline:
  Build and Extract must emit Element nodes with `elementRef`, `x`, `y`, `w`,
  and `h`, plus Relationship connections whose endpoints reference view-node
  identifiers; empty generated views are model inventory, not
  `diagram-readable` output.
  The pipeline preserves architect-authored geometry, builds a normalized
  backend contract, selects the viewpoint policy, chooses an available backend
  or the deterministic fallback, assigns ports, routes high-priority edges
  first, glosses routes, and validates final OEF geometry. Capability Map,
  Migration, Technology Usage, Motivation, Service Realization, Application
  Cooperation, and Business Process Cooperation each have first-class layout
  policies; the deterministic layered fallback is reserved for small generated
  directed views. Main Service Realization spines remain visible by default.
  Same inputs produce the same generated geometry on every fallback run, and
  architect hand-edits survive because locked placements are preserved unless
  explicitly reflowed or invalid. Review restates
  the contract as the `AD-L*` smell codes:
  L1 layer-ordering, L2 overlap, L3 label truncation, L4 view budget,
  L5 edge crossings exceed `n/6`, L6 non-orthogonal routing,
  L7 nested-plus-edge, L8 off-grid, L9 hierarchy not respected,
  L10 canvas not normalised, L11 connector-through-node (blocking),
  L12 view-orphan, L13 stacked connector lane, L14 wide empty layer gap,
  L15 local fan-out crisscross, L16 long peripheral bus route, L17 duplicate
  visible story path, L18 misleading boundary crossing, L19 ambiguous
  nested ownership, and L20 hidden realization spine).
  The packaged Java™ runtime adds concrete `validate-request`,
  `validate-result` schema checks, `validate-result --strict` result-quality
  gates, geometry-rich `LAYOUT_*` warning evidence, `layout-elk`,
  `route-repair`, `global-polish`, `materialize-oef`, and `validate-png`
  commands over that backend-neutral contract, but it does not ship the
  deferred interactive debugger, relationship-matrix provenance proof,
  mainstream-tool compatibility proof, or multi-evidence recovery loop.
  Recreate, regenerate, and global reflow requests now report layout intent
  plus a per-view backend/fallback row, so users can distinguish OEF geometry
  generation or repair (`layout-elk`, `route-repair`, `global-polish`, or
  viewpoint fallback), result-to-OEF materialization (`materialize-oef`), and
  rendered PNG validation (`validate-png`).
- **Process-view emission contract** (introduced in 0.9.0). Build and
  Extract always emit a complete process-view set when Business Processes
  are in scope: one §9.7 Business Process Cooperation view per feature
  (containing every top-level process — root of its Composition tree)
  plus §9.3 Service Realization coverage per distinct realization story
  (top-level + Composition-nested sub-orchestrators per
  [process-view-emission.md](souroldgeezer-design/skills/architecture-design/references/procedures/process-view-emission.md)).
  Multiple processes that share the same Application / Technology / data /
  security / deployment / UI-entry story are consolidated into one process-rooted
  §9.3 view; materially different process stories keep separate views.
  Activity-call steps stay as nodes inside the parent's §9.3 — they are
  not orchestrator-level. Architects can suppress emission per process
  via two orthogonal properties (reference §6.4b):
  `propid-coop-view-exclude` (skip §9.7 inclusion) for deprecated /
  planned / external processes, and `propid-drilldown-exclude` (skip
  §9.3 emission) for thin sub-orchestrator helpers. Under-coverage and
  duplicate same-story drill-downs are findable in Review via four smells:
  `AD-B-11` (single-process
  cooperation view), `AD-B-12` (sub-process without its own drill-down),
  `AD-B-13` (top-level process missing from §9.7), and `AD-B-14`
  (duplicate realization drill-down).
- **Professional-readiness gate** (introduced in 0.10.0; per-view in 0.18.0).
  Build and Extract target at least `diagram-readable`; Review reports
  whether each `<view>` is `model-valid`, `diagram-readable`, or
  `review-ready`, then derives the artifact rollup as the worst-view minimum.
  The `AD-Q*` smells cover inventory views, viewpoint mismatch, unreviewable
  density, weak hierarchy, extraction leakage, relationship noise, orphaned
  decision context, thin process views, thin service realization, ambiguous
  labels, and authority override contradictions (`AD-Q11`, 0.18.0). A
  generated view without materialized node/connection geometry is capped at
  `model-valid`; when a renderer is available, every view must be rendered
  and inspected before the skill claims `diagram-readable` or `review-ready`.
  Project packaging stays with the consuming project: README rows, render
  galleries, screenshots, and CI publication checks are not architecture-design
  success criteria — they are surfaced via the disclosure-only render-contract
  discovery (0.18.0) for the architect to act on.
- **Extracted security and boundary semantics.** Bicep lifting surfaces
  Managed Identity / RBAC Access paths, diagnostic Flow edges, Key Vault
  references, RBAC-only resource flags, and private endpoint Paths. .NET
  lifting groups internal and external Application Components into
  trust-boundary Groupings. GitHub Actions lifting distinguishes true
  migration from parallel deployment topology.
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
docs/skill-architecture.md         # canonical skill architecture craft standard
scripts/skill-architecture-report.sh  # craft-standard validation wrapper for agent iteration
scripts/skill_architecture_report.py  # Python® validation engine and JSON/Markdown reporter
tests/skill_architecture_report_test.py  # unittest fixtures and wrapper smoke coverage
tests/skill_architecture_report_ledger.jsonl  # one-case-per-line report-engine ledger
tests/generate_skill_architecture_report_ledger.py  # deterministic 500+ case ledger generator
pyproject.toml / uv.lock           # uv-managed repo-local tooling project
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
    api-reference/                 # bundled reference (api-design.md)
    architecture-reference/        # bundled reference (architecture.md)
  agents/*.md                      # Claude Code subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # workflow
    agents/openai.yaml             # Codex per-skill UI metadata / invocation policy
    extensions/                    # per-stack packs (primitives + patterns + project-assimilation)
    references/                    # smell catalogs + reusable procedures where needed
souroldgeezer-ops/                 # operations plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/*.md                      # Claude Code subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # provider-agnostic workflow
    agents/openai.yaml             # Codex per-skill UI metadata / invocation policy
    extensions/                    # provider-specific mechanics
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
