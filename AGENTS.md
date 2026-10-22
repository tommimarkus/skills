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

Architecture Review preserves original package evidence. When a reproducibility
build is needed, use the architecture skill's isolated-review procedure and its
byte-accounted persistent copy; never rebuild or refresh the reviewed original.

Keep this file, `CLAUDE.md`, and `README.md` current when repository structure,
runtime support, install commands, validation, or a public skill contract
changes. `AGENTS.md` owns Codex-facing repository guidance; `CLAUDE.md` remains
the self-contained Claude Code contract. Cross-runtime rules must agree without
making either runtime load the other's file first.

## Operation status

<!-- lean-audit:sync-intentional: CLAUDE.md § Operation status states the same rule for Claude Code; each runtime file stays self-contained, so edit both together. -->

For every operation that crosses about one second, keep status discoverable.
Immediately acknowledge known slow foreground work, then report meaningful
milestones or confirmed waiting within 60 seconds when the host can emit them.
Use real completed/total progress only when a total is known; otherwise label
the state indeterminate and never invent a percentage or ETA. Clear busy status
on usable success, failure, cancellation, or awaiting input; keep housekeeping
and terminal outcomes inspectable, with actionable failures surfaced. Prefer
host notifications over polling and aggregate background status without repeated
interruption. Do not promise an update during an uninterruptible host call;
disclose that limit when it applies. The timing limits are repository guidance,
not a host guarantee.

## Repository shape

- `.agents/plugins/marketplace.json`: native Codex marketplace.
- `.claude-plugin/marketplace.json`: Claude Code marketplace.
- `<plugin>/plugin.json` + `<plugin>/mcp.json`: Agent Plugins 1.0.0 manifest and
  its MCP configuration — the current Codex lane, and the only one that
  interpolates `${PLUGIN_DATA}` in MCP config. The same root `plugin.json` is the
  native Copilot manifest when that plugin supports Copilot CLI directly;
  spec-aware Copilot reads root `mcp.json`, while its legacy adapter lives at
  `<plugin>/mcp/copilot.mcp.json`.
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

<!-- lean-audit:sync-intentional: CLAUDE.md § Dediren MCP adapter contract states the same contract for Claude Code; each runtime file stays self-contained, so edit both together. -->

