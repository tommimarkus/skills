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
- `<plugin>/plugin.json` + `<plugin>/mcp.json`: Agent Plugins 1.0.0 manifest and
  its MCP configuration — the current Codex lane, and the only one that
  interpolates `${PLUGIN_DATA}` in MCP config. The same root `plugin.json` is the
  native Copilot manifest when that plugin supports Copilot CLI directly; its own
  MCP adapter lives at `<plugin>/mcp/copilot.mcp.json`.
- `<plugin>/.codex-plugin/plugin.json`: legacy Codex manifest, retained as the
  fallback lane.
- `<plugin>/mcp/codex.mcp.json`: legacy Codex MCP adapter when that manifest
  declares `mcpServers`.
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

### Dediren MCP adapter contract

The architecture plugin's Dediren configuration is host-specific, while its
shared launcher/router has no harness detection. The maintained host adapters
are Claude Code, Codex, and Copilot CLI; the router only launches a local
stdio Dediren process for the explicit `workspaceRoot` supplied to each tool
call. Dediren itself is provisioned by the plugin: on first use the launcher
installs the pinned, checksum-verified release (pin `2026.08.9`, support floor
`2026.07.28`, overridable by a CalVer `DEDIREN_VERSION` at or above that floor)
into the host's own per-plugin writable data directory. That directory resolves
from `DEDIREN_HOME` (which must be absolute), else `CLAUDE_PLUGIN_DATA`,
`COPILOT_PLUGIN_DATA`, or `PLUGIN_DATA` with `/dediren` appended; there is no
invented fallback, so a host offering none exits 78 naming `DEDIREN_HOME`.
Executables resolve in order: an explicit `DEDIREN_COMMAND` (honoured without a
floor probe — the deliberate lane for pinning one executable for controlled
validation), the managed install, a host `dediren` on `PATH` that reports at or
above the floor, the legacy verified-release-cache migration lane, then
provisioning the pin. Java stays host-managed and is never downloaded: the
release ships jars with no bundled JRE, so Java 21+ is a host prerequisite. The
bundled procedure at
[`souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md`](souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md)
is the single place that documents what provisioning does, how to override it,
how to run air-gapped, and how to diagnose a failure.

Dediren 2026.08.3 adds `export-result.schema.v2` assurance to direct UML/XMI
exports. Native package-build results do not surface it, so shared guidance
preserves the artifact/source and diagnostic evidence path with an explicit
assurance limit.

Dediren 2026.08.4 moves online export-schema fetching into a bounded Java HTTP
client, so exports no longer require `curl`; the plugin launcher may still use
`curl` or `wget` as a fallback for release downloads. Its additive inline import
and negotiated MCP image fields flow through the live discovered schema and
unchanged tool result rather than a runtime-specific adapter fork.

Dediren 2026.08.6 adds the non-failing
`DEDIREN_RENDER_EDGE_LABEL_OCCLUDED` warning when the renderer cannot place an
edge label without occluding content. A render carrying it still returns its
SVG, but architecture review maps the affected view to `ARCH-R-3` until the
label is made visually clear or the limitation is disclosed.

Dediren 2026.08.7 adds a draw.io® import lane: `dediren_import` accepts a third
plugin id, `drawio`, beside `mermaid` and `dot`. An imported draw.io file always
lands as `generic-graph` (`generic.node` / `generic.link`) rather than a promoted
model, because draw.io carries relationship semantics only as arrowhead
decoration, and the non-failing `DEDIREN_DRAWIO_HINT_IGNORED` warning names the
geometry and presentation keys ELK re-lays out. The release's draw.io export
engine is reachable from no build driver, so the tool set stays at eight and the
skill's trigger boundary still excludes diagrams the user wants kept in that
format.

