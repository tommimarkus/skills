# AGENTS.md

This repository is a cross-runtime plugin marketplace for Claude Code and
Codex, with a native GitHub™ Copilot CLI adapter where a plugin declares one.
It publishes the same skills through runtime-specific packaging; the shared
skill workflow under each plugin's `skills/` directory is the source of truth.

## Start here

Before planning, editing, reviewing, or validating a skill, manifest,
marketplace, agent wrapper, hook, bundled reference, extension, or helper, read
[`docs/skill-architecture.md`](docs/skill-architecture.md). Read the affected
skill's own `SKILL.md` and only the references or extensions its load map selects.

Keep this file, `CLAUDE.md`, and `README.md` current when repository structure,
runtime support, install commands, validation, or a public skill contract
changes. `AGENTS.md` owns Codex-facing repository guidance; `CLAUDE.md` remains
the self-contained Claude Code contract. Cross-runtime rules must agree without
making either runtime load the other's file first.

## Repository shape

- `.agents/plugins/marketplace.json`: native Codex marketplace.
- `.claude-plugin/marketplace.json`: Claude Code marketplace.
- `<plugin>/.codex-plugin/plugin.json`: native Codex manifest.
- `<plugin>/mcp/codex.mcp.json`: Codex MCP adapter when the Codex manifest
  declares `mcpServers`.
- `<plugin>/plugin.json`: native Copilot manifest when that plugin supports
  Copilot CLI directly; its MCP adapter lives at `<plugin>/mcp/copilot.mcp.json`.
- `<plugin>/.claude-plugin/plugin.json`: Claude manifest.
- `<plugin>/skills/<skill>/SKILL.md`: shared runtime-neutral workflow.
- `<plugin>/skills/<skill>/extensions/`: on-demand supporting packs; a stack
  core may own nested mode lanes such as `build.md` and `review.md` when the
  skill's load map declares them.
- `<plugin>/agents/<skill>.md`: Claude-only subagent wrapper.
- `.agents/skills/<name>/SKILL.md`: Codex wrapper for a repo-internal skill.
- `.claude/skills/<name>/SKILL.md`: Claude wrapper for a repo-internal skill.
- `internal-skills/<name>/SKILL.md`: source of truth for repo-internal skills.
- `.codex/hooks.json` and `.claude/settings.json`: runtime hook registration;
  both invoke shared scripts under `scripts/agent-hooks/`.

Do not copy a published skill to make it runtime-specific. Put portable
workflow in `skills/**`; isolate host metadata, hook configuration, MCP launch
variables, and UI presentation in the host adapter.

## Required conventions

- `git-workflow-policy: feature branches, persistent repo-local worktrees,
  clean worktree, no direct main`.
- Create every task worktree under the primary checkout's gitignored,
  persistent `.worktrees/<task-name>/` directory. Never place a Git worktree or uncommitted
  task work under `/tmp`, `$TMPDIR`, `/var/tmp`, a tmpfs/ramdisk, or another
  ephemeral location, even for a short-lived task. Gitignored does not mean
  disposable. Run worktree creation from the primary checkout; if its
  `.worktrees/` is unavailable, stop and ask before choosing a different
  persistent location.
- Use `jq` for JSON and Mike Farah `yq` for YAML frontmatter, TOML, and XML.
- Use `rg` or `rg --files` for repository search.
- Preserve the existing Python 3.11 floor and repo-local `uv` configuration.
- Do not force-add ignored files. Before a commit, run
  `git ls-files -ci --exclude-standard`; the result must be empty unless the
  user explicitly approved an exact tracked exception.
- Run repository-wide scanners from the clean task worktree itself, not the
  primary checkout; nested worktrees otherwise pollute primary enumeration.
- Shared skill commands must preserve documented Claude substitutions and add a
  Codex source-path form beside them. Never replace `${CLAUDE_SKILL_DIR}` or
  `${CLAUDE_PLUGIN_ROOT}` with a generic placeholder as the only instruction.
- Codex hook commands use `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`. Codex plugin MCP
  fields are literal: use plugin-relative `cwd` / paths where changing directory
  is correct, or a tested source-discovery bootstrap when the server must preserve
  the caller's workspace. Claude MCP and hook commands use
  `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}`.
- Copilot plugin MCP commands use `${PLUGIN_ROOT}` and writable plugin data uses
  `${COPILOT_PLUGIN_DATA}`. Keep a separate Copilot MCP file; never let Copilot
  fall through to the Codex bootstrap.

## Runtime parity

Every published plugin appears in both marketplaces and has both manifests.
Keep plugin sets, ordering, names, descriptions, and semantic versions aligned.
The Claude manifest and README preserve CalVer `YYYY.0M.MICRO`; Codex derives
strict SemVer `YYYY.M.MICRO` from that authority. Marketplace entries never
carry a `version` field.

