# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and Codex when working with code in this repository.

## What this repo is

A **Claude Code and Codex plugin marketplace**, not an application. The shared root `.claude-plugin/marketplace.json` registers the published plugins (`souroldgeezer-audit`, `-design`, `-architecture`, `-policy`, `-ops`) and is read by both runtimes — Codex reads this Claude-style marketplace directly, so do not duplicate it under `.agents/plugins/marketplace.json` unless a future design explicitly splits catalogs. Each published plugin carries both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Content is mostly Markdown + YAML + JSON; there is no plugin build, but a small `uv`-managed Python® surface backs the skill architecture report. Validation is structural (filenames, frontmatter, schema, manifest sync via `jq`), semantic (does the described workflow still match SKILL.md), and script-level for `scripts/skill_architecture_report.py`.

## Runtime documentation cross-checks

When changing plugin packaging, marketplace wiring, install instructions, or agent / skill exposure rules, cross-check **both** official runtime doc sets — a Codex-only or Claude-only reading is insufficient.

- Claude Code: [Create plugins](https://code.claude.com/docs/en/plugins), [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces), [Plugins reference](https://code.claude.com/docs/en/plugins-reference) — authority for `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, Claude Code `skills/` and `agents/`, plugin source resolution, and marketplace strict-mode behaviour.
- Codex: [Plugins overview](https://developers.openai.com/codex/plugins), [Build plugins](https://developers.openai.com/codex/plugins/build), [Codex skills](https://developers.openai.com/codex/skills), and [Codex subagents](https://developers.openai.com/codex/subagents) (when editing `.codex/agents/*.toml`) — authority for `.codex-plugin/plugin.json`, Codex `interface` metadata, marketplace handling, per-skill `agents/openai.yaml`, how Codex activates bundled `skills/**/SKILL.md`, and project-scoped custom agents.
- Keep `.claude-plugin/marketplace.json` as the single shared marketplace while Codex supports Claude-style marketplaces; do not add `.agents/plugins/marketplace.json` unless a future design splits catalogs.
- Codex local refresh: `codex plugin marketplace upgrade <name>` refreshes Git-backed marketplaces but reports a local marketplace as not Git-backed. After local plugin source changes, refresh the changed plugin through the plugin browser, restart Codex, and verify the materialized cache path and bundled `skills/` directories.
- Keep `.codex-plugin/plugin.json#interface.defaultPrompt` to at most three entries; Codex warns and ignores extras.

## Keeping CLAUDE.md, AGENTS.md, and README.md current (MUST)

**All three MUST be kept current as the repo evolves** — each is load-bearing, and stale guidance causes downstream bugs. Treat drift as a blocking bug; fix it in the same commit that introduced it. Before finishing any task that changes repo structure or a skill's contract, re-read all three and amend any section now wrong or incomplete.

**CLAUDE.md** (audience: Claude Code authoring/editing skills here; first file Claude reads). Update when:
- a plugin is added/removed/renamed (→ "Directory layout", plugin references);
- a skill is added/removed/renamed or moved between plugins or `undecided/` (→ "Skill-specific notes");
- a skill's mode set, output contract, or bundled-reference path changes (→ "Skill architecture", "Skill-specific notes");
- a new cross-skill convention emerges — reference category (e.g. `docs/app-reference/`), extension layout, supporting-file kind, required SKILL.md section (→ "Directory layout", "Skill architecture");
- any statement here becomes factually wrong.

**README.md** (audience: humans browsing the marketplace). Update when:
- a plugin is added/removed/renamed (intro, the "What's in `<plugin>`" section, layout example);
- a skill is added/removed within a plugin (that plugin's "What's in" table and its "How `<skill>` works" section);
- install commands or marketplace slugs change (→ "Install");
- repository layout changes a new reader benefits from (→ "Repository layout");
- a skill's audience-facing behaviour changes — new mode, output format, reference path (→ that skill's "How it works").

**AGENTS.md** (audience: Codex and AGENTS.md-aware tooling). A thin pointer to this file, not a copy. Update only when Codex entrypoint rules change (marketplace location, Codex manifest requirements, structured-file tooling, the bundled-skills vs custom-agents boundary). Keep canonical details here.

## Skill architecture craft standard (MUST)

For any task that creates, edits, reviews, triages, plans, or fixes a skill-related surface, read [docs/skill-architecture.md](docs/skill-architecture.md) **before** deciding scope or making edits. This covers published plugin skills, matching agents, runtime metadata, bundled references, extensions, deterministic machinery, manifests, marketplace entries, repo-internal `.claude/skills/**` authoring skills, and the README / CLAUDE / AGENTS sections describing them.

The standard is the first design input; the report is the repeatable check. Loading the standard only at closeout misses trigger precision, workflow shape, context discipline, runtime parity, and release-hygiene decisions made while changing the code. Before finishing, apply the standard and run `scripts/skill-architecture-report.sh` when available; if it cannot run, record why and what narrower verification was used.

## Structured-file tooling

Use `jq` for JSON inspection, validation, and sync checks. Use Mike Farah `yq` for YAML frontmatter, TOML, and XML. Avoid Python® one-liners or `python3 -m json.tool` for structured JSON / YAML / TOML / XML checks unless `jq` / `yq` cannot express the check.

## Git ignore hygiene (MUST)

Treat `.gitignore` as a hard staging boundary. Do not force-add ignored files (`git add -f` / `--force`, `git update-index --add`, or equivalents) unless the user explicitly names the exact ignored path and says it should be tracked. Broad approval to stage or commit is not approval to bypass `.gitignore`.

Before committing, run `git ls-files -ci --exclude-standard`. The output must be empty unless the same task documents a deliberate, path-specific tracked exception. If it lists a tracked ignored path, uncommit it immediately with `git rm --cached -- <path>` (keeping the working-tree copy); don't defer cleanup.

Ignored local state and scratch trees — `docs/superpowers/**`, `.cache/**`, `.worktrees/**`, `.venv/**`, `.codex/config.toml`, `.mcp.json` — are local-only by default.

## Repo-local Python® tooling

The public validation command is `scripts/skill-architecture-report.sh [repo-root]`, a thin `uv`-run wrapper around the Python® engine `scripts/skill_architecture_report.py`. It is tool-first: use its deterministic findings and JSON output to keep skill workflows thin, and reserve LLM judgment for explicit manual prompts the tool cannot decide. Use the repo-local `pyproject.toml` / `uv.lock` and a local `.venv/` from `uv venv`; do not commit `.venv/`.

`pyproject.toml` sets `[tool.uv] cache-dir = ".cache/uv"`. Run `uv` from the repo root, or via wrappers (such as `scripts/skill-architecture-report.sh`) that `cd` there first. Do not add `UV_CACHE_DIR=/tmp/codex-uv-cache` to plans or normal verification; confirm the repo-local cache with `uv cache dir` and override `UV_CACHE_DIR` only as a one-off fallback when the repo config isn't applied or the reported path isn't writable.

Primary checks:

```bash
bash scripts/skill-architecture-report.sh --help
uv run python scripts/skill_architecture_report.py .
uv run python scripts/skill_architecture_report.py --format json --strict .
uv run python -m unittest tests.skill_architecture_report_test
git diff --check
```

Report-engine coverage is ledger-backed. Add cases one at a time to `tests/skill_architecture_report_ledger.jsonl` with contiguous `SAC-T#####` IDs, ordered complexity (`simple` → `moderate` → `complex` → `adversarial`), and a unique intent; the unittest suite rejects duplicate IDs, intents, and fixture/expectation fingerprints before executing the cases. The report's primary replacement claim is empirical: the `Replacement Calibration` section runs the local gold ledger and reports how many skill-only findings the tool detects automatically — keep ≥500 gold-finding cases and ≥90% automated replacement recall (catalog coverage is secondary metadata, not the success criterion). When cases are bulk-generated, update `tests/generate_skill_architecture_report_ledger.py` and regenerate the JSONL in the same change.

## Repo-internal skills

The repo ships a small set of **internal** skills under `.claude/skills/` — repo-scoped, auto-discovered by Claude Code here, and deliberately *not* bundled with the published `souroldgeezer-*` plugins. Codex doesn't consume them as plugin content, but agents working here should follow them as authoring guidance when they apply. They encode how *we* author this repo, not capabilities shipped downstream.

`ip-hygiene` formerly lived here but is now a public skill in `souroldgeezer-audit` at [souroldgeezer-audit/skills/ip-hygiene/SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md).

Current internal skills:

- **`github-issue-lifecycle`** at [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md) — repo-local overlay for explicit GitHub™ issue lifecycle requests here. Composes the public `issue-ops` skill, the GitHub™ provider extension, and this repo's defaults (`ip-hygiene`, `.worktrees/**`, direct-main handling, skill-architecture verification, published-surface sync, lifecycle status, cleanup). Codex has a thin wrapper at [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml) pointing back to it.

Add here when new internal skills appear. Internal skills must not appear in `.claude-plugin/marketplace.json` or any plugin's `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`.

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
  agents/{issue-ops,pr-ops}.md
  skills/issue-ops/SKILL.md
                  /agents/openai.yaml
                  /extensions/github.md ← GitHub™ provider mechanics
                  /extensions/gitlab.md ← GitLab™ provider mechanics
  skills/pr-ops/SKILL.md
               /agents/openai.yaml
               /extensions/github.md ← GitHub™ provider mechanics
               /extensions/gitlab.md ← GitLab™ provider mechanics
souroldgeezer-policy/                  ← published passive policy plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/{git-workflow-policy,release-policy}.md
  skills/git-workflow-policy/SKILL.md
                            /agents/openai.yaml
                            /references/ ← initialized policy, source grounding, and evals
  skills/release-policy/SKILL.md
                       /agents/openai.yaml
                       /references/ ← declarative release policy, source grounding, and evals
souroldgeezer-audit/                   ← published DevSecOps, test-quality, and IP hygiene audit plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/devsecops-audit.md
  agents/test-quality-audit.md
  agents/ip-hygiene.md
  docs/security-reference/devsecops.md
  docs/quality-reference/{unit,integration,e2e}-testing.md
  skills/devsecops-audit/SKILL.md
                        /agents/openai.yaml
                        /extensions/ ← per-stack security-audit overlays
  skills/test-quality-audit/SKILL.md
                           /agents/openai.yaml
                           /extensions/ ← per-stack test-quality audit overlays
                           /references/ ← behavior evals and source grounding
  skills/ip-hygiene/SKILL.md
                   /agents/openai.yaml
                   /references/ ← copyright, trademark, licence/assets, drive-by, authority, fence-posts, evals, and source grounding
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
  skills/app-design/extensions/ ← React, Next.js, and Blazor WebAssembly app-design overlays
  skills/api-design/extensions/ ← Azure Functions .NET, Node.js, hosted Next.js, Cosmos DB, and Blob Storage API overlays
  skills/infra-design/extensions/ ← Azure®, Terraform™, and Bicep™ infrastructure-design overlays
  skills/infra-design/references/ ← behavioral evidence and source grounding
souroldgeezer-architecture/            ← published architecture plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/architecture-design.md
  docs/architecture-reference/architecture.md
  skills/architecture-design/SKILL.md
                            /agents/openai.yaml
                            /references/ ← dediren release resolver, package support, procedures, fixtures, evals, and source grounding
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
- `souroldgeezer-architecture/docs/architecture-reference/architecture.md` — architecture-design playbook (ArchiMate® 3.2, with UML® notation overlays under the skill references)

Migration note: `architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.

When moving a skill out of `undecided/` into a plugin (or vice versa), **also move its matching subagent file** in `agents/<name>.md`. Skill and subagent are paired by identical name.

## Plugin registration

Adding a new plugin:
1. `<plugin-name>/.claude-plugin/plugin.json` (required `name`, `version`, `description`; `author: {name, email}` and `license: MIT` defaults from memory; start at `0.1.0`).
2. `<plugin-name>/.codex-plugin/plugin.json` with the same `name` / `version` / `description` / `author` / `license`, plus `"skills": "./skills/"` and Codex `interface` metadata (`interface.defaultPrompt` ≤ three entries; omit `apps` / `mcpServers` unless the plugin ships them).
3. For each bundled skill, `skills/<skill>/agents/openai.yaml` with Codex UI metadata and invocation policy.
4. Add to `.claude-plugin/marketplace.json` under `plugins[]` (`name`, `source: ./<plugin-name>`, `version`, `description`) — this one marketplace is shared by both runtimes.
5. `name` / `description` / `version` must stay in sync across both manifests and `marketplace.json#plugins[]` — every bump updates all three in the same commit.

## Plugin versioning (MUST)

Plugins follow semver with the interpretation below. **The version bump lives in the same commit as the content change that required it** — never defer; both plugin manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) and the `marketplace.json#plugins[]` entry move together.

**Bump kinds:**
- **Major** (`X.0.0` → `(X+1).0.0`) — backwards-incompatible; something a downstream consumer relied on breaks. E.g. a skill removed/renamed; a reference file moved/renamed; an output contract changes (smell-code prefix renamed, canonical path changed, frontmatter field removed); a mode removed; `plugin.json#name` changes.
- **Minor** (`0.X.0` → `0.(X+1).0`) — additive, no regression. E.g. a new skill, extension, mode, or `references/procedures/` entry; a new reference section shaping new output (new `AD-L*` namespace, new `§6.4a`); a new SKILL.md frontmatter field downstream tooling may read.
- **Patch** (`0.1.X` → `0.1.(X+1)`) — prose-only or no-op behavioural. E.g. rubric/reference tightening, typos, clarifying rewrites, description language that doesn't change behaviour, README / CLAUDE.md mentions.

**Mandatory bump** when a commit touches, under a `<plugin>/`: `skills/<skill>/SKILL.md`, `agents/<name>.md`, `docs/<kind>-reference/**`, `skills/<skill>/references/**`, `skills/<skill>/extensions/**` → at least *patch*; adding/removing a top-level artefact (skill, extension, agent, reference file, reference section, mode, smell namespace) → at least *minor*; renaming/removing/breaking an existing top-level artefact's contract → *major*.

**Major/minor IP hygiene gate.** Every major or minor change requires an in-depth `ip-hygiene` run before finishing, scoped to the whole changed plugin surface (added/moved/renamed/removed/contract-shaping skills, agents, references, extensions, deterministic machinery, manifests, marketplace entries, public repo guidance); load every hit bucket from the workflow and report its normal output contract in closeout. Patch bumps use the normal scoped IP hygiene triage.

**No bump needed:** fixing broken links, whitespace, `docs/<kind>-reference/` cross-references between sections that already existed, repo-level `README.md` / `CLAUDE.md` edits outside the plugin tree, or packaging metadata that doesn't alter shipped behaviour or need pickup by installed-plugin update checks.

**Sibling-file sync** (same commit):
- `.claude-plugin/plugin.json#version`, `.codex-plugin/plugin.json#version`, `marketplace.json#plugins[].version` — always all three.
- the three `#description` fields — when the change alters the plugin's surface (new skill, new mode).
- `description:` frontmatter in any affected `SKILL.md` and matching `agents/<name>.md` — when what the skill does changes (required by the subagent pattern; see "Subagents").
- `README.md` and `CLAUDE.md` — per the currency rule above; one commit.

**Retroactive right-sizing is allowed.** If several content commits landed at one `0.Y.Z`, a catch-up bump in the next content commit is fine — note it in the message; thereafter bump one step per commit.

**Don't bump without content change.** A bare version-increment commit is a smell (earlier commits skipped bumps); amend the earlier commit (rare — only before pushing) or carry the catch-up in the next content commit.

## Skill architecture (shared pattern across skills)

Skills here follow a recurring shape. Understand it before editing any SKILL.md:

- **Reference vs workflow separation.** SKILL.md is a *workflow* for applying a bundled reference; the reference prose lives under `<plugin>/docs/<kind>-reference/*.md` (rubric for audits, playbook for design — see "Directory layout"). Relative paths like `../../docs/app-reference/app-design.md` resolve from a skill dir. SKILL.md **cites** reference sections and codes, never duplicates prose.
- **Mode dispatch.** Each SKILL.md lists its modes. Audit skills (`devsecops-audit`, `test-quality-audit`): **Quick** (single file / PR diff, per-finding output only) vs **Deep** (whole-repo, full sectioned rollup, may use MCP probes). Design skills: **Build / Extract / Review / Lookup** — Extract is first-class for existing-code, frontend-app, API, and IaC baselines and code-to-diagram lifting. Ambiguous request → the skill asks.
- **Output cites codes / sections, not prose.** Audit reports cite smell codes (`DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`); design output cites reference sections (`§3.11`, `§5.8`) plus WCAG SC numbers (`SC 1.4.10`, `SC 2.5.8`). Never duplicate reference prose.
- **Extensions are on-demand packs** in `skills/<skill>/extensions/*.md`, loaded from detected target / provider. Audit and design extensions are per-stack; `issue-ops` / `pr-ops` use provider extensions; `git-workflow-policy` / `release-policy` start provider-agnostic, adding extensions later only when initialized options can't stay compact. For audits, extensions **ADD** namespaced smells (`<ext>.HC-N` / `.LC-N` / `.POS-N`) or **CARVE OUT** core smells for idiomatic framework patterns; for design, they also add stack-specific primitives, patterns, and project-assimilation rules (reading the stack's token config, component library, cloud platform, IaC source); for operations, they add provider state / tooling / lifecycle-marker / issue-to-PR handoff / PR creation-reuse / review-comment-check / branch-update / integration / merge / close / cleanup mechanics; policy skills prefer declarative initialization options over provider lifecycle extensions. Extensions **never override** core rules. Each skill's extension-authoring convention lives in `extensions/README.md` or a `references/procedures/*extension*.md` loaded from SKILL.md — follow its required-sections list exactly. Multi-extension composition: a Next.js app loads `react.md` then `nextjs.md`; an Azure® Functions™ .NET API on Cosmos DB™ + Blob Storage™ loads all three API extensions; a hosted Next.js™ API loads `nodejs.md` then `nextjs.md` plus matching data/storage extensions; Bicep™ on Azure® loads `azure.md` + `bicep.md`; Terraform™ on Azure® loads `azure.md` + `terraform.md`. Namespaces are orthogonal by construction (`react.APP-*`, `nextjs.APP-*`, `blazor.APP-*`, `afdotnet.*`, `nodejs.*`, `nextjs.*`, `cosmos.*`, `blob.*`, core `SAD-G-*`, core `ID-*`, `azure.ID-*`, `terraform.ID-*`, `bicep.ID-*`), so findings never collide.
- **Supporting files live under `references/`** (audit skills, and design skills when needed): `smell-catalog.md` (compact code index), `procedures/*.md` (reusable sub-procedures the workflow steps into), `scripts/*.sh` (allowed when a deterministic executable gate ships with the skill), `evals/*.jsonl` + `source-grounding.md` (behavioral evidence for trigger / workflow / source-grounding / high-risk-gate evals). `software-design`, `app-design`, `api-design`, `infra-design` use skill-local `references/procedures/project-assimilation.md` for existing-codebase discovery, reuse/debt classification, and migration disclosure. `app-design` keeps stack rules under `extensions/`; `software-design` uses a compact smell catalog + evidence; `infra-design` keeps evidence/source-grounding under `references/` while Azure® / Terraform™ / Bicep™ rules live under `extensions/`; `architecture-design` uses `references/` for notation references, finding catalog, package workflow procedures, source-lifting rules, evals, source grounding, and the dediren package fixture.
- **Cross-skill coupling is via filesystem convention** (design skills). `architecture-design` owns `docs/architecture/<feature>.dediren/`; `app-design`, `api-design`, `infra-design` check that path when a paired model may need drift review. Siblings don't reach into the architecture-design surface beyond this path.
- **Project assimilation is one-way** (design skills). Assimilate the *project* to the *reference*, not vice versa. New code is always reference-compliant; non-compliant existing infrastructure is reused only when substantively compliant, else flagged as legacy debt. Load skill-local `project-assimilation.md` when existing source, app structure, API wiring, IaC, diffs, or runtime/config evidence is in scope. Footer shape: `Project assimilation:` with `Reused`, `Legacy debt`, `Migrations performed`.
- **Output footers disclose state.** Every report / build output ends with a footer listing loaded extensions, MCP availability, cost stance (if applicable), reference path, and (design skills) project-assimilation summary. Don't remove them — they're how users audit the auditor / verify the builder.