Dediren 2026.08.8 adds an `ascii` render engine — box-drawn text diagrams from
the same layout stages, Unicode by default with a plain-ASCII `text.charset`
option — reachable only from the standalone `render` stage and a fourth
`dediren_import` output mode, `text`, which returns an inline text diagram as a
second text content beside the imported envelope. No build driver selects it,
so the tool set stays at eight and SVG remains the evidence of record. Render
policies move to `render-policy.schema.v4`: the runtime refuses a v3 policy
with a single-operation `set_version` migration diagnostic, so checked-in
packages migrate that one field. Dediren 2026.08.9 converges render-result
`artifact_kind` onto the media-suffix form (v7): `svg` → `svg+xml` and text →
`ascii+text`, breaking for consumers reading that field. The repo's fixture
compatibility baseline moves to 2026.08.9; the support floor stays 2026.07.28.

| Host | Root/path interpolation | Process cwd | Environment overrides | Host timeout unit |
|---|---|---|---|---|
| Claude Code | `${CLAUDE_PLUGIN_ROOT}` in the inline manifest command; `DEDIREN_HOME` set explicitly from `${CLAUDE_PLUGIN_DATA}` | Host launch cwd; router sets the upstream child cwd to `workspaceRoot` | Inherit `DEDIREN_COMMAND`, `DEDIREN_MCP_STARTUP_TIMEOUT_SEC`, `DEDIREN_MCP_REQUEST_TIMEOUT_SEC` | Router values are seconds |
| Codex | Agent Plugins root `plugin.json` + `mcp.json`, declaring only `type` / `command`; Codex exports `PLUGIN_ROOT` / `PLUGIN_DATA` into the child. The retained legacy `.codex-plugin` + `mcp/codex.mcp.json` lane is literal (plugin-relative command, `cwd: "."`) and receives no plugin data root | Plugin root for the launcher; router sets the upstream child cwd to `workspaceRoot` | Same three `DEDIREN_*` overrides, plus `DEDIREN_HOME` / `DEDIREN_VERSION` / `DEDIREN_AUTO_INSTALL` on every host | Agent Plugins has no MCP startup-timeout field, so Codex's 30s default applies; the legacy `startup_timeout_sec` is seconds |
| Copilot CLI | With the Agent Plugins `$schema` on the root manifest, Copilot reads that root `mcp.json` and ignores `mcp/copilot.mcp.json`; it does not interpolate `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` there, and exports `PLUGIN_DATA` / `COPILOT_PLUGIN_DATA` / `CLAUDE_PLUGIN_DATA` into the child as absolute paths. `mcp/copilot.mcp.json` is the legacy lane | Host launch cwd; router sets the upstream child cwd to `workspaceRoot` | Same three `DEDIREN_*` overrides | `timeout` is milliseconds (legacy lane only) |

The shared root `mcp.json` therefore declares no `env` and no `cwd`: one host
would expand a token there and the other would not. Both export the plugin data
directory into the child, which is what the resolver reads.

Codex's 30s startup default is safe: the router answers `initialize` itself
without touching Dediren, and provisioning happens later, on the first
`tools/list`.

Generic local-client compatibility means only that a local client can launch a
stdio process and permits Bash, Python, and Java 21+ with a writable plugin data
directory; it must set `DEDIREN_HOME` to an absolute path when it offers no
plugin data variable, may optionally set `DEDIREN_COMMAND` instead, and must
pass an absolute
`workspaceRoot` on every tool call. It is not a support or packaging promise for
another harness. Preserve the legacy verified-release-cache fallback; nothing
populates it any more. Streamable HTTP is future work only for an explicit
remote/shared multi-client service requirement, because it adds authentication,
origin validation, port and service lifecycle, session isolation, and workspace
authorization responsibilities.

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
- Codex hook commands use `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`. Codex MCP
  interpolation depends on the lane: the Agent Plugins root `mcp.json`
  interpolates `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`, so it is the only Codex lane
  that can hand a server a writable plugin data root; the legacy
  `.codex-plugin` + `mcp/codex.mcp.json` fields stay **literal** — use
  plugin-relative `cwd` / paths where changing directory
  is correct, or a tested source-discovery bootstrap when the server must preserve
  the caller's workspace, and expect no plugin data root there. Claude MCP and
  hook commands use `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}`.
