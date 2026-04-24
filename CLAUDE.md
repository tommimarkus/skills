# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Code plugin marketplace**, not an application. The root `.claude-plugin/marketplace.json` registers one or more plugin subdirectories. There is nothing to build, lint, or test — content is Markdown + YAML. Validation is structural (correct filenames, frontmatter, schema) and semantic (does the skill's described workflow still match its SKILL.md).

## Keeping CLAUDE.md and README.md current (MUST)

**Both CLAUDE.md and README.md MUST be kept up to date as the repo evolves.** They have different audiences and different triggers, but both are load-bearing — stale guidance in either causes downstream bugs. Treat drift in either as a blocking bug and fix it in the same commit as the change that introduced the drift.

**CLAUDE.md audience:** Claude Code when authoring or editing skills in this repo. It is the first file Claude reads — stale guidance here causes stale reasoning everywhere else. Update CLAUDE.md whenever any of the following change:

- A plugin is added, removed, or renamed (update "Directory layout" and any plugin-level references).
- A skill is added, removed, renamed, or moved between plugins (or between a plugin and `undecided/`) (update "Skill-specific notes").
- A skill's mode set, output contract, or bundled-reference path changes (update "Skill architecture" and "Skill-specific notes").
- A new convention or pattern emerges across skills — new reference category (e.g. `docs/ui-reference/`), new extension layout, new supporting-file kind, new required SKILL.md section (update "Directory layout" and "Skill architecture").
- Any statement in this file becomes factually wrong about the current repo state.

**README.md audience:** humans browsing the marketplace (GitHub readers, potential installers). It is the first file humans read. Update README.md whenever any of the following change:

- A plugin is added, removed, or renamed (update the intro paragraph, add/remove the corresponding "What's in `<plugin>`" section, update the repository-layout example).
- A skill is added or removed within a plugin (update the corresponding plugin's "What's in" table and its "How `<skill>` works" section).
- Install commands or marketplace slugs change (update "Install").
- Repository layout changes in a way a new reader would benefit from seeing (update "Repository layout").
- The audience-facing behaviour of a skill changes — new mode, new output format, new reference path (update the skill's "How it works" section).

Before finishing any task that changes repo structure or a skill's contract, re-read **both files** and diff them mentally against the change. If any section is now wrong or incomplete, amend it in the same commit.

## Repo-internal skills

The repo ships a small set of **internal** skills under `.claude/skills/` — scoped to this repository, auto-discovered by Claude Code when working here, and deliberately *not* bundled with the distributed `souroldgeezer-*` plugins. Internal skills encode how *we* author this repo; they are not capabilities shipped to downstream users.

Current internal skills:

- **`ip-hygiene`** at [.claude/skills/ip-hygiene/SKILL.md](.claude/skills/ip-hygiene/SKILL.md) — copyright, trademark, and licence check for any skill-related edit. Fast five-question triage, then copyright / trademark / licence check if triggered, with a codified remediation order and authoritative-sources appendix. Invoke on any create / modify / rename / move / delete touching `souroldgeezer-*/skills/**`, `souroldgeezer-*/agents/**`, `souroldgeezer-*/docs/*-reference/**`, `.claude/skills/**`, the plugin / marketplace manifests, or the `CLAUDE.md` / `README.md` sections that describe those artefacts. Prevents verbatim reproduction of copyrighted spec prose / code / figures / samples, enforces ® on first public-visible mention, blocks bundling of third-party copyrighted assets unless the upstream licence permits redistribution, and preserves the repo's nominative-fair-use convention.

Add to this section when new internal skills are introduced. Internal skills must not appear in `.claude-plugin/marketplace.json` or any plugin's `plugin.json`.

## Directory layout

```
.claude-plugin/marketplace.json        ← marketplace manifest (lists plugins, owner, etc.)
<plugin-name>/
  .claude-plugin/plugin.json           ← plugin manifest
  docs/<kind>-reference/*.md           ← bundled reference prose (rubric, playbook, or similar)
  agents/<skill-name>.md               ← one subagent per skill, same name
  skills/<skill-name>/SKILL.md         ← skill workflow
                     /extensions/      ← per-stack packs (see below)
                     /references/      ← smell catalog + reusable procedures (audit skills)
                     /config.yaml      ← optional, skill-specific (not a Claude Code standard)
undecided/                             ← skills not yet assigned to a plugin (NOT in marketplace.json, NOT production-ready; do not reference from other skills)
  agents/<name>.md                     ← matching subagents sit here too
  <skill-name>/                        ← same shape as a plugin's skill dir
```

Current `<kind>-reference/` directories in use:
- `souroldgeezer-audit/docs/security-reference/devsecops.md` — DevSecOps rubric
- `souroldgeezer-audit/docs/quality-reference/{unit,integration,e2e}-testing.md` — test-quality rubrics
- `souroldgeezer-design/docs/ui-reference/responsive-design.md` — responsive-design playbook
- `souroldgeezer-design/docs/api-reference/serverless-api-design.md` — serverless-api-design playbook
- `souroldgeezer-design/docs/architecture-reference/architecture.md` — architecture-design playbook (ArchiMate® 3.2)

When moving a skill out of `undecided/` into a plugin (or vice versa), **also move its matching subagent file** in `agents/<name>.md`. Skill and subagent are paired by identical name.

## Plugin registration

Adding a new plugin:
1. Create `<plugin-name>/.claude-plugin/plugin.json` (required: `name`, `version`, `description`; use `author: {name, email}` and `license: MIT` defaults from memory).
2. Add it to `marketplace.json` under `plugins[]` with `name`, `source: ./<plugin-name>`, `version`, `description`.
3. Plugin description in `plugin.json` and in `marketplace.json#plugins[]` should stay in sync.

## Skill architecture (shared pattern across skills)

Skills in this repo follow a recurring shape. Understand it before editing any SKILL.md:

- **Reference vs workflow separation.** SKILL.md is a *workflow* for applying a bundled reference; the reference prose lives in a separate file under `<plugin>/docs/<kind>-reference/*.md` (rubric for audits, playbook for design; see "Directory layout" for the current list). Relative paths like `../../docs/ui-reference/responsive-design.md` resolve to these from a skill dir. SKILL.md must **cite** reference sections and codes — never duplicate reference prose.
- **Mode dispatch.** Every skill defines its own modes; each SKILL.md lists them. Audit skills (`devsecops-audit`, `test-quality-audit`) use **Quick** (single file / PR diff, per-finding output only) vs **Deep** (whole-repo, full sectioned rollup, may use MCP probes). Design skills use **Build** / **Review** / **Lookup** (`responsive-design`, `serverless-api-design`) or **Build** / **Extract** / **Review** / **Lookup** (`architecture-design` — the 4-mode shape is deliberate because Extract (code → diagram) is a first-class, load-bearing operation for the bridge purpose). If the user request is ambiguous, the skill asks.
- **Output cites codes / sections, not prose.** Audit reports cite smell codes like `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`. Design output cites reference sections (`§3.11`, `§5.8`) plus WCAG SC numbers (`SC 1.4.10`, `SC 2.5.8`). Either way, SKILL.md and its output never duplicate reference prose.
- **Extensions are per-stack packs** in `skills/<skill>/extensions/*.md`. They are loaded on demand based on detected target type. For audits they **ADD** namespaced smells (`<ext>.HC-N`, `<ext>.LC-N`, `<ext>.POS-N`) or **CARVE OUT** core smells for idiomatic framework patterns; for design they also add stack-specific primitives, patterns, and project-assimilation rules (how to read the stack's token config and component library). Extensions **never override** core rules. Each skill's `extensions/README.md` is the authoritative convention for that skill; follow its required-sections list exactly when adding a new extension. `serverless-api-design` is the first skill in the repo where **multiple extensions compose on the same target** (compute + data + object storage): an API on Azure Functions .NET using Cosmos DB and Blob Storage loads all three extensions at once. Smell-code namespaces are orthogonal by construction (`afdotnet.*`, `cosmos.*`, `blob.*`, core `SAD-G-*`), so findings from different extensions never collide.
- **Supporting files live under `references/`** (audit skills, and design skills when needed). `references/smell-catalog.md` is the compact code index; `references/procedures/*.md` are reusable sub-procedures the workflow steps into. `responsive-design` and `serverless-api-design` omit `references/` because their bundled reference prose covers the need; `architecture-design` uses `references/` because (a) its code-to-diagram lifting rules are per-input-source reusable procedures, not per-stack extensions, and (b) its Review mode's drift sub-behaviour is itself a reusable procedure.
- **Cross-skill coupling is via filesystem convention** (design skills). `architecture-design` introduces the first cross-skill canonical-path convention in the repo: `docs/architecture/<feature>.oef.xml` is written by `architecture-design` and read by `responsive-design` / `serverless-api-design` in their Review mode for drift detection. Sibling skills do not reach into the `architecture-design` surface beyond this path. The convention is documented identically in the canonical path section of each SKILL.md.
- **Project assimilation is one-way** (design skills). Output assimilates the *project* to the *reference*, not the other way around. New code is always reference-compliant; non-compliant existing infrastructure is reused only when substantively compliant, otherwise flagged as legacy debt. See `souroldgeezer-design/skills/responsive-design/SKILL.md` § "Project assimilation" for the canonical form.
- **Output footers disclose state.** Every report / build output ends with a footer listing which extensions loaded, MCP availability, cost stance (if applicable), reference path, and (design skills) project-assimilation summary. Don't remove these — they're how users audit the auditor / verify the builder.

## Subagents

Every skill has a matching subagent at `<plugin>/agents/<skill-name>.md`. The subagent is a thin one-shot wrapper: it invokes the skill via the `Skill` tool, follows the skill's instructions, and presents results in the skill's required shape. Subagent frontmatter: `name`, `description` (mirror the skill's description for discoverability), `tools`, `model`. When editing a skill's invocation contract (output format, required footer fields), update the matching subagent.

## Skill-specific notes

- **`devsecops-audit`** (plugin `souroldgeezer-audit`) has a `config.yaml` controlling cost stance (`free` / `mixed` / `full`), with a documented resolution precedence (invocation arg > config.yaml > audited repo's `CLAUDE.md` § "Cost Guidance" > default `full`). Only `bicep.md` currently uses cost banding.
- **`test-quality-audit`** (plugin `souroldgeezer-audit`) dispatches on detected test type in step 0b to select one of three rubrics (unit / integration / E2E). Extensions can use either a single-file layout (`<stack>.md`) or a core + rubric-addon layout (`<stack>-core.md` plus `<stack>-unit.md`, `-integration.md`, `-e2e.md`). Three extensions currently use the core + rubric-addon layout: `.NET` (`dotnet-*.md`, covering xUnit / NUnit / MSTest / bUnit / Playwright .NET / Stryker.NET), `Node.js / TypeScript` (`nodejs-*.md`, covering Jest / Vitest / Mocha / `node:test` / Sinon / React Testing Library / Playwright JS / Cypress / WebdriverIO / Prisma / Drizzle / TypeORM / Knex / Stryker JS), and `Next.js` (`nextjs-*.md`, covering App Router / Pages Router / Route Handlers / Server Components / Server Actions / `proxy` v16+ and legacy `middleware` / `next-router-mock` / `next/experimental/testing/server` / Auth.js v5 `auth()` and legacy NextAuth). `.NET` was the reference implementation; `nodejs` mirrors its shape; `nextjs` is a **strict superset of nodejs** — when `next` is detected, `nodejs-core.md` always loads first, then `nextjs-core.md`. `nextjs.*` smells MAY carve out `nodejs.*` smells at Next-platform boundaries (`next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, `client-only`, `next/server`, `next/image`) but MUST NOT override them. The v16 `middleware` → `proxy` rename is detected via dual-file-shape matching; a project with both files flags a mid-migration state (`nextjs.LC-2`).
- **`responsive-design`** (plugin `souroldgeezer-design`) exposes three modes: **Build** (produce code embodying reference defaults, run §7 self-check), **Review** (walk §7 checklist, emit per-finding output with layer tags), **Lookup** (narrow-question answer). Checklist items in reference §7 carry verification-layer tags (`[static]` / `[dom]` / `[behaviour]` / `[visual]` / `[a11y-tool]` / `[runtime]`) distinguishing what the skill can verify from source alone vs. what requires a browser, axe-core, or RUM. Runs a pre-flight (locale / theme / stack / viewport floor / perf posture / **architecture pairing**) and a project-assimilation pass before generating or reviewing code. Extension pattern differs from audits: `extensions/blazor-wasm.md` covers hosting-model surface (standalone Blazor WebAssembly vs Blazor Web App `.Client`) and component-library reuse rules (MudBlazor / FluentUI Blazor / Radzen / Blazorise) rather than smell packs only. Review mode auto-dispatches to `architecture-design` (drift detection sub-behaviour) when a paired diagram exists at `docs/architecture/<feature>.oef.xml`.
- **`serverless-api-design`** (plugin `souroldgeezer-design`) exposes three modes: **Build** / **Review** / **Lookup** — same mode shape as `responsive-design`. Enforces non-negotiable baselines of security (Entra ID / managed identities / Key Vault / data-plane RBAC, `disableLocalAuth` on Cosmos, `allowSharedKeyAccess=false` on Storage), contract discipline (OpenAPI 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 conditional requests), reliability (idempotency on mutations, safe retries, 429 + `Retry-After`, poison / dead-letter), and observability (structured logs, W3C `traceparent`, correlation ID, per-request RU / request-charge visibility). §7 checklist items carry verification-layer tags (`[static]` / `[iac]` / `[contract]` / `[runtime]` / `[security-tool]` / `[load]`) distinguishing source-readable from runtime-observable. Runs a pre-flight (consumer scope / auth model / hosting stack / plan target / reliability posture / observability target / **architecture pairing**) and a project-assimilation pass. **Three composable extensions load together when the target spans those layers**: `azure-functions-dotnet.md` (isolated-worker only — in-process model blocked; retired 2026-11-10; `[BuiltIn]` vs `[AspNetCore]` HTTP response styles), `azure-cosmosdb.md` (`[Provisioned]` vs `[Serverless]` capacity surface; NoSQL API only), `azure-blob-storage.md` (`[SAS-direct]` vs `[API-proxy]` surface; user-delegation SAS as the canonical escape hatch for §3.12 large payloads). Extension smell-code namespaces are orthogonal (`afdotnet.*`, `cosmos.*`, `blob.*`). Review mode auto-dispatches to `architecture-design` (drift detection sub-behaviour) when a paired diagram exists at `docs/architecture/<feature>.oef.xml`.
- **`architecture-design`** (plugin `souroldgeezer-design`) is the first repo skill with a 4-mode shape: **Build** (architect intent → OEF XML model), **Extract** (code + IaC + workflows → OEF XML model, per-layer; Application / Technology / Implementation & Migration are liftable, Business / Motivation / Strategy / Physical are forward-only with a `FORWARD-ONLY — architect fills in` XML comment block), **Review** (artefact well-formedness via the `AD-*` smell catalog + drift detection against current code/IaC via the `AD-DR-*` codes), **Lookup** (narrow notation question). Sole notation is ArchiMate 3.2 (The Open Group, C226, March 2023). Sole serialisation is **OEF XML** per The Open Group ArchiMate Model Exchange File Format 3.2 (Appendix E of C226); output is tool-neutral and loadable in ArchiMate-conformant tools. The Open Group's XSD schemas are **not bundled** with the plugin; emitted files reference the canonical schema URL via `xsi:schemaLocation` and validation is delegated to the architect's toolchain (Archi's import or `xmllint`). Six supported diagram kinds (Capability Map, Application Cooperation, Application-to-Business Realisation, Technology Realisation, Migration, Motivation). Stack surface for Extract: .NET Azure Functions (isolated-worker), Blazor WebAssembly (standalone + Web App `.Client`), Bicep, `host.json`, `staticwebapp.config.json`, GitHub Actions workflows. Per-stack lifting rules live in `references/procedures/` (not `extensions/`) — extension approach differs from the sibling skills because the split is by input source (code / IaC / workflow), not by target stack choice. Smell-code namespace: `AD-*` for artefact smells, `AD-DR-*` for drift. Canonical-path convention `docs/architecture/<feature>.oef.xml` is the coupling mechanism with `responsive-design` and `serverless-api-design`, which auto-dispatch to `architecture-design` Review for drift detection when a paired model exists. BPMN and UML sequence modelling were considered and explicitly cancelled in v1.

## Things that are not standard Claude Code

- `skills/<skill>/config.yaml` — skill-internal, not read by the Claude Code runtime. Safe to leave alone when editing plugin metadata.
- `skills/<skill>/extensions/` and `skills/<skill>/references/` — skill-internal supporting files (docs allow arbitrary files alongside `SKILL.md`), not a Claude Code feature.