The architecture plugin's Dediren configuration is host-specific, while its
shared launcher/router has no harness detection. The maintained host adapters
are Claude Code, Codex, and Copilot CLI; the router only launches a local
stdio Dediren process for the explicit `workspaceRoot` supplied to each tool
call. Dediren itself is provisioned by the plugin: on first use the launcher
installs the pinned, checksum-verified release (pin `2026.10.0`, support floor
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

Per-release Dediren behaviour (export assurance, import and render lanes,
diagnostics, and schema migrations) is recorded in architecture-design's
[source grounding](souroldgeezer-architecture/skills/architecture-design/references/source-grounding.md)
and the references it routes to; adopt a new release through
[docs/maintenance-procedures.md § Dediren upstream release adoption](docs/maintenance-procedures.md#dediren-upstream-release-adoption).
The repo's fixture compatibility baseline is 2026.08.9; the support floor
stays 2026.07.28.

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
  The lean-audit, test-quality-audit, and planning-policy bundled scripts
  follow the enforced ruff + `mypy --strict` standard (config in
  `pyproject.toml`, gate test `tests/lean_audit_python_standard_test.py`).
- Lean Audit's metadata-only `workflow_cost.py --trace` lane streams native
  Codex rollout JSONL, sums complete `last_token_usage` records rather than
  cumulative totals, and reports explicit coverage plus bounded content-free
  lifecycle counters. Missing or partial usage is calibration-ineligible; the
  counters are evidence, not automatic causal findings or proof of livelock.
- Lean Audit normal Markdown scans report requested-scope coverage and reject an
  empty eligible scope; workflow forecasts require declared core evidence before
  reporting feasible or at-risk, while a proved expected overflow remains a block.
- Do not force-add ignored files. Before a commit, run
  `git ls-files -ci --exclude-standard`; the result must be empty unless the
  user explicitly approved an exact tracked exception.
- Run repository-wide scanners from the clean task worktree itself, not the
  primary checkout; nested worktrees otherwise pollute primary enumeration.
- Shared skill commands must preserve documented Claude substitutions and add a
  Codex source-path form beside them. Never replace `${CLAUDE_SKILL_DIR}` or
  `${CLAUDE_PLUGIN_ROOT}` with a generic placeholder as the only instruction.
- [`data-efficiency.md`](souroldgeezer-design/docs/design-reference/data-efficiency.md) is shared:
  api-design owns its HTTP-to-storage application and API findings; software-design
  owns non-HTTP algorithms and data paths. Report each defect once.
- Codex hook commands use `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`. Codex MCP
  interpolation depends on the lane: the Agent Plugins root `mcp.json`
  interpolates `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`, so it is the only Codex lane
  that can hand a server a writable plugin data root; the legacy
  `.codex-plugin` + `mcp/codex.mcp.json` fields stay **literal** — use
  plugin-relative `cwd` / paths where changing directory
  is correct, or a tested source-discovery bootstrap when the server must preserve
  the caller's workspace, and expect no plugin data root there. Claude MCP and
  hook commands use `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}`.
- Legacy Copilot MCP commands use `${PLUGIN_ROOT}` and writable plugin data uses
  `${COPILOT_PLUGIN_DATA}`. Keep that separate fallback file; never let legacy
  Copilot fall through to the Codex bootstrap. Spec-aware Copilot consumes the
  shared root `mcp.json` instead and exports plugin-data variables to the child;
  keep that root file free of `env` and `cwd`, as documented above.

Inspect existing tests before selecting the RED test, and classify the change
first by its effect at the seam (by default each module's public API): new or
changed observable behavior there needs a focused failing test at the cheapest
level that proves it through the seam; a change with no effect at the seam is a
behavior-preserving refactor and runs under existing passing tests, adding
bounded characterization coverage only where protection is missing; trivial
wiring, delegation, accessors, and declarative config get no RED of their own.
Extend a suitable cohesive scenario without weakening coverage; create a new
test when the scenario is distinct or reuse would weaken clarity or regression
coverage, reusing existing fixtures. A pre-existing failure counts as RED only
when it precisely represents the intended behavior. Run the focused scenario per
RED/GREEN step and the full suite at the declared cadence. REFACTOR includes the
suite: retire or consolidate a test the new one supersedes, naming its
successor; rewrite at the seam or delete any scaffold test below it before GREEN
lands; removing a behavior removes its tests. Reuse `tests/surface_test_lib.py`
helpers before defining new ones; share only immutable setup; no fixed sleeps,
real clocks, or reliance on the machine's locale or timezone.

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
App-design also owns user-flow mapping and adaptive screen layout through a
framework-neutral on-demand procedure for substantial multi-screen, dashboard,
and material-layout work. Approved direction skips alternatives; only routine
component/state work and narrow approved-layout changes skip the whole procedure.
Unsettled direction calls for two or three meaningful alternatives with
tradeoffs and a selection checkpoint. Modal dialogs have modality semantics
distinct from nonmodal popovers, tooltips, and portal mounting. Supported
`'use server'` Server Function references may cross the Server/Client prop
boundary; ordinary functions, server-only clients, and secrets may not.
Every Deep test-quality audit assesses suite health by establishing management
evidence before sampling: feedback lanes, project-declared budgets, current
results, runtime distribution, reliability, ownership, overlap, and retirement
discipline. It also includes a bounded setup/teardown lifecycle assessment for
cost attribution, safe infrastructure amortization, per-test mutable-state
isolation, and failure-safe cleanup. Deep appends a propose-only suite
recovery program when Suite health substantiates a feedback or efficiency
finding. Quick remains per-test. Missing optional history or effectiveness
evidence is `unknown`, not a prompt to build analytics.

When a shared workflow needs host behavior, state the capability and give a
runtime mapping with a safe fallback. For example, Claude planning retains
`EnterPlanMode` / `ExitPlanMode`; Codex uses Plan mode when exposed and otherwise
emits a proposed plan for explicit approval.

### Bounded audit-lane gate

For delegated Deep/in-depth audit population and coverage reconciliation, follow
[scaled-audit.md §3](souroldgeezer-audit/docs/audit-reference/scaled-audit.md#3-delegation-protocol),
including authoritative enumeration before slicing.

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
text/data changes with no software-design or sibling-owned decision. It does
not expand into source-code, API/schema redesign, IaC, or ambiguous destructive
work: use the shared workflow's format-aware precedence and direct validation.
Its optional clone-local native-tool state helper emits bounded JSON
(`tool_state.py list` / `tool_state.py gc`) and is advisory only.

For DevSecOps audits, resolve cost guidance from the target repository's
`AGENTS.md` and `CLAUDE.md` regardless of the active harness. Apply the rule
scoped to the current host and task; retain matching guidance from the other
file as evidence and disclose conflicting policies before applying paid-control
criteria. Do not treat this repository's guidance as the target's policy.

### Planning-policy execution contract (Codex)

<!-- lean-audit:sync-intentional: CLAUDE.md § Planning-policy execution contract (Claude Code) is the Claude Code counterpart; each runtime file stays self-contained, so edit both together. -->

The contract lives in the skill, not here. Load it through the
[SKILL.md load map](souroldgeezer-policy/skills/planning-policy/SKILL.md), which
routes to the [plan contract](souroldgeezer-policy/skills/planning-policy/references/plan-contract.md),
[ledger contract](souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md),
[approval](souroldgeezer-policy/skills/planning-policy/references/approval-handoff.md),
[worker](souroldgeezer-policy/skills/planning-policy/references/worker-handoff.md) and
[verify](souroldgeezer-policy/skills/planning-policy/references/verify-handoff.md) handoffs,
[plan series](souroldgeezer-policy/skills/planning-policy/references/plan-series.md),
[usage tracing](souroldgeezer-policy/skills/planning-policy/references/usage-tracing.md), and
[ledger compatibility](souroldgeezer-policy/skills/planning-policy/references/ledger-compatibility.md).
New executable plans use `contract_version: 5`, started from
[plan-v5.json](souroldgeezer-policy/skills/planning-policy/references/templates/plan-v5.json);
versions 1–4 are retired; retained pre-v5 runs are handled per
[ledger compatibility](souroldgeezer-policy/skills/planning-policy/references/ledger-compatibility.md).

Codex host adapter ([codex.md](souroldgeezer-policy/skills/planning-policy/extensions/codex.md)):
the portable tiers map exactly: `mechanical` → `gpt-5.6-luna`/`low`,
`standard` → `gpt-5.6-terra`/`medium`, `analytical` → `gpt-5.6-sol`/`high`,
`deep` → `gpt-5.6-sol`/`xhigh`. If the mapping is unavailable, return
`blocked:model_unavailable` and never silently downgrade. Plan prose is written
for a fresh parent per [orchestrator readability](souroldgeezer-policy/skills/planning-policy/references/core-workflow.md#orchestrator-readability).
The opt-in fresh-context comparison is
`uv run python scripts/planning_policy_forward_eval.py --harness both --output-dir /secure/path --execute`.

## Security and local publication

<!-- lean-audit:sync-intentional: CLAUDE.md § Security and local publication states the same cross-runtime repository contract; each runtime file stays self-contained, so edit both together. -->

[`SECURITY.md`](SECURITY.md) owns supported versions, the reporting channel,
response targets, and coordinated disclosure. Private vulnerability reporting
is the chosen GitHub channel, but its enablement is pending and unverified;
never claim it is enabled until the repository state is re-read after the live
change. Keep sensitive report content out of public issues. The threat model,
OWASP SCVS Level 1 target and gap matrix, non-claim of SLSA, and accepted
writer-trust residuals live in [`docs/security-baseline.md`](docs/security-baseline.md).

A push of `main` is publication. From the exact clean candidate commit, run:

```text
python3 -B scripts/publication_check.py --repo-root . record
```

This runs the ordered candidate gates with the unconditional safety-flagged
host smoke and stores a commit/tree-bound local receipt in the Git common
directory. After the one allowed atomic version-only follow-up, run `record
--version-followup`. `check-push` is the pre-push entrypoint; `install-hook` and
`uninstall-hook` manage only this repository's hook and refuse to overwrite or
remove a different hook. Installing the hook, pushing, and changing GitHub
security settings require the task's explicit authority. The receipt and hook
are bypassable local controls; they are not CI, a required status check,
independent approval, artifact provenance, or proof of attained SCVS
conformance.

## Version and release policy

The Claude manifest and README use CalVer `YYYY.0M.MICRO` as the release
authority. Codex and any native Copilot manifest mirror it as strict SemVer
`YYYY.M.MICRO`.

Feature branches and worktrees carry content only. Do not increment existing
version cells there. Verify the exact clean candidate before integration, then
fast-forward that commit. After integration, compute the next stamp on `main`:

```text
uv run python scripts/version_stamp.py guard
uv run python scripts/version_stamp.py compute --plugin <name>
```

Then apply the padded computed stamp to the Claude manifest and matching README
cell, and its normalized derivative to the Codex and native Copilot manifests,
in an integration commit that contains only version changes. Verification
evidence from the exact clean candidate survives that atomic follow-up only
when fast-forward ancestry is
proved and the complete change is limited to these version cells: the Claude
manifest, the matching normalized legacy Codex and (when present) root Agent
Plugins/Copilot manifests, and the matching README version-table cell. Run the
focused version and metadata-parity checks for that fixed surface. Any other
source, plan, evidence, surface, or integration drift requires the full
candidate verification again. New manifests added by a feature branch may
carry the existing release's SemVer-normalized value; that is packaging content,
not a release increment.

Breaking or additive public-surface work requires the repository's in-depth
`ip-hygiene` gate. Cosmetic changes use scoped triage.

## Validation

### Primary checks

<!-- lean-audit:sync-intentional: CLAUDE.md § Repo-local Python® tooling › Primary checks states the same check list for Claude Code; each runtime file stays self-contained, so edit both together. -->

Run the changed-surface checks first. Before integration, run the following
ordered candidate gates from the clean persistent task worktree at repository
root, preserving each command's exit status:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
uv run python souroldgeezer-audit/skills/lean-audit/references/scripts/lean_engine.py .  # exit 1 on block findings; info/warn stay advisory
uv run python -m unittest discover -s tests -p '*_test.py'
scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation --changed-since main .
git diff --check
uv run python scripts/version_stamp.py guard
```

The lean engine gate fails only on block findings, so its exit 0 proves only that no block is new. Info and warn findings already on the base stay advisory (run `lean-audit` periodically for them); compare the engine's findings on the paths a change touches against a base run, and fix each one the change introduced or declare it with a rationale.

### Gate order and evidence

<!-- lean-audit:sync-intentional: CLAUDE.md § Repo-local Python® tooling › Gate order and evidence states the same gate-order, evidence-survival, fast-gate, exit-status, zero-test, and host-smoke rules for Claude Code; each runtime file stays self-contained, so edit those rules in both together. -->

Run the version guard after the candidate gates and before fast-forward
integration. The fragmentation script runs metadata and stop-hook checks. The explicit
`*_test.py` discovery command above owns the one full-suite run at closeout.
This exact clean candidate and ordered gate sequence own the full verification
evidence; fast-forward integration preserves it. If only the fixed version
cells documented above change afterward, run the focused version guard and
metadata-parity checks. Any other drift returns to the full sequence.

Also validate every Codex plugin with the current first-party plugin validator
when it is available, and run `claude plugin validate --strict` through the
repository report path when the Claude CLI is installed. A test run that
collects zero tests is a failed gate.

A plan leaf whose write set touches a surface one of the fast gates covers runs
that gate in its own acceptance command, from its own worktree, whenever the
base already passes it: `scripts/validate-fragmentation.sh` for JSON/TOML,
manifest, marketplace, runtime-metadata, and Stop-hook paths; the stdlib report
engine `python3 -B scripts/skill_architecture_report.py --strict .` for skill,
agent, reference, manifest, and repo-guidance paths; and
`python3 -B -m unittest tests.test_code_clone_ratchet_test` for `tests/`. Each
takes about a second, so a defect fails the leaf that introduced it rather than
a later slice's closeout. The full suite and the host smoke stay closeout-only.

Never let a pipeline stage or a `||` fallback own a gate's reported exit code —
`cmd | tail` or `cmd | grep ... || fallback` reports the downstream stage's
status, not the gate's, and can read green while the gate itself failed.
Capture `${PIPESTATUS[0]}` right after the pipe, redirect output to a file and
test the bare command, or run the gate unpiped; a status that provably came
from a downstream stage is no evidence the gate ran or passed.

The host smoke must keep both safety flags. It uses temporary `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` state without
replacing `HOME`, clears inherited plugin-data roots that could redirect
provisioning, verifies installed plugin, skill, agent, and Dediren MCP
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
Use `docs/contributing.md` as the contributor entry point and keep its guide map
accurate when a maintained documentation surface moves.
Keep `.github/CODEOWNERS` on executable hook configuration and hook scripts.

No checked-in `.codex/config.toml` should choose a model, approval policy, or
sandbox profile for contributors unless the repository genuinely requires that
setting. Repo-local hooks are enough for this repository and remain subject to
Codex trust review.
