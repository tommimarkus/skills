# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and Codex when working with code in this repository.

## What this repo is

A **Claude Code and Codex plugin marketplace**, not an application. The root `.claude-plugin/marketplace.json` registers the published `souroldgeezer-audit`, `souroldgeezer-design`, `souroldgeezer-architecture`, and `souroldgeezer-ops` plugin subdirectories and is intentionally shared by both runtimes; Codex can read this Claude-style repo marketplace directly, so do not duplicate it under `.agents/plugins/marketplace.json` unless a future design explicitly chooses to split catalogs. Each published plugin carries both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Published content is mostly Markdown + YAML + JSON. There is no plugin build, but the repo now has a small `uv`-managed Python® tooling surface for the skill architecture report. Validation is structural (correct filenames, frontmatter, schema, manifest sync via `jq`), semantic (does the skill's described workflow still match its SKILL.md), and script-level for `scripts/skill_architecture_report.py`.

## Runtime documentation cross-checks

When changing plugin packaging, marketplace wiring, install instructions, or
agent / skill exposure rules, cross-check **both** official runtime doc sets.
This is a cross-agent skills repo; a Codex-only or Claude-only reading is
insufficient.

- Claude Code sources: [Create plugins](https://code.claude.com/docs/en/plugins),
  [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces),
  and [Plugins reference](https://code.claude.com/docs/en/plugins-reference).
  These are the authority for `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, Claude Code `skills/`, Claude Code
  `agents/`, plugin source resolution, and marketplace strict-mode behaviour.
- Codex sources: [Plugins overview](https://developers.openai.com/codex/plugins),
  [Build plugins](https://developers.openai.com/codex/plugins/build), and
  [Codex skills](https://developers.openai.com/codex/skills), plus
  [Codex subagents](https://developers.openai.com/codex/subagents) when editing
  `.codex/agents/*.toml`. These are the authority for
  `.codex-plugin/plugin.json`, Codex `interface` metadata, Codex plugin
  marketplace handling, per-skill `agents/openai.yaml` metadata, how Codex
  activates bundled `skills/**/SKILL.md` workflows, and project-scoped custom
  agents.
- Repo rule: keep `.claude-plugin/marketplace.json` as the single shared
  marketplace while Codex supports Claude-style marketplaces. Do not add
  `.agents/plugins/marketplace.json` unless a future design explicitly chooses
  split catalogs.
- Codex local marketplace refresh note: `codex plugin marketplace upgrade <name>`
  refreshes Git-backed marketplaces, but the CLI reports that a local
  marketplace is not Git-backed. After local plugin source changes, refresh the
  changed plugin through the plugin browser, restart Codex, and verify the
  materialized cache path and bundled `skills/` directories.
- Keep `.codex-plugin/plugin.json#interface.defaultPrompt` to at most three
  entries; Codex warns and ignores extra starter prompts.

## Keeping CLAUDE.md, AGENTS.md, and README.md current (MUST)

**CLAUDE.md, AGENTS.md, and README.md MUST be kept up to date as the repo evolves.** They have different audiences and different triggers, but all are load-bearing — stale guidance in any of them causes downstream bugs. Treat drift in these files as a blocking bug and fix it in the same commit as the change that introduced the drift.

**CLAUDE.md audience:** Claude Code when authoring or editing skills in this repo. It is the first file Claude reads — stale guidance here causes stale reasoning everywhere else. Update CLAUDE.md whenever any of the following change:

- A plugin is added, removed, or renamed (update "Directory layout" and any plugin-level references).
- A skill is added, removed, renamed, or moved between plugins (or between a plugin and `undecided/`) (update "Skill-specific notes").
- A skill's mode set, output contract, or bundled-reference path changes (update "Skill architecture" and "Skill-specific notes").
- A new convention or pattern emerges across skills — new reference category (e.g. `docs/app-reference/`), new extension layout, new supporting-file kind, new required SKILL.md section (update "Directory layout" and "Skill architecture").
- Any statement in this file becomes factually wrong about the current repo state.

**README.md audience:** humans browsing the marketplace (GitHub™ readers, potential installers). It is the first file humans read. Update README.md whenever any of the following change:

- A plugin is added, removed, or renamed (update the intro paragraph, add/remove the corresponding "What's in `<plugin>`" section, update the repository-layout example).
- A skill is added or removed within a plugin (update the corresponding plugin's "What's in" table and its "How `<skill>` works" section).
- Install commands or marketplace slugs change for Claude Code or Codex (update "Install").
- Repository layout changes in a way a new reader would benefit from seeing (update "Repository layout").
- The audience-facing behaviour of a skill changes — new mode, new output format, new reference path (update the skill's "How it works" section).

**AGENTS.md audience:** Codex and other AGENTS.md-aware tooling. It is intentionally a thin pointer to this file, not a copy. Update AGENTS.md when the Codex entrypoint rules change, such as marketplace location, Codex manifest requirements, structured-file tooling rules, or the boundary between bundled skills and custom agents. Do not duplicate the full policy there; keep canonical details in CLAUDE.md.

Before finishing any task that changes repo structure or a skill's contract, re-read **all three files** and diff them mentally against the change. If any section is now wrong or incomplete, amend it in the same commit.

## Skill architecture craft standard (MUST)

For any task that creates, edits, reviews, triages, plans, or fixes a
skill-related surface, read [docs/skill-architecture.md](docs/skill-architecture.md)
before deciding scope or making edits. This includes published plugin skills,
matching agents, runtime metadata, bundled references, extensions, deterministic
machinery, manifests, marketplace entries, repo-internal `.claude/skills/**`
authoring skills, and README / CLAUDE / AGENTS sections that describe those
surfaces.

Treat the standard as the first design input and the report as the repeatable
check. The closeout gate is not a substitute for the initial read; loading the
standard only at the end misses trigger precision, workflow shape, context
discipline, runtime parity, and release-hygiene decisions while the change is
being made.

Before finishing any change on those surfaces, apply the standard and run
`scripts/skill-architecture-report.sh` when it is available. If the report
cannot run, record why and what narrower verification was used.

## Structured-file tooling

Use `jq` for JSON inspection, validation, and sync checks. Use Mike Farah
`yq` for YAML frontmatter, TOML, and XML inspection or validation. Avoid Python®
one-liners or `python3 -m json.tool` for structured JSON / YAML / TOML / XML
checks unless `jq` or `yq` cannot express the check.

## Repo-local Python® tooling

The public skill architecture validation command remains
`scripts/skill-architecture-report.sh [repo-root]`. It is a thin wrapper around
the Python® engine at `scripts/skill_architecture_report.py` and must be run
through `uv`. The command is tool-first: use its deterministic findings and
JSON output to keep skill workflows thin, and reserve LLM judgment for explicit
manual prompts the tool cannot decide. Use the repo-local project files
(`pyproject.toml`, `uv.lock`) and a local `.venv/` created with `uv venv`; do
not commit `.venv/`.

Primary checks:

```bash
bash scripts/skill-architecture-report.sh --help
uv run python scripts/skill_architecture_report.py .
uv run python scripts/skill_architecture_report.py --format json --strict .
uv run python -m unittest tests.skill_architecture_report_test
git diff --check
```

Report-engine coverage is ledger-backed. Add new cases one at a time to
`tests/skill_architecture_report_ledger.jsonl` with contiguous `SAC-T#####`
IDs, ordered complexity (`simple` → `moderate` → `complex` → `adversarial`),
and a unique intent. The unittest suite rejects duplicate IDs, duplicate
intents, and duplicate fixture/expectation fingerprints before executing the
case fixtures. The report's primary replacement claim is empirical: the
`Replacement Calibration` section runs the local gold ledger and reports how
many skill-only findings the tool detects automatically. Keep at least 500
gold-finding cases and `>=90%` automated replacement recall; catalog coverage is
secondary metadata, not the success criterion. When cases are bulk-generated,
update `tests/generate_skill_architecture_report_ledger.py` and regenerate the
JSONL ledger in the same change.

## Repo-internal skills

The repo ships a small set of **internal** skills under `.claude/skills/` — scoped to this repository, auto-discovered by Claude Code when working here, and deliberately *not* bundled with the distributed `souroldgeezer-*` plugins. Codex does not consume these as plugin content, but agents working in this repo should still follow them as repo authoring guidance when they apply. Internal skills encode how *we* author this repo; they are not capabilities shipped to downstream users.

Current internal skills:

- **`ip-hygiene`** at [.claude/skills/ip-hygiene/SKILL.md](.claude/skills/ip-hygiene/SKILL.md) — copyright, trademark, and licence check for any skill-related edit. Fast five-question triage, then copyright / trademark / licence check if triggered, with a concern→remedy mapping, an anti-drift fence-posts section recording deliberate non-changes, and an authoritative-sources appendix grouping EU + US + UK statute, directive, and case law. Invoke on any create / modify / rename / move / delete touching `souroldgeezer-*/skills/**`, `souroldgeezer-*/agents/**`, `souroldgeezer-*/docs/*-reference/**`, `.claude/skills/**`, Claude Code / Codex plugin manifests, marketplace manifests, or the `CLAUDE.md` / `AGENTS.md` / `README.md` sections that describe those artefacts; repo Stop hooks also prompt for this check when those surfaces change. Prevents verbatim reproduction of copyrighted spec prose / code / figures / samples, requires source citation as part of the paraphrase remedy, enforces ® / ™ on first-and-subsequent-significant public-visible mentions, applies the adjective-only rule for product / standard marks (corporate-name possessives outside scope), covers EU-only sui generis database right for structured spec tables, blocks bundling of third-party copyrighted assets unless the upstream licence permits redistribution, and preserves the repo's nominative-fair-use convention (no attribution blocks). Anchored in EU (EUTMR Art 14, *Gillette* C-228/03, *BMW v Deenik* C-63/97, InfoSoc Directive Art 5(3)(d), Database Directive 96/9, Software Directive 2009/24) and US (Lanham Act, *New Kids*, *Welles*, *Thaler v. Perlmutter* D.C. Cir. 2025) authority.
- **`github-issue-lifecycle`** at [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md) — repo-local overlay for explicit GitHub™ issue lifecycle requests in this repository. It composes the public `issue-ops` skill from `souroldgeezer-ops`, the GitHub™ provider extension, and this repository's defaults for `ip-hygiene`, `.worktrees/**`, direct-main handling, skill-architecture verification, published-surface synchronization, lifecycle status, and cleanup. Codex has a thin project-scoped wrapper at [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml) that points back to this overlay.

Skill architecture review is governed by the repo-wide craft-standard rule
above. Keep that rule early in this file so agents load the standard before
designing or editing skill-related surfaces.

Add to this section when new internal skills are introduced. Internal skills must not appear in `.claude-plugin/marketplace.json`, any plugin's `.claude-plugin/plugin.json`, or any plugin's `.codex-plugin/plugin.json`.

## Directory layout

```
AGENTS.md                              ← thin Codex-native pointer to CLAUDE.md
docs/skill-architecture.md             ← canonical skill architecture craft standard
scripts/skill-architecture-report.sh   ← craft-standard validation wrapper for agent iteration
scripts/skill_architecture_report.py   ← Python® validation engine and JSON/Markdown reporter
tests/skill_architecture_report_test.py ← unittest coverage for report fixtures and wrapper smoke
tests/skill_architecture_report_ledger.jsonl ← one-case-per-line report-engine test ledger
tests/generate_skill_architecture_report_ledger.py ← deterministic 500+ case ledger generator
pyproject.toml / uv.lock               ← uv-managed repo-local tooling project
.codex/agents/*.toml                   ← project-scoped Codex custom agents
.claude/skills/<name>/SKILL.md         ← repo-internal Claude Code skills, followed by Codex when AGENTS.md / CLAUDE.md says they apply
.claude-plugin/marketplace.json        ← shared Claude Code + Codex marketplace manifest
souroldgeezer-ops/                     ← published operations plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/issue-ops.md
  agents/pr-ops.md
  skills/issue-ops/SKILL.md
                  /agents/openai.yaml
                  /extensions/github.md ← GitHub™ provider mechanics
                  /extensions/gitlab.md ← GitLab™ provider mechanics
  skills/pr-ops/SKILL.md
               /agents/openai.yaml
               /extensions/github.md ← GitHub™ provider mechanics
               /extensions/gitlab.md ← GitLab™ provider mechanics
souroldgeezer-design/                  ← published software / app / API / infrastructure design plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/{software-design,app-design,api-design,infra-design}.md
  docs/software-reference/software-design.md
  docs/app-reference/app-design.md
  docs/api-reference/api-design.md
  docs/infra-reference/infra-design.md
  skills/{software-design,app-design,api-design,infra-design}/SKILL.md
  skills/{software-design,app-design,api-design,infra-design}/agents/openai.yaml
  skills/infra-design/extensions/ ← Azure®, Terraform™, and Bicep™ infrastructure-design overlays
  skills/infra-design/references/ ← behavioral evidence and source grounding
souroldgeezer-architecture/            ← published architecture plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/architecture-design.md
  docs/architecture-reference/architecture.md
  tools/dediren-linux/                 ← packaged dediren CLI bundle used by architecture-design
  skills/architecture-design/SKILL.md
                            /agents/openai.yaml
                            /references/ ← dediren package support, procedures, fixtures, evals, and source grounding
<plugin-name>/
  .claude-plugin/plugin.json           ← Claude Code plugin manifest
  .codex-plugin/plugin.json            ← Codex plugin manifest (points at ./skills/)
  docs/<kind>-reference/*.md           ← bundled reference prose (rubric, playbook, or similar)
  agents/<skill-name>.md               ← one Claude Code subagent per skill, same name
  skills/<skill-name>/SKILL.md         ← skill workflow
                     /agents/openai.yaml ← Codex per-skill UI metadata / invocation policy
                     /extensions/      ← per-stack packs (see below)
                     /references/      ← smell catalog + reusable procedures / scripts / packaged runtime artifacts where needed
                     /config.yaml      ← optional, skill-specific (not a Claude Code standard)
undecided/                             ← skills not yet assigned to a plugin (NOT in marketplace.json, NOT production-ready; do not reference from other skills)
  agents/<name>.md                     ← matching Claude Code subagents sit here too
  <skill-name>/                        ← same shape as a plugin's skill dir
```

Current `<kind>-reference/` directories in use:
- `souroldgeezer-audit/docs/security-reference/devsecops.md` — DevSecOps rubric
- `souroldgeezer-audit/docs/quality-reference/{unit,integration,e2e}-testing.md` — test-quality rubrics
- `souroldgeezer-design/docs/software-reference/software-design.md` — software-design playbook
- `souroldgeezer-design/docs/app-reference/app-design.md` — app-design playbook
- `souroldgeezer-design/docs/api-reference/api-design.md` — api-design playbook
- `souroldgeezer-design/docs/infra-reference/infra-design.md` — infra-design playbook
- `souroldgeezer-architecture/docs/architecture-reference/architecture.md` — architecture-design playbook (ArchiMate® 3.2)

Migration note: `architecture-design` moved from `souroldgeezer-design` to
`souroldgeezer-architecture`. Users who installed `souroldgeezer-design` for
architecture work must install `souroldgeezer-architecture@souroldgeezer`. The
current canonical handoff is the dediren package directory
`docs/architecture/<feature>.dediren/`.

When moving a skill out of `undecided/` into a plugin (or vice versa), **also move its matching subagent file** in `agents/<name>.md`. Skill and subagent are paired by identical name.

## Plugin registration

Adding a new plugin:
1. Create `<plugin-name>/.claude-plugin/plugin.json` (required: `name`, `version`, `description`; use `author: {name, email}` and `license: MIT` defaults from memory). Start at `0.1.0`.
2. Create `<plugin-name>/.codex-plugin/plugin.json` with the same `name`, `version`, `description`, `author`, and `license`; add `"skills": "./skills/"` and Codex `interface` metadata. Keep `interface.defaultPrompt` to three or fewer entries. Omit `apps` and `mcpServers` unless the plugin actually ships those surfaces.
3. For each bundled skill, add `skills/<skill>/agents/openai.yaml` with Codex per-skill UI metadata and invocation policy.
4. Add it to `.claude-plugin/marketplace.json` under `plugins[]` with `name`, `source: ./<plugin-name>`, `version`, `description`. This one marketplace is shared by Claude Code and Codex.
5. Plugin `name`, `description`, and `version` in both plugin manifests and in `marketplace.json#plugins[]` must stay in sync — every bump updates all three files in the same commit.

## Plugin versioning (MUST)

Plugins follow semver, with the repo-specific interpretation below. **The version bump lives in the same commit as the content change that required it** — never defer. Both plugin manifests (`<plugin>/.claude-plugin/plugin.json`, `<plugin>/.codex-plugin/plugin.json`) and the matching `marketplace.json#plugins[]` entry move together.

**What each bump kind means:**

- **Major (`X.0.0` → `(X+1).0.0`)** — a **backwards-incompatible** change. Downstream consumers who installed the previous version will see something they relied on break. Examples: a skill is removed or renamed; a reference file is moved or renamed; an output contract changes (smell-code prefix renamed, canonical path changed, frontmatter field removed); a mode is removed; the `plugin.json#name` changes.
- **Minor (`0.X.0` → `0.(X+1).0`)** — an **additive** change that existing consumers will not notice as a regression. Examples: a new skill is added to the plugin; a new extension is added under `skills/<skill>/extensions/`; a new mode is added to an existing skill; a new procedure is added under `references/procedures/`; a new reference section that shapes new output (a new `AD-L*` smell namespace, a new `§6.4a`); a new frontmatter field on a skill that downstream tooling may read.
- **Patch (`0.1.X` → `0.1.(X+1)`)** — **prose-only or no-op behavioural** changes. Examples: rubric / reference prose tightening, typo fixes, clarifying rewrites, tightening language in a skill description that doesn't change what the skill does, README / CLAUDE.md updates that mention the skill without changing its surface.

**When a bump is mandatory.** Commit touches any of the following under a `<plugin>/` directory:
- `skills/<skill>/SKILL.md`, `agents/<name>.md`, `docs/<kind>-reference/**`, `skills/<skill>/references/**`, `skills/<skill>/extensions/**` → at least *patch*.
- Any of the above that adds or removes a top-level artefact (skill, extension, agent, reference file, reference section, mode, smell namespace) → at least *minor*.
- Any of the above that renames, removes, or breaks the contract of an existing top-level artefact → *major*.

Edits that **do not** require a version bump: fixing broken links, adjusting whitespace, updating `docs/<kind>-reference/` cross-references between sections that already existed, editing repo-level `README.md` / `CLAUDE.md` outside the plugin tree, or changing packaging metadata that does not alter shipped skill behaviour and does not need to be picked up by installed-plugin update checks.

**Sibling-file sync.** A plugin-version bump often implies updates in neighbouring files that must land in the same commit:
- `.claude-plugin/plugin.json#version`, `.codex-plugin/plugin.json#version`, and `marketplace.json#plugins[].version` — always all three.
- `.claude-plugin/plugin.json#description`, `.codex-plugin/plugin.json#description`, and `marketplace.json#plugins[].description` — when the change alters the plugin's surface (new skill, new mode), update all three descriptions.
- Frontmatter `description:` in any affected `SKILL.md` and matching `agents/<name>.md` — when the change alters what the skill does; required to stay in sync per the subagent pattern (see "Subagents" below).
- `README.md` and `CLAUDE.md` — per the "Keeping CLAUDE.md and README.md current" rule above; the plugin bump and the documentation update are one commit.

**Retroactive right-sizing is allowed.** If several content-changing commits landed at the same `0.Y.Z`, a catch-up bump in the next content-change commit is acceptable — note the catch-up in the commit message. Going forward, bump one step per commit.

**Don't bump without content change.** A bare version-increment commit is a smell; it means earlier commits skipped their bump. Either the earlier commit is amended (rare — only before pushing) or the next content commit carries the catch-up.

## Skill architecture (shared pattern across skills)

Skills in this repo follow a recurring shape. Understand it before editing any SKILL.md:

- **Reference vs workflow separation.** SKILL.md is a *workflow* for applying a bundled reference; the reference prose lives in a separate file under `<plugin>/docs/<kind>-reference/*.md` (rubric for audits, playbook for design; see "Directory layout" for the current list). Relative paths like `../../docs/app-reference/app-design.md` resolve to these from a skill dir. SKILL.md must **cite** reference sections and codes — never duplicate reference prose.
- **Mode dispatch.** Every skill defines its own modes; each SKILL.md lists them. Audit skills (`devsecops-audit`, `test-quality-audit`) use **Quick** (single file / PR diff, per-finding output only) vs **Deep** (whole-repo, full sectioned rollup, may use MCP probes). Design skills use **Build** / **Extract** / **Review** / **Lookup** (`software-design`, `app-design`, `api-design`, `infra-design`, `architecture-design` — Extract is first-class for existing-code design baselines, frontend app baselines, API baselines, infrastructure/IaC baselines, and code-to-diagram lifting respectively). If the user request is ambiguous, the skill asks.
- **Output cites codes / sections, not prose.** Audit reports cite smell codes like `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`. Design output cites reference sections (`§3.11`, `§5.8`) plus WCAG SC numbers (`SC 1.4.10`, `SC 2.5.8`). Either way, SKILL.md and its output never duplicate reference prose.
- **Extensions are on-demand packs** in `skills/<skill>/extensions/*.md`. Most existing audit and design extensions are per-stack packs loaded from detected target type; `issue-ops` and `pr-ops` use provider extensions loaded from tracker or PR provider identity. For audits they **ADD** namespaced smells (`<ext>.HC-N`, `<ext>.LC-N`, `<ext>.POS-N`) or **CARVE OUT** core smells for idiomatic framework patterns; for design they also add stack-specific primitives, patterns, and project-assimilation rules (how to read the stack's token config, component library, cloud platform, or IaC source). For operations they add provider state, tooling, lifecycle-marker, issue-to-PR handoff, PR creation/reuse, review/comment/check handling, branch-update, integration, merge, close, and cleanup mechanics. Extensions **never override** core rules. Each skill's extension-authoring convention lives either in `extensions/README.md` or in a clearly named `references/procedures/*extension*.md` file loaded from `SKILL.md`; follow its required-sections list exactly when adding a new extension. `api-design` and `infra-design` both compose multiple extensions on the same target: an API on Azure® Functions™ .NET using Azure® Cosmos DB™ and Azure® Blob Storage™ loads all three API extensions at once; a hosted Next.js™ API loads `nodejs.md` first and then `nextjs.md`, plus matching data/storage extensions; Bicep™ infrastructure on Azure® loads `infra-design`'s `azure.md` and `bicep.md`; Terraform™ infrastructure on Azure® loads `azure.md` and `terraform.md`. Smell-code namespaces are orthogonal by construction (`afdotnet.*`, `nodejs.*`, `nextjs.*`, `cosmos.*`, `blob.*`, core `SAD-G-*`, core `ID-*`, `azure.ID-*`, `terraform.ID-*`, `bicep.ID-*`), so findings from different extensions never collide.
- **Supporting files live under `references/`** (audit skills, and design skills when needed). `references/smell-catalog.md` is the compact code index; `references/procedures/*.md` are reusable sub-procedures the workflow steps into; `references/scripts/*.sh` is allowed when a deterministic executable gate is part of the shipped skill workflow; `references/evals/*.jsonl` and `references/source-grounding.md` hold behavioral evidence when a skill carries trigger, workflow, source-grounding, or high-risk-gate evals. `app-design` and `api-design` use `references/` for behavioral evidence; `app-design` keeps stack-specific frontend application rules under `extensions/`; `software-design` uses a compact smell catalog plus behavioral evidence; `infra-design` uses behavioral evidence and source grounding under `references/` while Azure®, Terraform™, and Bicep™ rules live under `extensions/`; `architecture-design` uses `references/` for its finding catalog, package workflow procedures, source lifting rules, behavior evals, source grounding, and dediren package fixture.
- **Cross-skill coupling is via filesystem convention** (design skills). `architecture-design` uses `docs/architecture/<feature>.dediren/` as the canonical package directory. `app-design`, `api-design`, and `infra-design` check that directory when a paired architecture model may need drift review. Sibling skills do not reach into the `architecture-design` surface beyond this path.
- **Project assimilation is one-way** (design skills). Output assimilates the *project* to the *reference*, not the other way around. New code is always reference-compliant; non-compliant existing infrastructure is reused only when substantively compliant, otherwise flagged as legacy debt. See `app-design` or the generic design workflow rule in each `SKILL.md` for the canonical form.
- **Output footers disclose state.** Every report / build output ends with a footer listing which extensions loaded, MCP availability, cost stance (if applicable), reference path, and (design skills) project-assimilation summary. Don't remove these — they're how users audit the auditor / verify the builder.

## Subagents

Every skill has a matching Claude Code subagent at `<plugin>/agents/<skill-name>.md`. The subagent is a thin one-shot wrapper: it invokes the skill via the `Skill` tool, follows the skill's instructions, and presents results in the skill's required shape. Subagent frontmatter: `name`, `description` (mirror the skill's description for discoverability), `tools`, `model`. When editing a skill's invocation contract (output format, required footer fields), update the matching subagent.

Codex does not consume these plugin-root `agents/*.md` files. Codex installable plugin parity is carried by the bundled skills plus `skills/<skill>/agents/openai.yaml` metadata. Project-scoped Codex custom-agent wrappers live in `.codex/agents/*.toml`; each wrapper should point back to the matching skill as the source of truth and should not duplicate the reference prose. When editing a skill's invocation contract, update all three surfaces together: `SKILL.md`, the Claude Code subagent, and the Codex custom-agent wrapper / `openai.yaml` metadata.

## Skill-specific notes

- **`issue-ops`** (plugin `souroldgeezer-ops`) exposes lifecycle modes **full-cycle**, **triage-only**, **plan-only**, **implement-only**, and **resume** for explicit issue or work-item operations. The core is tracker-agnostic: it owns mode selection, queue limits, live-state authority, local recovery ledger, ask-vs-continue rules, escalation gates, verification inference, prepared-branch handoff, and completion output. Provider mechanics live in extensions. Current extensions are `extensions/github.md`, covering GitHub™ issue state, lifecycle marker comments, labels/projects/milestones context, GitHub™ MCP / `gh` / REST routing, `pr-ops` handoff, direct-main mode, linked pull requests, and issue closure; and `extensions/gitlab.md`, covering GitLab™ issue state, lifecycle notes, GitLab™ integration / `glab` / REST routing, `pr-ops` handoff limits, direct integration, linked issues, related merge requests, and closure safety. The repo-internal `.claude/skills/github-issue-lifecycle` skill is an overlay on this public skill, not a separate published workflow.
- **`pr-ops`** (plugin `souroldgeezer-ops`) exposes lifecycle modes **full-cycle**, **review-only**, **create-or-update**, **checks-only**, **address-feedback**, **merge-only**, and **resume** for explicit pull-request / merge-request operations and prepared PR/MR branches. The core is provider-agnostic: it owns mode selection, queue limits, live-state authority, local recovery ledger, ask-vs-continue rules, escalation gates, verification inference, PR/MR creation/reuse, full-cycle required-check monitoring, branch-update safety, merge/close authorization, cleanup, and completion output. Provider mechanics live in extensions. Current extensions are `extensions/github.md`, covering GitHub™ PR state, prepared branches, PR creation/reuse, reviews, review threads, comments, checks, pending-check monitoring, branch protection, GitHub™ MCP / `gh` / REST routing, branch update, merge, close, and branch cleanup; and `extensions/gitlab.md`, covering GitLab™ MR state, prepared branches, MR creation/reuse, notes, discussions, approvals, pipelines, pending-pipeline monitoring, protected branches, GitLab™ integration / `glab` / REST routing, rebase, merge, close, and branch cleanup. `pr-ops` is a sibling to `issue-ops`: it reports linked issue implications but does not take issue closure authority by default.
- **`devsecops-audit`** (plugin `souroldgeezer-audit`) has a `config.yaml` controlling cost stance (`free` / `mixed` / `full`), with a documented resolution precedence (invocation arg > config.yaml > audited repo's `CLAUDE.md` § "Cost Guidance" > default `full`). Only `bicep.md` currently uses cost banding.
- **`test-quality-audit`** (plugin `souroldgeezer-audit`) dispatches on detected test type in step 0b to select one of three rubrics (unit / integration / E2E). Extensions can use either a single-file layout (`<stack>.md`) or a core + rubric-addon layout (`<stack>-core.md` plus `<stack>-unit.md`, `-integration.md`, `-e2e.md`). Seven extensions currently use the core + rubric-addon layout: `.NET` (`dotnet-*.md`, covering xUnit / NUnit / MSTest / bUnit / Playwright .NET / Stryker.NET), Java™ (`java-*.md`, covering JUnit / TestNG / Mockito / Maven Surefire and Failsafe / Gradle test tasks / Testcontainers / REST Assured / Playwright Java™ / Selenium / PIT), `Node.js / TypeScript` (`nodejs-*.md`, covering Jest / Vitest / Mocha / `node:test` / Sinon / React Testing Library / Playwright JS / Cypress / WebdriverIO / Prisma / Drizzle / TypeORM / Knex / Stryker JS), `Next.js` (`nextjs-*.md`, covering App Router / Pages Router / Route Handlers / Server Components / Server Actions / `proxy` v16+ and legacy `middleware` / `next-router-mock` / `next/experimental/testing/server` / Auth.js v5 `auth()` and legacy NextAuth), Python® (`python-*.md`, covering pytest / unittest / Hypothesis / async tests / FastAPI / Starlette / Flask / Django / SQLAlchemy / Alembic / Playwright Python / Selenium / Mutmut), Robot Framework® (`robotframework-*.md`, covering `.robot` / `.resource` suites, Browser Library / SeleniumLibrary / AppiumLibrary E2E, RequestsLibrary / DatabaseLibrary / Process / SSH integration tests, keyword-layer unit tests, Pabot-style parallel suites, and Robot XML / xUnit artifacts), and Rust® (`rust-*.md`, covering Cargo/libtest/nextest tests, `tokio` / async tests, property tests, trait fakes and mocks, CLI/service/browser boundaries, cargo-mutants, and Cargo workspace surface gaps). `.NET` was the reference implementation; `nodejs` mirrors its shape; `nextjs` is a **strict superset of nodejs** — when `next` is detected, `nodejs-core.md` always loads first, then `nextjs-core.md`. `nextjs.*` smells MAY carve out `nodejs.*` smells at Next-platform boundaries (`next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, `client-only`, `next/server`, `next/image`) but MUST NOT override them. The v16 `middleware` → `proxy` rename is detected via dual-file-shape matching; a project with both files flags a mid-migration state (`nextjs.LC-2`).
- **`software-design`** (plugin `souroldgeezer-design`) exposes **Build** / **Extract** / **Review** / **Lookup** for code/module/script design: boundaries, responsibilities, dependency direction, state/data ownership, semantic coherence, coupling, evolutionary design, lightweight quality tradeoffs, socio-technical fit, and design-pattern tradeoffs. It deliberately delegates frontend app structure to `app-design`, HTTP API/runtime concerns to `api-design`, infrastructure/IaC topology to `infra-design`, ArchiMate®/OEF and model drift to `architecture-design`, security posture to `devsecops-audit`, and test-quality classification to `test-quality-audit`. On-demand support files are `references/smell-catalog.md`, `references/pattern-catalog.md`, and extensions for `.NET™`, Java™ package/module/build/API design, Rust® crate/workspace design, Bash/zsh shell scripts, and repo-internal Python® tooling; keep those extensions thin and justified by pressure evidence, not by generic language advice a strong base model already knows. Core smells use `SD-*`; extension smells use `dotnet.SD-*`, `java.SD-*`, `rust.SD-*`, `shell.SD-*`, and `python.SD-*`.
- **`app-design`** (plugin `souroldgeezer-design`) exposes four modes: **Build** (frontend app feature, route, screen, component set, form flow, navigation path, interaction, or browser-facing workflow), **Extract** (existing frontend app baseline), **Review** (route/screen/component architecture, state/data behavior, responsive/accessibility/performance posture, and browser runtime behavior), and **Lookup** (narrow frontend app design tradeoff). It owns component architecture, route/screen structure, frontend state/data ownership, rendering and browser boundaries, responsive behavior, accessibility, internationalization, visual behavior, and Core Web Vitals posture as mandatory layers. Its Blazor™ WebAssembly extension covers standalone Blazor WebAssembly, Blazor Web App `.Client`, route/layout ownership, component-library reuse, render-mode boundaries, state containers, JS interop, navigation, forms, storage, and app-design finding codes. `software-design` supports app-design underneath frontend features; `architecture-design` drift detection composes through `docs/architecture/<feature>.dediren/` when a paired model exists.
- **`api-design`** (plugin `souroldgeezer-design`) exposes four modes: **Build** / **Extract** / **Review** / **Lookup**. Build produces reference-compliant API contracts and implementation snippets; Extract maps an existing API baseline (contract shape, route surface, auth model, error shape, versioning, runtime stack, loaded runtime/data/storage extensions, legacy debt, and next smallest move); Review emits per-finding API-quality findings; Lookup answers narrow API questions with citations. It enforces non-negotiable baselines of security (OAuth 2.0 / OIDC or Microsoft® Entra ID™ where applicable, managed/workload identities where available, platform secret managers, data-plane RBAC, `disableLocalAuth` on Azure® Cosmos DB™, `allowSharedKeyAccess=false` on Azure® Storage), contract discipline (OpenAPI™ 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 conditional requests), reliability (idempotency on mutations, safe retries, 429 + `Retry-After`, poison / dead-letter), observability (structured logs, W3C® `traceparent`, correlation ID, per-request RU / request-charge / dependency-cost visibility), and honest verification-layer disclosure. §7 checklist items carry verification-layer tags (`[static]` / `[iac]` / `[contract]` / `[runtime]` / `[security-tool]` / `[load]`) distinguishing source-readable from runtime-observable. Runs a pre-flight (consumer scope / auth model / hosting stack / hosting target / reliability posture / observability target / **architecture pairing**) and a project-assimilation pass. **Composable extensions load together when the target spans those layers**: `azure-functions-dotnet.md` (Azure® Functions™ isolated worker only — in-process model blocked; retired 2026-11-10; `[BuiltIn]` vs `[AspNetCore]` HTTP response styles), `nodejs.md` (Node.js® / TypeScript hosted and serverless APIs: `[Hosted]` / `[Serverless]` / `[Adapter]`, package/runtime contract, Node `http` timeouts, body-size limits, AsyncLocalStorage, OpenTelemetry startup, serverless handler shape, reverse proxy, graceful shutdown), `nextjs.md` (hosted Next.js™ Route Handlers, Pages API routes, Server Actions, Route Segment Config, instrumentation, shared cache / deployment ID, Server Actions encryption key, self-hosted reverse proxy expectations; loads after `nodejs.md`), `azure-cosmosdb.md` (`[Provisioned]` vs `[Serverless]` Azure® Cosmos DB™ capacity surface; NoSQL API only), `azure-blob-storage.md` (`[SAS-direct]` vs `[API-proxy]` Azure® Blob Storage™ surface; user-delegation SAS as the canonical escape hatch for §3.12 large payloads). Extension smell-code namespaces are orthogonal (`afdotnet.*`, `nodejs.*`, `nextjs.*`, `cosmos.*`, `blob.*`). Extract and Review modes auto-dispatch to `architecture-design` drift review when a paired package exists at `docs/architecture/<feature>.dediren/`.
- **`infra-design`** (plugin `souroldgeezer-design`) exposes four modes: **Build** / **Extract** / **Review** / **Lookup**. Build produces compact infrastructure design briefs for topology, IaC structure, environment strategy, state and identity boundaries, rollout/rollback, operations handoff, validation, and delegations; Extract maps source-readable infrastructure baselines; Review emits per-finding infrastructure-design findings with `ID-*` / extension codes and verification-layer tags; Lookup answers narrow infrastructure tradeoff questions with citations. It owns IaC, cloud resources, deployment topology, environment promotion, state ownership, identity boundaries, rollout/rollback design, operations handoff, and drift-management design while delegating API contracts to `api-design`, code/module/script boundaries to `software-design`, web frontend app and UI concerns to `app-design`, ArchiMate® package and model drift to `architecture-design`, security posture to `devsecops-audit`, and test-quality work to `test-quality-audit`. §7 checklist items carry verification-layer tags (`[static]` / `[iac]` / `[plan]` / `[runtime]` / `[cloud-control-plane]` / `[human]`) so static source review does not claim cloud runtime, cost, quota, backup, failover, restore, or rollout facts. **Composable extensions load together when target signals overlap**: `azure.md` for Azure® infrastructure, `terraform.md` for Terraform™ IaC, and `bicep.md` for Bicep™ IaC on Azure®; Bicep™ targets on Azure® load `azure.md` plus `bicep.md`, and Terraform™ targets on Azure® load `azure.md` plus `terraform.md`. Core smells use `ID-*`; extension smells use `azure.ID-*`, `terraform.ID-*`, and `bicep.ID-*`.
- **`architecture-design`** (plugin `souroldgeezer-architecture`) exposes **Build** / **Extract** / **Review** / **Lookup** for ArchiMate® 3.2 architecture models stored as dediren packages. Canonical source is `docs/architecture/<feature>.dediren/`; `project.json` lists actual views, `model.json` carries model/source evidence, render policy and metadata drive SVG proof, and `export-policy.json` is optional compatibility export setup. Build and Extract edit package source and policies; Extract must emit source-backed groups for ownership, hosting, trust, environment, or dependency boundaries when evidence supports them; Review assesses source validity, view readability, SVG render evidence, optional export evidence, and drift; Lookup answers narrow notation or reverse-lookup questions without mutation. Active finding namespaces are `ARCH-M-*`, `ARCH-V-*`, `ARCH-L-*`, `ARCH-R-*`, `ARCH-X-*`, `ARCH-E-*`, and `ARCH-Q-*`. Supported diagram kinds are Capability Map, Application Cooperation, Service Realization, Technology Usage, Migration, Motivation, and Business Process Cooperation; missing kinds are footer disclosure, not placeholder views. The packaged dediren runtime is selected directly from `souroldgeezer-architecture/tools/dediren-linux/bin/dediren` or future `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`.
- **`architecture-design` runtime evidence** runs through dediren commands: `validate`, `project`, `layout`, `validate-layout`, `render`, and optional `export`. The bundled dediren 0.3.0 runtime enforces ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not `TechnologyNode`, for technology nodes, and reports close parallel route channels during layout validation. Missing bundles or error envelopes are reported as `not run` / blocking evidence rather than silently replaced. SVG is the default visual proof; optional OEF export is only required when the user asks for compatibility output or supplies downstream validation evidence.

## Things that are not standard Claude Code

- `skills/<skill>/config.yaml` — skill-internal, not read by the Claude Code runtime. Safe to leave alone when editing plugin metadata.
- `skills/<skill>/extensions/` and `skills/<skill>/references/` — skill-internal supporting files (docs allow arbitrary files alongside `SKILL.md`), not a Claude Code feature. Executable helpers under `references/scripts/` are bundled resources invoked by the skill, not runtime-discovered commands.
- `.codex-plugin/plugin.json` — Codex packaging metadata, not read by the Claude Code runtime. Keep it synchronized with the Claude Code manifest and marketplace entry.
- `skills/<skill>/agents/openai.yaml` — Codex per-skill UI metadata / invocation policy, not read by the Claude Code runtime.
- `.codex/agents/*.toml` — project-scoped Codex custom agents, not plugin-bundled and not read by the Claude Code runtime.
