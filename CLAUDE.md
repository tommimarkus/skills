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

**CLAUDE.md** (audience: Claude Code authoring/editing skills here; first file Claude reads). Keep it lean — orientation + the cross-cutting MUST rules + the skills index and delegation map. Per-skill contract depth lives in each skill's own `SKILL.md`, never duplicated here. Update when:
- a plugin is added/removed/renamed (→ "Directory layout", plugin references, "Published skills index");
- a skill is added/removed/renamed or moved between plugins or `undecided/` (→ "Published skills index" and the delegation map);
- a skill's mode set, output contract, or bundled-reference path changes (→ the skill's `SKILL.md` is the source of truth; touch "Skill architecture" / the delegation map here only when a *cross-skill* convention shifts);
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

For any task that creates, edits, reviews, triages, plans, or fixes a skill-related surface, read [docs/skill-architecture.md](docs/skill-architecture.md) **before** deciding scope or making edits. This covers published plugin skills, matching agents, runtime metadata, bundled references, extensions, deterministic machinery, manifests, marketplace entries, shared repo-internal `internal-skills/**` authoring skills, tool-specific runtime wrappers, and the README / CLAUDE / AGENTS sections describing them.

The standard is the first design input; the report is the repeatable check. Loading the standard only at closeout misses trigger precision, workflow shape, context discipline, runtime parity, and release-hygiene decisions made while changing the code. Before finishing, apply the standard and run `scripts/skill-architecture-report.sh` when available; if it cannot run, record why and what narrower verification was used.

Also read the affected skill's own `SKILL.md` (and its `references/` / `extensions/`) before scoping — that is the source of truth for its modes, owns/delegates, finding namespaces, and extension set. The "Published skills index" only orients you to which skill that is and how it hands off to others.

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

The repo ships a small set of **internal** skills under `internal-skills/` — shared repo-scoped workflows, deliberately *not* bundled with the published `souroldgeezer-*` plugins. Keep shared workflow text, references, evals, fixtures, and helper material there. Tool-specific directories contain only tool-specific entrypoints: Claude Code auto-discovery wrappers live under `.claude/skills/<name>/SKILL.md`, and Codex project-scoped wrappers live under `.codex/agents/<name>.toml`. Every internal skill must have both wrappers pointing back to `internal-skills/<name>/SKILL.md`. They encode how *we* author this repo, not capabilities shipped downstream.

`ip-hygiene` formerly lived here but is now a public skill in `souroldgeezer-audit` at [souroldgeezer-audit/skills/ip-hygiene/SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md).

Current internal skills:

- **`github-issue-lifecycle`** at [internal-skills/github-issue-lifecycle/SKILL.md](internal-skills/github-issue-lifecycle/SKILL.md) — repo-local overlay for explicit GitHub™ issue lifecycle requests here. Composes the public `issue-ops` skill, the GitHub™ provider extension, and this repo's defaults (`ip-hygiene`, `.worktrees/**`, direct-main handling, skill-architecture verification, published-surface sync, lifecycle status, cleanup). Claude Code has a thin wrapper at [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md); Codex has a thin wrapper at [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml).
- **`lesson-capture`** at [internal-skills/lesson-capture/SKILL.md](internal-skills/lesson-capture/SKILL.md) — invoked by the `scripts/agent-hooks/stop-lesson-capture.sh` Stop hook, registered in both `.claude/settings.json` and `.codex/hooks.json`. The hook fires/prompts when a skill-authoring surface changes and asks `lesson-capture` to judge whether the session holds a reusable lesson; transcript correction phrases are hints, not the gate. Distills one generalizable, Layer-2 (developing-the-skills) lesson and stages it to the gitignored pending ledger (`scripts/lessons_ledger.py`, `.cache/lessons/pending.jsonl`) for later review. First step of the lesson-loop self-improvement system; capture only — graduation to committed rules is a separate flow. Claude Code has a thin wrapper at [.claude/skills/lesson-capture/SKILL.md](.claude/skills/lesson-capture/SKILL.md); Codex has a thin wrapper at [.codex/agents/lesson-capture.toml](.codex/agents/lesson-capture.toml).
- **`lessons`** at [internal-skills/lessons/SKILL.md](internal-skills/lessons/SKILL.md) — the `/lessons` review surface for the lesson loop. On `main` only, lists pending captured candidates (`scripts/lessons_ledger.py list --pending`), and for each the user approves/edits/rejects; approved `prose`/`policy` lessons are placed in their docs, approved `deterministic` lessons become a `SAC-T#####` fixture case only when the engine already detects the smell (else recorded as engine work). Completes the capture → review → graduate loop. Every graduation passes a deterministic secret scan (`scripts/lessons_secret_scan.py`, the `DSO-POS-9` control); the `auto-approved` fast-path is gated by `auto_approve_eligible()` and defaults to denying all change-classes until a template-synthesizable fixture path exists (unattended auto-commit is parked). Claude Code has a thin wrapper at [.claude/skills/lessons/SKILL.md](.claude/skills/lessons/SKILL.md); Codex has a thin wrapper at [.codex/agents/lessons.toml](.codex/agents/lessons.toml).

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
internal-skills/<name>/SKILL.md        ← shared repo-internal skill source of truth
.claude/skills/<name>/SKILL.md         ← Claude Code wrappers for repo-internal skills
.codex/agents/*.toml                   ← project-scoped Codex wrappers for published and repo-internal skills
.claude-plugin/marketplace.json        ← shared Claude Code + Codex marketplace manifest
souroldgeezer-ops/          ← published operations plugin (issue-ops, pr-ops)
souroldgeezer-policy/       ← published passive policy plugin (git-workflow-policy, release-policy)
souroldgeezer-audit/        ← published audit plugin (devsecops-audit, test-quality-audit, ip-hygiene, lean-audit)
  docs/audit-reference/     ← shared audit craft core (audit-craft.md, materiality.md, sampling-projection.md)
souroldgeezer-design/       ← published design plugin (software-design, app-design, api-design, infra-design)
souroldgeezer-architecture/ ← published architecture plugin (architecture-design)
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
- `souroldgeezer-audit/docs/audit-reference/audit-craft.md` — shared audit discipline + output contracts (independence disclosure, assurance level, consequence field, worklist prioritisation)
- `souroldgeezer-audit/docs/audit-reference/materiality.md` — risk-tier procedure: materiality = max(signal strength, declared tier); orthogonal to smell severity, combined at the worklist
- `souroldgeezer-audit/docs/audit-reference/sampling-projection.md` — sampling and projection procedure for Deep / in-depth modes when full enumeration exceeds budget
- `souroldgeezer-design/docs/software-reference/software-design.md` — software-design playbook
- `souroldgeezer-design/docs/app-reference/app-design.md` — app-design playbook
- `souroldgeezer-design/docs/api-reference/api-design.md` — api-design playbook
- `souroldgeezer-design/docs/infra-reference/infra-design.md` — infra-design playbook
- `souroldgeezer-architecture/docs/architecture-reference/architecture.md` — architecture-design playbook (ArchiMate® 3.2, with UML® notation overlays under the skill references)

Migration note: `architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.

When moving a skill out of `undecided/` into a plugin (or vice versa), **also move its matching subagent file** in `agents/<name>.md`. Skill and subagent are paired by identical name.

## Plugin registration

Adding a new plugin:
1. `<plugin-name>/.claude-plugin/plugin.json` (required `name`, `version`, `description`; `author: {name, email}` and `license: MIT` defaults from memory; start at the current CalVer stamp `YYYY.0M.0`, e.g. `2026.06.0`).
2. `<plugin-name>/.codex-plugin/plugin.json` with the same `name` / `version` / `description` / `author` / `license`, plus `"skills": "./skills/"` and Codex `interface` metadata (`interface.defaultPrompt` ≤ three entries; omit `apps` / `mcpServers` unless the plugin ships them).
3. For each bundled skill, `skills/<skill>/agents/openai.yaml` with Codex UI metadata and invocation policy.
4. Add to `.claude-plugin/marketplace.json` under `plugins[]` (`name`, `source: ./<plugin-name>`, `version`, `description`) — this one marketplace is shared by both runtimes.
5. `name` / `description` / `version` must stay in sync across both manifests and `marketplace.json#plugins[]` — every re-stamp updates all three in one commit (the integration commit on `main` for worktree work; see "Plugin versioning (MUST)").

## Plugin versioning (MUST)

Plugins follow **CalVer** in the format `YYYY.0M.MICRO` (four-digit year, zero-padded month, then a within-month micro counter) — e.g. `2026.06.0`. This mirrors the Dediren upstream scheme this repo already adopts. A stamp always pairs with the content change that required it, and both plugin manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) and the `marketplace.json#plugins[]` entry move together as one stamp. **Where that stamp lands depends on where the work happens:**

- **Work done directly on `main`** (the writable subset — `CLAUDE.md`, repo tooling): stamp in the **same commit** as the content change. Never defer.
- **Work done in a worktree / feature branch** (the normal case — the published plugin tree is read-only in the primary checkout, so all plugin-content edits happen in a worktree): the feature branch carries content **only** and **MUST NOT touch any version cell**. The stamp is applied **at integration, directly on `main`, after the branch merges**, computed against `main`'s actual state then. The within-month micro counter is a main-line sequence number; assigning it at integration (not against a stale worktree base) is what keeps it correct and conflict-free when several worktrees merge.

Before integrating a worktree, run `uv run python scripts/version_stamp.py guard` (compares the branch against its merge-base with `main`); it fails if the branch stamped a version cell. At integration, get the correct next stamp with `uv run python scripts/version_stamp.py compute --plugin <name>` and apply it to all four cells in the integration commit.

**Stamp mechanics:**
- Compute the stamp from the calendar month of the commit that lands it (the integration commit on `main` for worktree work). If the plugin's current version on `main` is from an **earlier** month (or a pre-CalVer semver), reset to `YYYY.0M.0`. If it is **already** in the current month, increment the micro counter (`2026.06.0` → `2026.06.1`). `uv run python scripts/version_stamp.py compute --plugin <name>` does exactly this against `main`'s current version.
- The number encodes *when*, not *how big*. CalVer is monotonic across the semver→CalVer switch (`2026.06.0` sorts above the old `2.8.1`), so installed-plugin update checks pick up the change.

**Mandatory stamp** when a change lands that touches, under a `<plugin>/`: `skills/<skill>/SKILL.md`, `agents/<name>.md`, `docs/<kind>-reference/**`, `skills/<skill>/references/**`, `skills/<skill>/extensions/**`; or adds/removes/renames a top-level artefact (skill, extension, agent, reference file, reference section, mode, smell namespace). One stamp per plugin per landing regardless of how many of its files changed; for worktree work the landing point is the integration commit on `main` (see "Where that stamp lands"), not the feature-branch commit.

**Change significance** is now decoupled from the version number but still classified, because it drives the IP-hygiene gate and the sync obligations below:
- **Breaking** — something a downstream consumer relied on breaks. E.g. a skill removed/renamed; a reference file moved/renamed; an output contract changes (smell-code prefix renamed, canonical path changed, frontmatter field removed); a mode removed; `plugin.json#name` changes.
- **Additive** — new capability, no regression. E.g. a new skill, extension, mode, or `references/procedures/` entry; a new reference section shaping new output (new `AD-L*` namespace, new `§6.4a`); a new SKILL.md frontmatter field downstream tooling may read.
- **Cosmetic** — prose-only or no-op behavioural. E.g. rubric/reference tightening, typos, clarifying rewrites, description language that doesn't change behaviour.

**Breaking/additive IP hygiene gate.** Every breaking or additive change requires an in-depth `ip-hygiene` run before finishing, scoped to the whole changed plugin surface (added/moved/renamed/removed/contract-shaping skills, agents, references, extensions, deterministic machinery, manifests, marketplace entries, public repo guidance); load every hit bucket from the workflow and report its normal output contract in closeout. Cosmetic changes use the normal scoped IP hygiene triage.

**No stamp needed:** fixing broken links, whitespace, `docs/<kind>-reference/` cross-references between sections that already existed, repo-level `README.md` / `CLAUDE.md` edits outside the plugin tree, or packaging metadata that doesn't alter shipped behaviour or need pickup by installed-plugin update checks.

**Sibling-file sync** (one commit — the stamp's landing commit; the integration commit on `main` for worktree work):
- `.claude-plugin/plugin.json#version`, `.codex-plugin/plugin.json#version`, `marketplace.json#plugins[].version`, and the plugin's `README.md` version-table cell — always all four; the README cell must equal the manifest version per plugin.
- the three `#description` fields — when the change alters the plugin's surface (new skill, new mode).
- `description:` frontmatter in any affected `SKILL.md` and matching `agents/<name>.md` — when what the skill does changes (required by the subagent pattern; see "Subagents").
- `README.md` and `CLAUDE.md` — per the currency rule above; one commit.

**Don't stamp without content change.** A stamp must pair with content — but for worktree work that content is the *just-integrated* merge, so the integration stamp commit on `main` is expected and is **not** a bare increment. A genuinely bare increment — a stamp with no corresponding content (in the same commit for direct-`main` work, or in the just-merged branch for integration work) — remains a smell (earlier commits skipped stamps); carry the catch-up in the next content or integration commit. Multiple content commits within the same month at one stamp are fine to leave; the next stamp increments the micro counter.

**Dediren upstream release adoption** (the one architecture-specific version procedure, documented nowhere else): when adopting a new `tommimarkus/dediren` release, bump only repo-owned refs — `DEDIREN_VERSION_DEFAULT` in `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`, `EXPECTED_DEDIREN_VERSION` in `tests/architecture_dediren_release_test.py`, and the basic fixture's `required_plugins` version. Before classifying the bump or re-stamping, run the gated `DEDIREN_RELEASE_SMOKE=1` release suite (full validate→layout→render→export pipeline against the new bundle): a version-string change can hide a runtime-contract change (e.g. the render-envelope schema version, `data.content`→`data.artifacts`) that requires test/doc updates and makes the bump non-cosmetic. Also run a feature-parity step before finishing — diff the new bundle against the current pin (agent-usage guide, plugin manifests, schemas, bundled fixtures, commands, semantic profiles) and add or update architecture-design skill support for any new capability, not only bump refs and sync; record the parity finding (new features supported, or "maintenance-only, no contract change") in closeout. Then re-stamp `souroldgeezer-architecture` (cosmetic only when the smoke suite and parity diff confirm no skill-contract change) and sync manifests / marketplace / README / version-sync test — the re-stamp follows "Where that stamp lands": deferred to the `main` integration commit when the adoption work is in a worktree. Never patch the downloaded bundle; report runtime defects upstream. Tool-ownership and runtime-evidence rules live in the architecture-design `SKILL.md` and `docs/architecture-reference/architecture.md`.

## Skill architecture (shared pattern across skills)

Skills here follow a recurring shape. Understand it before editing any SKILL.md:

- **Reference vs workflow separation.** SKILL.md is a *workflow* for applying a bundled reference; the reference prose lives under `<plugin>/docs/<kind>-reference/*.md` (rubric for audits, playbook for design — see "Directory layout"). Relative paths like `../../docs/app-reference/app-design.md` resolve from a skill dir. SKILL.md **cites** reference sections and codes, never duplicates prose.
- **Mode dispatch.** Each SKILL.md lists its modes. Audit skills (`devsecops-audit`, `test-quality-audit`): **Quick** (single file / PR diff, per-finding output only) vs **Deep** (whole-repo, full sectioned rollup, may use MCP probes). Design skills: **Build / Extract / Review / Lookup** — Extract is first-class for existing-code, frontend-app, API, and IaC baselines and code-to-diagram lifting. Ambiguous request → the skill asks.
- **Output cites codes / sections, not prose.** Audit reports cite smell codes (`DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`); design output cites reference sections (`§3.11`, `§5.8`) plus WCAG SC numbers (`SC 1.4.10`, `SC 2.5.8`). Never duplicate reference prose.
- **Shared audit craft core.** All four audit skills (`devsecops-audit`, `test-quality-audit`, `ip-hygiene`, `lean-audit`) cite `docs/audit-reference/audit-craft.md` for the canonical output contracts: independence disclosure, assurance level, SUT risk tier, Consequence finding field, and worklist prioritisation. `ip-hygiene` conforms by named principle (§2/§3/§5) to preserve its triage / in-depth mode shape; `lean-audit` likewise conforms by principle with one adaptive path (no Quick/Deep), deriving its assurance level from the scanned scope. Materiality (risk tier) is orthogonal to smell severity; they combine at the worklist via a priority grid (P0–P3) keyed on both axes — neither overrides the other.
- **Extensions are on-demand packs** in `skills/<skill>/extensions/*.md`, loaded from detected target / provider. Audit and design extensions are per-stack; `issue-ops` / `pr-ops` use provider extensions; `git-workflow-policy` / `release-policy` start provider-agnostic, adding extensions later only when initialized options can't stay compact. For audits, extensions **ADD** namespaced smells (`<ext>.HC-N` / `.LC-N` / `.POS-N`) or **CARVE OUT** core smells for idiomatic framework patterns; for design, they also add stack-specific primitives, patterns, and project-assimilation rules; for operations, they add provider lifecycle mechanics; policy skills prefer declarative initialization options. Extensions **never override** core rules. Each skill's extension-authoring convention lives in `extensions/README.md` or a `references/procedures/*extension*.md` loaded from SKILL.md — follow its required-sections list exactly. Multi-extension composition order is summarized in "Published skills index"; each skill's own `extensions/README.md` and SKILL.md carry the authoritative per-stack composition and the orthogonal finding namespaces (so findings never collide).
- **Supporting files live under `references/`** (audit skills, and design skills when needed): `smell-catalog.md` (compact code index), `procedures/*.md` (reusable sub-procedures the workflow steps into), `scripts/*.sh` (allowed when a deterministic executable gate ships with the skill), `evals/*.jsonl` + `source-grounding.md` (behavioral evidence for trigger / workflow / source-grounding / high-risk-gate evals). `software-design`, `app-design`, `api-design`, `infra-design` use skill-local `references/procedures/project-assimilation.md` for existing-codebase discovery, reuse/debt classification, and migration disclosure. `app-design` keeps stack rules under `extensions/`; `software-design` uses a compact smell catalog + evidence; `infra-design` keeps evidence/source-grounding under `references/` while Azure® / Terraform™ / Bicep™ rules live under `extensions/`; `architecture-design` uses `references/` for notation references, finding catalog, package workflow procedures, source-lifting rules, evals, source grounding, and the dediren package fixture.
- **Cross-skill coupling is via filesystem convention** (design skills). `architecture-design` owns `docs/architecture/<feature>.dediren/`; `app-design`, `api-design`, `infra-design` check that path when a paired model may need drift review. Siblings don't reach into the architecture-design surface beyond this path.
- **Project assimilation is one-way** (design skills). Assimilate the *project* to the *reference*, not vice versa. New code is always reference-compliant; non-compliant existing infrastructure is reused only when substantively compliant, else flagged as legacy debt. Load skill-local `project-assimilation.md` when existing source, app structure, API wiring, IaC, diffs, or runtime/config evidence is in scope. Footer shape: `Project assimilation:` with `Reused`, `Legacy debt`, `Migrations performed`.
- **Output footers disclose state.** Every report / build output ends with a footer listing loaded extensions, MCP availability, cost stance (if applicable), reference path, and (design skills) project-assimilation summary. Don't remove them — they're how users audit the auditor / verify the builder.

## Subagents

Every skill has a matching Claude Code subagent at `<plugin>/agents/<skill-name>.md` — a thin one-shot wrapper that invokes the skill via the `Skill` tool, follows its instructions, and presents results in the skill's required shape. Frontmatter: `name`, `description` (mirror the skill's for discoverability), `tools`, `model`.

Codex doesn't consume these plugin-root `agents/*.md` files; its installable-plugin parity is the bundled skills plus `skills/<skill>/agents/openai.yaml`, with project-scoped wrappers in `.codex/agents/*.toml` that point back to the matching skill and don't duplicate reference prose. When editing a skill's invocation contract (output format, required footer fields), update all three together: `SKILL.md`, the Claude Code subagent, and the Codex wrapper / `openai.yaml`.

## Published skills index

One row per published skill. **Each skill's own `SKILL.md` is its binding contract** — modes, owns/delegates, finding namespaces, extension set — so read it before creating, editing, reviewing, or planning that skill; this table and the delegation map below are orientation only, deliberately not a second copy of those contracts. Internal skills are in § "Repo-internal skills".

| Skill | Plugin | Purpose |
|---|---|---|
| `issue-ops` | `souroldgeezer-ops` | Explicit issue / work-item operations; tracker-agnostic core + GitHub™ / GitLab™ provider extensions |
| `pr-ops` | `souroldgeezer-ops` | Explicit PR/MR operations and prepared branches; provider-agnostic core + GitHub™ / GitLab™ extensions |
| `git-workflow-policy` | `souroldgeezer-policy` | Passive developer git workflow policy; standing enforcement once initialized in target-repo guidance |
| `release-policy` | `souroldgeezer-policy` | Passive distribution policy (versions, changelog, tags, publication); standing enforcement once initialized |
| `devsecops-audit` | `souroldgeezer-audit` | Security audit for CI/CD, IaC, containers, releases, supply chain; cost stance via `config.yaml` |
| `test-quality-audit` | `souroldgeezer-audit` | Test-quality audit; dispatches unit / integration / E2E rubric per detected test type and stack |
| `ip-hygiene` | `souroldgeezer-audit` | Copyright / trademark / licence / bundled-asset hygiene for publication surfaces |
| `lean-audit` | `souroldgeezer-audit` | Duplication & waste (Lean *muda*) audit of prose / skill surfaces; bundled deterministic engine + judgment layer; read-only |
| `software-design` | `souroldgeezer-design` | Code/module/script design; core `SD-*` + per-language extensions |
| `app-design` | `souroldgeezer-design` | Frontend app design (React / Next.js / Blazor™ WASM); WCAG 2.2 / i18n / Core Web Vitals baselines |
| `api-design` | `souroldgeezer-design` | HTTP API design; OpenAPI™ 3.1 / problem+json / security / reliability + composable runtime extensions |
| `infra-design` | `souroldgeezer-design` | Infrastructure / IaC design; core `ID-*` + Azure® / Terraform™ / Bicep™ extensions |
| `architecture-design` | `souroldgeezer-architecture` | ArchiMate® 3.2 + UML® dediren packages; SVG / OEF / XMI evidence, drift, reverse lookup |

Design and audit skills share the Build / Extract / Review / Lookup (design) and Quick / Deep (audit) mode dispatch from § "Skill architecture (shared pattern across skills)".

**Delegation map** (the cross-skill handoff view no single `SKILL.md` gives):
- `software-design` → `app-design` (frontend), `api-design` (HTTP), `infra-design` (IaC), `architecture-design` (ArchiMate®/UML® drift), `devsecops-audit` (security), `test-quality-audit` (tests).
- `app-design` / `api-design` / `infra-design` → `architecture-design` drift review via the paired package at `docs/architecture/<feature>.dediren/`; `app-design` ↔ `api-design` at the frontend/API boundary.
- `git-workflow-policy` → `pr-ops`, `issue-ops`, `release-policy`; `release-policy` applies `git-workflow-policy` preflight then → `pr-ops`; `issue-ops` ↔ `pr-ops` handoff.
- `lean-audit` → `devsecops-audit` (security), `test-quality-audit` (tests), `ip-hygiene` (copyright / marks / licence), the design skills (code / structure); sibling skills may hand duplication / waste assessment to `lean-audit`.

**Extension composition order** (load in order when the target spans layers): app `react.md` → `nextjs.md` (Blazor™ WASM is standalone); api picks one base — `azure-functions-dotnet.md` (Azure® Functions™ .NET) *or* `nodejs.md` (hosted Node, then `nextjs.md` for Next.js) — plus `azure-cosmosdb.md` / `azure-blob-storage.md` data/storage extensions as the stack spans; infra `azure.md` + (`bicep.md` | `terraform.md`); test-quality `nodejs-core.md` → `nextjs-core.md` (Next.js is a strict superset of Node.js).

## Things that are not standard Claude Code

- `skills/<skill>/config.yaml` — skill-internal, not read by the Claude Code runtime. Safe to leave alone when editing plugin metadata.
- `skills/<skill>/extensions/` and `references/` — skill-internal supporting files (docs allow arbitrary files beside `SKILL.md`), not a Claude Code feature. Executable helpers under `references/scripts/` are bundled resources the skill invokes, not runtime-discovered commands.
- `.codex-plugin/plugin.json` — Codex packaging metadata, not read by Claude Code. Keep it synced with the Claude Code manifest and marketplace entry.
- `skills/<skill>/agents/openai.yaml` — Codex per-skill UI metadata / invocation policy, not read by Claude Code.
- `.codex/agents/*.toml` — project-scoped Codex custom agents, not plugin-bundled and not read by Claude Code.