- Copilot plugin MCP commands use `${PLUGIN_ROOT}` and writable plugin data uses
  `${COPILOT_PLUGIN_DATA}`. Keep a separate Copilot MCP file; never let Copilot
  fall through to the Codex bootstrap.

Inspect existing tests before selecting the RED test: extend a suitable cohesive
scenario without weakening coverage; create a new test when the scenario is
distinct or reuse would weaken clarity or regression coverage. A pre-existing
failure counts as RED only when it precisely represents the intended behavior.

## Runtime parity

Every published plugin appears in both marketplaces and has both manifests.
Keep plugin sets, ordering, names, descriptions, and semantic versions aligned.
The Claude manifest and README preserve CalVer `YYYY.0M.MICRO`; Codex derives
strict SemVer `YYYY.M.MICRO` from that authority. Marketplace entries never
carry a `version` field.

When a plugin has a root `plugin.json` (the Agent Plugins manifest, also read by
Copilot CLI), keep its name, description, skills path, and strict-SemVer version
aligned with the legacy Codex manifest.

Each public `SKILL.md` keeps its matching Claude subagent. Codex discovers the
same skill through the Codex manifest's `skills` path; do not create a parallel
Codex workflow. Each `internal-skills/<name>` entry has thin wrappers under both
`.agents/skills/<name>` and `.claude/skills/<name>`.

Keep stack composition explicit in the shared load map: app-design loads Vite
before React for Vite + React, retains React before Next.js, and permits Vite
alone. JavaScript/TypeScript software guidance remains the existing
`typescript.md` lane; security uses its separate evidence-gated `jsts.*` pack,
and Node/React lifecycle-test rules remain under test-quality-audit.
Every Deep test-quality audit assesses suite health by establishing management
evidence before sampling: feedback lanes, project-declared budgets, current
results, runtime distribution, reliability, ownership, overlap, and retirement
discipline. It also includes a bounded setup/teardown lifecycle assessment for
cost attribution, safe infrastructure amortization, per-test mutable-state
isolation, and failure-safe cleanup. Quick remains per-test. Missing optional
history or effectiveness evidence is `unknown`, not a prompt to build analytics.

When a shared workflow needs host behavior, state the capability and give a
runtime mapping with a safe fallback. For example, Claude planning retains
`EnterPlanMode` / `ExitPlanMode`; Codex uses Plan mode when exposed and otherwise
emits a proposed plan for explicit approval.

### Bounded audit-lane gate

The shared audit craft contract defines a bounded-lane gate: `Quick gate: <status>`
for test-quality and DevSecOps, `triage gate: <status>` for IP, and
`limited-scope gate: <status>` for bounded Lean. Its status is `fail` for a
substantiated in-scope block, otherwise `not-evaluated` when required evidence
or machinery cannot rule out blockers, otherwise `pass-limited`. This is a
mechanical limited-scope check, not a Deep/in-depth/full-repo rollup or
reasonable-assurance verdict; see
[`audit-craft.md §4a`](souroldgeezer-audit/docs/audit-reference/audit-craft.md).
IP findings retain their coded criterion, authority class, fact/inference,
remediation, and counsel outcome; neither gate nor verdict is legal clearance.

`software-design` also owns an early-return File Edit lane for bounded non-code
content changes with no software-design or sibling-owned decision. It does not
expand into source-code work: use the shared workflow's format-aware precedence
and direct validation. Its optional clone-local native-tool state helper emits
bounded JSON (`tool_state.py list` / `tool_state.py gc`) and is advisory only.

### Planning-policy execution contract (Codex)