When a plugin has a root Copilot `plugin.json`, keep its name, description,
skills path, and strict-SemVer version aligned with the Codex manifest.

Each public `SKILL.md` keeps its matching Claude subagent. Codex discovers the
same skill through the Codex manifest's `skills` path; do not create a parallel
Codex workflow. Each `internal-skills/<name>` entry has thin wrappers under both
`.agents/skills/<name>` and `.claude/skills/<name>`.

When a shared workflow needs host behavior, state the capability and give a
runtime mapping with a safe fallback. For example, Claude planning retains
`EnterPlanMode` / `ExitPlanMode`; Codex uses Plan mode when exposed and otherwise
emits a proposed plan for explicit approval.

### Planning-policy execution contract (Codex)

The shared `planning-policy` contract is runtime-neutral. Every executable leaf
has decision-complete, stable fields: IDs/dependencies, task/boundary, named
read/write sets, settled decisions, size, portable tier, worktree owner, one
acceptance command, bounded return contract, stop conditions, and stable work
unit ID. A missing load-bearing field stops as `blocked:missing_input`; do not
search for or invent it. Work units are weighted once from their original size
(`small=1`, `medium=2`, `large=3`) and require `standard_ready_ratio >= 0.60`;
only an explicitly user-approved, recorded analytical-heavy exception waives
that gate. Route an initial inspection to at most one owning audit only when
its bounded question and evidence surface remain unresolved by targeted
inspection or focused tests; ordinary design is not an audit route.

For an approved plan with at least two delegated steps, only the parent may
activate the durable ledger at `<git-common-dir>/planning-policy/ledgers/<plan-id>/`.
Use its bounded checkpoint and lifecycle/retry returns, never raw logs. The
parent owns integration and end-to-end verification; a delegated return covers
only its assigned drafting and acceptance check.

Codex maps the portable tiers exactly: `mechanical` → `gpt-5.6-luna`/`low`,
`standard` → `gpt-5.6-terra`/`medium`, `analytical` → `gpt-5.6-sol`/`high`, and
`deep` → `gpt-5.6-sol`/`xhigh`. If the selected mapping is unavailable, return
`blocked:model_unavailable` with the requested tier/model/effort and availability
evidence; never silently downgrade. The opt-in fresh-context evidence command is
`uv run python scripts/planning_policy_forward_eval.py --harness both --output-dir /secure/path --execute`;
it writes bounded comparison summaries only.

## Version and release policy

The Claude manifest and README use CalVer `YYYY.0M.MICRO` as the release
authority. Codex and any native Copilot manifest mirror it as strict SemVer
`YYYY.M.MICRO`.

Feature branches and worktrees carry content only. Do not increment existing
version cells there. At integration on `main`, run:

```text
uv run python scripts/version_stamp.py guard
uv run python scripts/version_stamp.py compute --plugin <name>
```

Then apply the padded computed stamp to the Claude manifest and matching README
cell, and its normalized derivative to the Codex and native Copilot manifests,
in the integration commit. New manifests added by a feature branch may
carry the existing release's SemVer-normalized value; that is packaging content,
not a release increment.

Breaking or additive public-surface work requires the repository's in-depth
`ip-hygiene` gate. Cosmetic changes use scoped triage.

## Validation

Run from a clean worktree at repository root:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
uv run python -m unittest discover -s tests -p '*_test.py'
scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .
git diff --check
```

Also validate every Codex plugin with the current first-party plugin validator
when it is available, and run `claude plugin validate --strict` through the
repository report path when the Claude CLI is installed. A test run that
collects zero tests is a failed gate.

The host smoke must keep both safety flags. It uses temporary `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` state without
replacing `HOME`, verifies installed plugin, skill, agent, and Dediren MCP
surfaces, and fingerprints the normal host plugin/config control planes before
and after. Dediren itself is host-managed: the smoke uses `dediren` from `PATH`
or `DEDIREN_COMMAND`, never a plugin-owned pin. Absence of a standalone Codex
validator is a reported skip, not a fabricated pass.

## Documentation and ownership

Update `README.md` when install commands, plugin names, skills, public behavior,
or local validation changes. Update `docs/release-checklist.md` and
`docs/maintenance-procedures.md` when packaging or version mechanics change.
Keep `.github/CODEOWNERS` on executable hook configuration and hook scripts.

No checked-in `.codex/config.toml` should choose a model, approval policy, or
sandbox profile for contributors unless the repository genuinely requires that
setting. Repo-local hooks are enough for this repository and remain subject to
Codex trust review.