## Subagents

Every skill has a matching Claude Code subagent at `<plugin>/agents/<skill-name>.md` — a thin one-shot wrapper that invokes the skill via the `Skill` tool, follows its instructions, and presents results in the skill's required shape. Frontmatter: `name`, `description` (mirror the skill's for discoverability), `tools`, `model`.

Codex doesn't consume these plugin-root `agents/*.md` files; its installable-plugin parity is the bundled skills plus `skills/<skill>/agents/openai.yaml`, with project-scoped wrappers in `.codex/agents/*.toml` that point back to the matching skill and don't duplicate reference prose. When editing a skill's invocation contract (output format, required footer fields), update all three together: `SKILL.md`, the Claude Code subagent, and the Codex wrapper / `openai.yaml`.

## Skill-specific notes

- **`issue-ops`** (`souroldgeezer-ops`) — modes **full-cycle / triage-only / plan-only / implement-only / resume** for explicit issue / work-item operations. Tracker-agnostic core owns mode selection, queue limits, live-state authority, local recovery ledger, ask-vs-continue rules, escalation gates, verification inference, prepared-branch handoff, and completion output; provider mechanics live in extensions. `extensions/github.md`: GitHub™ issue state, lifecycle marker comments, labels/projects/milestones, GitHub™ MCP / `gh` / REST routing, `pr-ops` handoff, direct-main mode, linked PRs, closure. `extensions/gitlab.md`: GitLab™ issue state, lifecycle notes, integration / `glab` / REST routing, `pr-ops` handoff limits, direct integration, linked issues, related MRs, closure safety. The internal `github-issue-lifecycle` skill is an overlay on this, not a separate published workflow.
- **`pr-ops`** (`souroldgeezer-ops`) — modes **full-cycle / review-only / create-or-update / checks-only / address-feedback / merge-only / resume** for explicit PR/MR operations and prepared branches. Provider-agnostic core owns mode selection, queue limits, live-state authority, local recovery ledger, ask-vs-continue rules, escalation gates, verification inference, PR/MR creation/reuse, full-cycle required-check monitoring, branch-update safety, merge/close authorization, cleanup, and completion output; provider mechanics live in extensions. `extensions/github.md`: GitHub™ PR state, prepared branches, creation/reuse, reviews, review threads, comments, checks, pending-check monitoring, branch protection, GitHub™ MCP / `gh` / REST routing, branch update, merge, close, cleanup. `extensions/gitlab.md`: GitLab™ MR state, prepared branches, creation/reuse, notes, discussions, approvals, pipelines, pending-pipeline monitoring, protected branches, integration / `glab` / REST routing, rebase, merge, close, cleanup. Sibling to `issue-ops`: reports linked-issue implications but doesn't take issue-closure authority by default.
- **`git-workflow-policy`** (`souroldgeezer-policy`) — **lookup / inspect / adopt-guidance / preflight / enforce-initialized** modes for developer-facing git workflow policy. Passive until a target repo initializes the skill in its guidance, or the user explicitly asks; once initialized, repo guidance is standing enforcement authority before matching git actions, even when unnamed in the task. Adopt-guidance consolidates existing branch / staging / commit / worktree / PR-MR-handoff guidance into initialization options or adjacent local exceptions, then removes competing prose. Bare initialization applies the conservative default profile: feature branch/worktree for non-trivial work, clean default branch unless overridden, status checks before edits/staging, explicit path staging, preservation of unrelated work, no force-add ignored files, verification before handoff, stop before destructive git actions. Owns branch strategy, staging/commit policy, working-tree hygiene, PR/MR handoff, merge/rebase/squash expectations, protected-branch expectations, destructive-action gates, project-local exceptions, and version-policy placement during development. Delegates PR/MR lifecycle → `pr-ops`, issue lifecycle → `issue-ops`, distribution → `release-policy`, security release controls → `devsecops-audit`, test adequacy → `test-quality-audit`.
- **`release-policy`** (`souroldgeezer-policy`) — **lookup / preflight / adopt-guidance / enforce-initialized / prepare-release / cut-release / publish / post-release / resume** modes for distribution-facing policy. Passive until initialized in target repo guidance or explicitly requested; once initialized, repo guidance is standing enforcement authority before matching release actions, even when unnamed. Adopt-guidance consolidates existing version / changelog / tag / provider-release / publication / rollback / post-release guidance into initialization options or local exceptions, then removes competing prose. Bare initialization default profile: SemVer intent, single inferred version source, annotated `v<version>` git tags, repo-defined releasable-change detection, verification before version/tag writes, no provider release or publication without explicit target authority. Initialization can be declarative, e.g. `release-policy: calver YYYY.MM.build, git tagging` — granting standing authority for routine version updates and git tag creation for repo-defined releasable changes after verification. Owns release readiness, concrete version updates, changelog / release notes, tag creation/inspection, provider release state, package or marketplace publication when the policy or user names the target, post-release verification, rollback/deprecation notes, project-local exceptions. Applies `git-workflow-policy` preflight before release writes; delegates PR/MR lifecycle → `pr-ops`.
- **`devsecops-audit`** (`souroldgeezer-audit`) — `config.yaml` controls cost stance (`free` / `mixed` / `full`); resolution precedence: invocation arg > config.yaml > audited repo's `CLAUDE.md` § "Cost Guidance" > default `full`. Only `bicep.md` currently uses cost banding.
- **`test-quality-audit`** (`souroldgeezer-audit`) — step 0b dispatches on detected test type to one of three rubrics (unit / integration / E2E). Extensions use either a single-file layout (`<stack>.md`) or core + rubric-addon (`<stack>-core.md` plus `-unit` / `-integration` / `-e2e.md`). Seven use core + rubric-addon: `.NET` (`dotnet-*`: xUnit / NUnit / MSTest / bUnit / Playwright .NET / Stryker.NET), Java™ (`java-*`: JUnit / TestNG / Mockito / Maven Surefire and Failsafe / Gradle test tasks / Testcontainers / REST Assured / Playwright Java™ / Selenium / PIT), Node.js / TypeScript (`nodejs-*`: Jest / Vitest / Mocha / `node:test` / Sinon / React Testing Library / Playwright JS / Cypress / WebdriverIO / Prisma / Drizzle / TypeORM / Knex / Stryker JS), Next.js (`nextjs-*`: App / Pages Router / Route Handlers / Server Components / Server Actions / `proxy` v16+ and legacy `middleware` / `next-router-mock` / `next/experimental/testing/server` / Auth.js v5 `auth()` and legacy NextAuth), Python® (`python-*`: pytest / unittest / Hypothesis / async / FastAPI / Starlette / Flask / Django / SQLAlchemy / Alembic / Playwright Python / Selenium / Mutmut), Robot Framework® (`robotframework-*`: `.robot` / `.resource` suites, Browser / Selenium / Appium E2E, Requests / Database / Process / SSH integration, keyword-layer unit, Pabot-style parallel suites, Robot XML / xUnit artifacts), and Rust® (`rust-*`: Cargo / libtest / nextest, `tokio` / async, property tests, trait fakes/mocks, CLI/service/browser boundaries, cargo-mutants, Cargo workspace surface gaps). `.NET` was the reference; `nodejs` mirrors it; `nextjs` is a **strict superset of nodejs** — when `next` is detected, `nodejs-core.md` loads first, then `nextjs-core.md`. `nextjs.*` smells MAY carve out `nodejs.*` smells at Next-platform boundaries (`next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, `client-only`, `next/server`, `next/image`) but MUST NOT override them. The v16 `middleware` → `proxy` rename is detected via dual-file-shape matching; both files present flags mid-migration (`nextjs.LC-2`).
- **`ip-hygiene`** (`souroldgeezer-audit`, [SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md)) — owns public copyright, trademark, licence, and bundled-asset hygiene for skill/plugin publication surfaces: skills, agents, bundled references, extensions, deterministic machinery, manifests, marketplace/runtime metadata, bundled assets, and repo guidance describing them. Project conventions resolve by explicit user instruction > target repo guidance > skill default. Output contract is terse (`nothing to check`, `checked: ...`, `fixed: ...`, `deferred drive-by observation ...`). Repo Stop hooks prompt for this check when scoped publication surfaces change.
- **`software-design`** (`souroldgeezer-design`) — **Build / Extract / Review / Lookup** for code/module/script design: boundaries, responsibilities, dependency direction, state/data ownership, semantic coherence, coupling, evolutionary design, lightweight quality tradeoffs, socio-technical fit, principle/pattern tradeoffs. Delegates frontend app structure → `app-design`, HTTP API/runtime → `api-design`, infra/IaC → `infra-design`, ArchiMate®/OEF + UML®/XMI + dediren drift → `architecture-design`, security → `devsecops-audit`, test-quality → `test-quality-audit`. On-demand support: `references/procedures/project-assimilation.md`, `references/smell-catalog.md`, `references/principles-catalog.md`, `references/pattern-catalog.md`, and extensions for `.NET™`, Java™ (package/module/build/API), Rust® (crate/workspace), TypeScript (package/module/API surface), Bash/zsh shell scripts, and repo-internal Python® tooling — keep extensions thin and pressure-justified, not generic language advice a strong base model already knows. Core smells `SD-*`; extension smells `dotnet.SD-*`, `java.SD-*`, `rust.SD-*`, `typescript.SD-*`, `shell.SD-*`, `python.SD-*`.
- **`app-design`** (`souroldgeezer-design`) — four modes: **Build** (frontend app feature, route, screen, component set, form flow, navigation path, interaction, or browser-facing workflow), **Extract** (existing frontend app baseline), **Review** (route/screen/component architecture, state/data behavior, responsive/accessibility/performance posture, browser runtime behavior), **Lookup** (narrow frontend tradeoff). Mandatory layers: component architecture, route/screen structure, frontend state/data ownership, rendering and browser boundaries, responsive behavior, accessibility, i18n, visual behavior, Core Web Vitals. Existing app work runs `references/procedures/project-assimilation.md` to reuse compliant routes/components/tokens/state and classify broken local UI/runtime patterns as legacy or blocking debt. React extension: component boundaries, Hooks, state/data ownership, rendering purity, hydration, Suspense, effects, forms, browser APIs, finding codes. Next.js extension (loads after React): App / Pages Router route/layout ownership, Server/Client Component boundaries, cache/freshness, navigation, forms, metadata/assets, delegation to `api-design` for API contracts. Blazor™ WebAssembly extension: standalone + Blazor Web App `.Client`, route/layout ownership, component-library reuse, render-mode boundaries, state containers, JS interop, navigation, forms, storage, finding codes. `software-design` supports app-design underneath frontend features; `architecture-design` drift composes through `docs/architecture/<feature>.dediren/` when a paired model exists.
- **`api-design`** (`souroldgeezer-design`) — four modes **Build / Extract / Review / Lookup**. Build produces reference-compliant API contracts and implementation snippets; Extract maps an existing baseline (contract shape, route surface, auth model, error shape, versioning, runtime stack, loaded runtime/data/storage extensions, legacy debt, next smallest move); Review emits per-finding API-quality findings; Lookup answers narrow questions with citations. Non-negotiable baselines: security (OAuth 2.0 / OIDC or Microsoft® Entra ID™ where applicable, managed/workload identities where available, platform secret managers, data-plane RBAC, `disableLocalAuth` on Azure® Cosmos DB™, `allowSharedKeyAccess=false` on Azure® Storage), contract discipline (OpenAPI™ 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 conditional requests), reliability (idempotency on mutations, safe retries, 429 + `Retry-After`, poison / dead-letter), observability (structured logs, W3C® `traceparent`, correlation ID, per-request RU / request-charge / dependency-cost visibility), and honest verification-layer disclosure. §7 checklist items carry verification-layer tags (`[static]` / `[iac]` / `[contract]` / `[runtime]` / `[security-tool]` / `[load]`). Runs a pre-flight (consumer scope / auth model / hosting stack / hosting target / reliability posture / observability target / **architecture pairing**) plus a project-assimilation pass. **Composable extensions load together when the target spans those layers**: `azure-functions-dotnet.md` (isolated worker only — in-process model blocked; retired 2026-11-10; `[BuiltIn]` vs `[AspNetCore]`), `nodejs.md` (`[Hosted]` / `[Serverless]` / `[Adapter]`, package/runtime contract, Node `http` timeouts, body-size limits, AsyncLocalStorage, OpenTelemetry startup, serverless handler shape, reverse proxy, graceful shutdown), `nextjs.md` (hosted Route Handlers, Pages API routes, Server Actions as API/mutation surfaces, Route Segment Config, instrumentation, shared cache / deployment ID, Server Actions encryption key, self-hosted reverse proxy; loads after `nodejs.md`; delegates frontend route/layout/screen/component behavior to `app-design`), `azure-cosmosdb.md` (`[Provisioned]` vs `[Serverless]`; NoSQL API only), `azure-blob-storage.md` (`[SAS-direct]` vs `[API-proxy]`; user-delegation SAS as the canonical escape hatch for §3.12 large payloads). Namespaces orthogonal (`afdotnet.*`, `nodejs.*`, `nextjs.*`, `cosmos.*`, `blob.*`). Extract / Review auto-dispatch to `architecture-design` drift review when a paired package exists at `docs/architecture/<feature>.dediren/`.
- **`infra-design`** (`souroldgeezer-design`) — four modes **Build / Extract / Review / Lookup**. Build produces compact infrastructure briefs for topology, IaC structure, environment strategy, state and identity boundaries, rollout/rollback, operations handoff, validation, and delegations; Extract maps source-readable baselines; Review emits per-finding findings with `ID-*` / extension codes and verification-layer tags; Lookup answers narrow tradeoff questions with citations. Owns IaC, cloud resources, deployment topology, environment promotion, state ownership, identity boundaries, rollout/rollback design, operations handoff, drift-management; delegates API contracts → `api-design`, code/module/script → `software-design`, web frontend/UI → `app-design`, ArchiMate® package/model drift → `architecture-design`, security → `devsecops-audit`, test-quality → `test-quality-audit`. Existing IaC work runs `references/procedures/project-assimilation.md` to reuse compliant IaC/env/state/rollout assets and classify drift / state / migration / topology debt. §7 checklist items carry verification-layer tags (`[static]` / `[iac]` / `[plan]` / `[runtime]` / `[cloud-control-plane]` / `[human]`) so static review doesn't claim cloud runtime, cost, quota, backup, failover, restore, or rollout facts. **Composable extensions**: `azure.md` for Azure®, `terraform.md` for Terraform™, `bicep.md` for Bicep™ on Azure®; Bicep™ on Azure® loads `azure.md` + `bicep.md`, Terraform™ on Azure® loads `azure.md` + `terraform.md`. Core `ID-*`; extensions `azure.ID-*`, `terraform.ID-*`, `bicep.ID-*`.
- **`architecture-design`** (`souroldgeezer-architecture`) — **Build / Extract / Review / Lookup** for ArchiMate® 3.2 and UML® models stored as dediren packages. Canonical source `docs/architecture/<feature>.dediren/`: `project.json` lists actual views, `model.json` carries model/source evidence, render policy/metadata drive SVG proof, `export-policy.json` is optional OEF/XMI export setup. Build / Extract edit package source and policies; Extract must emit source-backed groups for ownership / hosting / trust / environment / dependency boundaries when evidence supports them; source-family lifting covers .NET™, generic Java™ (with framework-specific evidence), Bicep™, GitHub Actions, and process candidates via on-demand procedures. Review assesses source validity, view readability, SVG visual-readiness, optional export evidence, cross-notation links, drift; Lookup answers narrow notation / reverse-lookup questions without mutation. Finding namespaces: `ARCH-M-*`, `ARCH-V-*`, `ARCH-L-*`, `ARCH-R-*`, `ARCH-X-*`, `ARCH-E-*`, `ARCH-Q-*`. ArchiMate diagram kinds: Capability Map, Application Cooperation, Service Realization, Technology Usage, Migration, Motivation, Business Process Cooperation; UML® kinds `uml-class`, `uml-data`, `uml-activity`, `uml-sequence` as design handoff detail. Missing kinds are footer disclosure, not placeholder views. The dediren runtime is resolved from GitHub™ Releases by `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`, cached under `.cache/dediren/releases/`.
- **`architecture-design` runtime evidence** runs through dediren commands: `validate`, notation validation (`validate --plugin generic-graph --profile archimate|uml`), `project` (layout requests + render metadata), `layout`, `validate-layout`, `render`, optional `export`. The release-resolved runtime is Java™-backed, needing Java™ 21+ for runnable CLI checks. It enforces ArchiMate® 3.2 relationship endpoint legality, expects `Node` (not `TechnologyNode`) for technology nodes, supports semantic-backed groups, reports close parallel route channels during layout validation, allows parallel per-view ELK layout with serial rerun as a diagnostic fallback, and supports generated render metadata via `plugins.generic-graph.semantic_profile`. ArchiMate export uses `archimate-oef`; UML® export uses `uml-xmi`. Cross-notation support is optional upward UML® → ArchiMate context via `properties.uml.architecture_context` with `relationship: "elaborates"` — validate referenced ids at the skill level since schema validation permits open properties. Missing downloads, missing Java™ 21+, or error envelopes are reported as `not run` / blocking evidence, never silently replaced. SVG is the default visual proof, but layout-valid / nonblank SVG ≠ visually clean; dense, hub-heavy, label-obscured, route-congested, or mixed-concern diagrams get `ARCH-L-3`, `ARCH-R-3`, or `ARCH-Q-2`. Optional OEF/XMI export is required only when the user asks for compatibility output or supplies downstream validation evidence.
- **Dediren agent usage guide:** after resolving the release bundle, read its `docs/agent-usage.md` before loading schemas when authoring or repairing Dediren package JSON — it's the fast source-JSON authoring, command-handoff, and repair-loop contract.
- **Dediren release update checklist:** when adopting a new upstream release, first confirm the latest GitHub™ release for `tommimarkus/dediren` and its bundle assets. Update only repo-owned version references: `DEDIREN_VERSION_DEFAULT` and usage text in `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`, `EXPECTED_DEDIREN_VERSION` in `tests/architecture_dediren_release_test.py`, and the basic fixture `required_plugins` version. Since the resolver and fixture are shipped references, bump `souroldgeezer-architecture` by patch (unless the release forces a skill-contract change) and sync the Claude manifest, Codex manifest, marketplace entry, README table, and version sync test. Prove with the focused release tests, `bash -n` on the resolver, JSON validation, the optional `DEDIREN_RELEASE_SMOKE=1 uv run python -m unittest tests.architecture_dediren_release_test` lane when network and Java™ 21+ are available, then normal repo validation. Never patch the downloaded or packaged bundle; report runtime defects upstream.
- **Dediren tool ownership:** GitHub™ release bundles and any future checked-in platform bundles are upstream distribution artifacts, not repo-owned source. Don't fix runtime, schema, plugin, helper, or bundle behavior by editing them here. Treat defects as upstream tool issues and disclose under `Dediren tool issues` with release version, command, input summary, envelope/error, expected behavior, and repro evidence. Keep agent-specific issue-filing mechanics out of this canonical guidance.

## Things that are not standard Claude Code

- `skills/<skill>/config.yaml` — skill-internal, not read by the Claude Code runtime. Safe to leave alone when editing plugin metadata.
- `skills/<skill>/extensions/` and `references/` — skill-internal supporting files (docs allow arbitrary files beside `SKILL.md`), not a Claude Code feature. Executable helpers under `references/scripts/` are bundled resources the skill invokes, not runtime-discovered commands.
- `.codex-plugin/plugin.json` — Codex packaging metadata, not read by Claude Code. Keep it synced with the Claude Code manifest and marketplace entry.
- `skills/<skill>/agents/openai.yaml` — Codex per-skill UI metadata / invocation policy, not read by Claude Code.
- `.codex/agents/*.toml` — project-scoped Codex custom agents, not plugin-bundled and not read by Claude Code.