The shared `planning-policy` contract is runtime-neutral. New executable plans
use `contract_version: 4`. Start them from
[references/templates/plan-v4.json](souroldgeezer-policy/skills/planning-policy/references/templates/plan-v4.json);
the discriminator is `contract_version`, never `version`. Versions 2 and 3 are
resume-only (`dispatch_ready: false`, `resume_ready: true`) and new `init-v2` or
`init-v3` stops as `blocked:contract_migration_required`; unversioned version-1
plans remain inspection-readable only.
Every executable leaf
has decision-complete, stable fields: IDs/dependencies, task/boundary, named
read/write sets, settled decisions, size, portable tier, worktree owner, one
acceptance command, bounded return contract, stop conditions, and stable work
unit ID, plus exact `capability_requirements`: baseline `plan-step-base-v1` and
bounded additional requirements. A missing load-bearing field stops as `blocked:missing_input`; do not
search for or invent it. Work units are weighted once from their original size
(`small=1`, `medium=2`, `large=3`) and require `standard_ready_ratio >= 0.60`;
only an explicitly user-approved, recorded analytical-heavy exception waives
that gate. A valid decision-complete v4 plan is approval-ready without host
binding; it is dispatch-ready only after `planning-capability-binding-v1` joins
plan digest, every leaf, host/executor, requirements, and bounded evidence. An
unavailable or mismatched join stops `blocked:capability_unavailable`; never
silently substitute or downgrade. Each v4 plan carries an at-most-4-KiB advisory
`planning-execution-cost-v1` block. The existing validator invocation emits an
at-most-600-proxy-token `planning-cost-advisory-v1`; missing or invalid profiles,
unknown ranges, shared-prefix repetition, retry multiplication, and verification
reserve never affect validity, readiness, dispatch, retry, or lifecycle. Keep
stable-proxy, declared-model-token, and provider-measured lanes separate. The
human plan has one compact `Execution economics` summary and `tracing: off`.
Route an initial inspection to at most one owning audit only when
its bounded question and evidence surface remain unresolved by targeted
inspection or focused tests; ordinary design is not an audit route.

For an approved plan with at least two delegated steps, only the parent may
activate and write a run at
`<git-common-dir>/planning-policy/ledgers/<plan-id>/<run-id>/`; `run-id` is a
lowercase UUID4. The parent assigns every declared step exactly once and issues
one current opaque attempt ID for it. Agents may concurrently execute only
independent ready steps with separate worktrees and write paths. A step has a
finite `max_attempts` (1–5): identical progress fingerprints block a retry as
`blocked:no_progress`; an exhausted step is terminal `blocked:retry_exhausted`;
and a boundary overrun is terminal `oversized`, never an expanded retry.
The ledger is the sole retry-policy owner: new v4 runs stamp
`retry_policy: escalating_remediation_v1`; policy-less v2/v3 and v1 preserve old
behavior. `portable_tier` is initial only. Only `failed:acceptance` and
`blocked:needs_higher_tier` are eligible; one same-tier retry is allowed only
after `failed:acceptance`, while `blocked:needs_higher_tier` escalates
immediately. Later retries use higher tiers through `deep`/`max_attempts`.
Each retry persists a bounded `retry-remediation-v1` artifact and checks
identity, prior-return digest, worktree, boundary, and assignment. Terminal
precedence is repeated result (`blocked:no_progress`), ineligible outcome,
exhaustion (`blocked:retry_exhausted`), then tier ceiling.

Every successful v4 lifecycle result carries a live `next` block of at most
120 proxy tokens. After a long pause or context compaction, read-only
`show --next-only` returns one highest-priority action in an at-most-240-token
envelope. Full `show` remains the diagnostic fallback; load the ledger runtime
reference only for errors, legacy resumption, diagnosis, retention operations,
or ledger authoring/audit. Between active returns, wait for a host notification;
never busy-poll or start an autonomous lifecycle loop.

Successful v2/v3/v4 steps continue `completed` → `integrated` → `cleaned`.
The parent ingests bounded `planning-worktree-result-v1` evidence from the
Git-policy helper: rebase the exact returned branch onto the current parent,
fast-forward-only merge, then prove merged ancestry and clean up without force.
Cleanup retries safely after partial removal by revalidating recorded identity,
branch state, and target ancestry. Routine integration never cherry-picks.
Dependencies become ready only after their prerequisites are cleaned, and their
worktrees start at the then-current parent tip. `validate --closeout` requires
every successful step to be cleaned.

Use bounded checkpoint and lifecycle/retry returns, never raw logs. Every
delegated handoff is one at-most-8-KiB `bounded-step-return-v1` JSON object;
it carries its step/agent/attempt identity, bounded result facts, and no
`run_id`. The ledger hashes its canonical approved plan; a mismatch is
`blocked:plan_tampered`. Its bounded `show` rehydrates one step or a truncated
run summary, not history. Version-1 ledgers remain readable and mutable in
place with `retry_policy: legacy_unbounded` until every version-1 ledger is
terminal. Version-1 keeps its terminal `integrated` state and does not gain
`cleaned`. Current planning-policy cannot approve or dispatch an unversioned
version-1 plan as new work; new documentation uses `init-v4`. Remove legacy
support only in a later explicit breaking release after no version-1 ledger is
nonterminal. The parent owns integration and
end-to-end verification; a delegated return covers only its assigned drafting
and acceptance check.

The parent closes a version-2/3/4 run with explicit `completed`, `blocked`, or
`abandoned` outcome, reopens only an eligible retained blocked run, and uses
`list` for bounded discovery. `gc --dry-run` previews conservative retention:
completed runs 30 days, blocked runs 90 days, abandoned runs 7 days; active,
invalid, and ambiguous records remain preserved. `purge --actor parent` targets
one closed run only (and needs `--before-retention` plus reason before expiry);
there is no bulk deletion.

Runtime tracing is a separate explicit opt-in per v3/v4 run. Ordinary planning and
execution create no usage directory, inspect no telemetry, install no hooks,
and make no network or provider call. Only an explicit request to trace,
measure, or calibrate loads the `trace-init`, `trace-record`, `trace-show`, and
`trace-close` procedure. Usage records contain bounded counters plus
harness/model provenance, never prompts, completions, arguments, results, or
raw logs; they live outside the checkpoint and follow run retention/purge.

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

Never let a pipeline stage or a `||` fallback own a gate's reported exit code —
`cmd | tail` or `cmd | grep ... || fallback` reports the downstream stage's
status, not the gate's, and can read green while the gate itself failed.
Capture `${PIPESTATUS[0]}` right after the pipe, redirect output to a file and
test the bare command, or run the gate unpiped; a status that provably came
from a downstream stage is no evidence the gate ran or passed.

The host smoke must keep both safety flags. It uses temporary `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` state without
replacing `HOME`, verifies installed plugin, skill, agent, and Dediren MCP
surfaces, and fingerprints the normal host plugin/config control planes before
and after. Dediren itself is plugin-provisioned, so the smoke resolves it
through the launcher's own lanes — an explicit `DEDIREN_COMMAND`, or a temporary
`DEDIREN_HOME` that keeps a provisioned bundle out of normal host state — and
never installs into a real per-plugin data directory. Absence of a standalone
Codex validator is a reported skip, not a fabricated pass.

## Documentation and ownership

Update `README.md` when install commands, plugin names, skills, public behavior,
or local validation changes. Update `docs/release-checklist.md` and
`docs/maintenance-procedures.md` when packaging or version mechanics change.
Keep `.github/CODEOWNERS` on executable hook configuration and hook scripts.

No checked-in `.codex/config.toml` should choose a model, approval policy, or
sandbox profile for contributors unless the repository genuinely requires that
setting. Repo-local hooks are enough for this repository and remain subject to
Codex trust review.
