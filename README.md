# souroldgeezer

Cross-runtime plugin marketplace by Sour Old Geezer. Claude Code™, Codex, and
GitHub™ Copilot CLI publish the same shared skill workflows through additive
host adapters.

## What this is

The repo currently ships five plugins:

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `2026.08.8` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md), [lean-audit](souroldgeezer-audit/skills/lean-audit/SKILL.md) | [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md), [security](souroldgeezer-audit/docs/security-reference/devsecops.md), [quality](souroldgeezer-audit/docs/quality-reference/unit-testing.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md) |
| `souroldgeezer-design` | `2026.08.6` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [app-design](souroldgeezer-design/skills/app-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md), [infra-design](souroldgeezer-design/skills/infra-design/SKILL.md) | [software](souroldgeezer-design/docs/software-reference/software-design.md), [app](souroldgeezer-design/docs/app-reference/app-design.md), [api](souroldgeezer-design/docs/api-reference/api-design.md), [infra](souroldgeezer-design/docs/infra-reference/infra-design.md) |
| `souroldgeezer-architecture` | `2026.08.7` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [architecture](souroldgeezer-architecture/docs/architecture-reference/architecture.md) |
| `souroldgeezer-policy` | `2026.08.10` | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) |
| `souroldgeezer-ops` | `2026.08.0` | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) |

## Install

### Claude Code

Add the shared marketplace, then install the plugins you want:

```text
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
/plugin install souroldgeezer-architecture@souroldgeezer
/plugin install souroldgeezer-policy@souroldgeezer
/plugin install souroldgeezer-ops@souroldgeezer
```

For local development, point Claude at the clone instead:

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
    "souroldgeezer-architecture@souroldgeezer": true,
    "souroldgeezer-policy@souroldgeezer": true,
    "souroldgeezer-ops@souroldgeezer": true
  }
}
```

### Codex

Add the Codex marketplace mirror, then install the plugins you want:

```bash
codex plugin marketplace add tommimarkus/skills
codex plugin add souroldgeezer-audit@souroldgeezer
codex plugin add souroldgeezer-design@souroldgeezer
codex plugin add souroldgeezer-architecture@souroldgeezer
codex plugin add souroldgeezer-policy@souroldgeezer
codex plugin add souroldgeezer-ops@souroldgeezer
```

For local Codex development, use the clone as the marketplace source:

```bash
codex plugin marketplace add /absolute/path/to/skills
codex plugin add souroldgeezer-audit@souroldgeezer
```

### GitHub™ Copilot CLI

Copilot CLI currently consumes the native root `plugin.json` only for the
MCP-equipped architecture plugin:

```bash
copilot plugin marketplace add tommimarkus/skills
copilot plugin install souroldgeezer-architecture@souroldgeezer
```

For local development, add the clone path as the marketplace source before
running the same install command.

## Local development

- Keep task worktrees in the primary checkout's persistent, gitignored
  `.worktrees/<task-name>/` directory. Never use `/tmp`, `$TMPDIR`, tmpfs, or
  other ephemeral storage for a worktree or uncommitted task work.
- Keep `.claude-plugin/marketplace.json` as the shared Claude Code marketplace.
- Keep each plugin's `.claude-plugin/plugin.json` manifest synchronized with its
  Claude marketplace entry on `name` and `description`. `version` lives only in
  the Claude `plugin.json` as the release authority — Claude Code always resolves
  it over a marketplace-entry copy without warning, so marketplace entries never
  carry a `version` key.
- Keep the additive `.agents/plugins/marketplace.json` Codex catalog aligned on
  plugin set, order, and paths, and mirror each plugin through
  `.codex-plugin/plugin.json`. Codex requires strict SemVer, so its version is the
  normalized form of the Claude CalVer authority (`YYYY.0M.MICRO` →
  `YYYY.M.MICRO`).
- The MCP-equipped architecture plugin also has a native Copilot `plugin.json`.
  Keep its identity and strict-SemVer version aligned with Codex; its adapter lives at
  `mcp/copilot.mcp.json`, beside the Codex adapter.
- `architecture-design` drives a host-managed current Dediren CLI through three
  MCP adapters and a shared compatibility router. The plugin does not bundle,
  download, pin, or downgrade Dediren. Install `dediren` on `PATH`, or set
  `DEDIREN_COMMAND` to an explicit executable for controlled validation. To
  avoid stranding pre-multi-harness installs, the MCP launcher otherwise reuses
  the newest executable already present in the former verified release cache;
  it never populates that cache. Each
  operation carries an absolute `workspaceRoot`, preserving the selected
  project as Dediren's path boundary and child-process working directory, so a
  replaced host plugin cache cannot strand later calls in a deleted directory.
  Backend stderr remains visible in host logs; bounded command, cwd, exit, and
  stderr context is also returned with adapter failures.
- Use the repo-local `uv` tooling for the skill architecture report.
- Use the validation script before asking for review.

## Examples

1. Audit a workflow, Dockerfile, or .NET™ logging path with `devsecops-audit`. All four audit skills (`devsecops-audit`, `test-quality-audit`, `ip-hygiene`, `lean-audit`) now disclose auditor independence and assurance level and weight findings by subject materiality via the shared [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md).
2. Review an API surface, extract an existing contract, or build against a brownfield API baseline with `api-design`; its stack packs load a compact core plus only the requested build or review lane, including Python® ASGI/WSGI and serverless API routing.
3. Design or review a frontend app route, screen, or component set with `app-design`, including standalone Vite, Vite + React, React + Next.js, and Blazor WebAssembly surfaces; Vite owns development/build/deployment mechanics while React owns component lifecycle and state.
4. Review or extract a dediren ArchiMate® or UML® architecture/design package, including UML® sequence views or Java™ source evidence, with `architecture-design`.
5. Review infrastructure or IaC topology with `infra-design`; existing IaC work uses project assimilation to classify reused assets, legacy debt, and migration moves.
6. Check a skill/plugin publication-surface edit with `ip-hygiene`.
7. Initialize repository git workflow governance with `git-workflow-policy`.
8. Initialize declarative release governance with `release-policy`, for example
   `release-policy: calver YYYY.MM.build, git tagging`. Bare initialization
   applies the default profiles: conservative git workflow and SemVer
   `v<version>` release tags. Once a target repo adds either policy to root
   guidance such as `AGENTS.md`, matching git or release actions must run that
   policy before changing state. Adopt mode consolidates existing related
   guidance into the initialization/options and removes competing policy prose.
9. Audit a repo, file, or diff for duplication and waste with `lean-audit` (read-only; deterministic engines plus judgment). Skill/command/agent scopes gain per-use findings (`LA-PUC-*`) from legacy file sets or declared multi-entry load routes with predicates, heading anchors, and separately measured selection metadata. Staged, iterative, delegated, or retrying plugin workflows also gain an offline pre-run forecast and orchestrator-survivability findings (`LA-RUN-*`, `LA-ORCH-*`): peak coordinator context stays separate from total usage, verification capacity is reserved, fixed/per-item output can be forecast, and retry, no-progress, unresolved-scope, and bounded-checkpoint contracts are checked statically. The analyzer inventories recognized hook registrations without executing or emitting commands; optional content-free fixtures evidence enabled/model-visible frequency multiplication. Unknown values remain unknown rather than zero. Metadata-only provider/host traces calibrate usage totals but do not prove lifecycle stalls or TDD loops. Opt-in hooks guard new duplication and fidelity; see [hook-recipe](souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md). Explicit requests can additionally run live-verified platform redundancy (`LA-NAT-*`) or propose-only minify (`LA-MIN-*`), which never applies edits.
10. Use `planning-policy` to turn an approved implementation approach into a
    delegation-ready plan. New executable plans use `contract_version: 2`; an
    unversioned version-1 plan remains readable for inspection but is
    `dispatch_ready: false` with a migration deprecation warning. Its shared,
    runtime-neutral contract gives every leaf
    stable IDs, dependencies, task/boundary, named reads and writes, settled
    decisions, size, portable tier, owner, one acceptance command, return shape,
    stop conditions, and a stable work unit. Work units are weighted once
    (`small=1`, `medium=2`, `large=3`); at least 0.60 of that weight must be
    mechanical or standard ready unless the user explicitly approves and the
    plan records an analytical-heavy exception. Missing load-bearing input stops
    the leaf rather than inviting discovery or invention. The parent owns
    integration and end-to-end verification; selective audit routing remains an
    exceptional, bounded-evidence decision after targeted inspection or focused
    tests cannot answer the question.

    For an approved plan with two or more delegated steps, exactly one parent
    creates and writes the checkpoint ledger under the Git common directory at
    `planning-policy/ledgers/<plan-id>/<run-id>/`, where `run-id` is a lowercase
    UUID4. Each declared leaf has one assignment and one current, helper-issued
    attempt identity. Ready agents may work concurrently only on independent
    steps with separate worktrees and write paths. A leaf has a finite
    `max_attempts` (1 through 5): unchanged return facts stop retries as
    `blocked:no_progress`, exhaustion is terminal `blocked:retry_exhausted`, and
    an exceeded task/boundary/read/write set is terminal `oversized` rather than
    a silently broadened retry.
    The ledger is the sole retry-policy owner: new v2 runs stamp
    `retry_policy: escalating_remediation_v1`; policy-less v2 and v1 preserve
    old behavior. `portable_tier` is initial only. Only `failed:acceptance` and
    `blocked:needs_higher_tier` are eligible; one same-tier retry follows only
    `failed:acceptance`, while `blocked:needs_higher_tier` escalates immediately.
    Later retries use higher tiers through `deep`/`max_attempts`; each retry
    persists bounded `retry-remediation-v1` identity/digest/worktree/boundary/
    assignment checks. Terminal precedence is repeated result, ineligible
    outcome, exhaustion, then tier ceiling.

    Successful leaves continue `completed` → `integrated` → `cleaned`.
    The parent ingests bounded `planning-worktree-result-v1` evidence from the
    Git-policy helper, which rebases and fast-forward-only merges rather than
    routinely cherry-picking, then proves merged ancestry before non-force
    cleanup. Cleanup retries safely after partial removal by revalidating
    recorded identity, branch state, and target ancestry. Dependencies become
    ready only after cleanup and start from the then-current parent tip;
    `validate --closeout` requires every successful leaf to be cleaned.

    The ledger records bounded lifecycle returns. Every handoff is one
    at-most-8-KiB `bounded-step-return-v1` JSON object with
    its step, agent, and attempt identity, bounded changed paths, exact scoped
    acceptance result, blockers, typed notes, commit hash, and unstarted
    remainder. It includes no `run_id` or raw logs. The ledger preserves an approved
    plan copy and SHA-256 hash; a mismatch is `blocked:plan_tampered`. Its
    bounded `show` rehydrates either one step or a truncated run summary, not
    event history. A parent closes each run with an explicit completed, blocked,
    or abandoned outcome; it may reopen only an eligible retained blocked run.
    `list` emits bounded discovery, `gc --dry-run` previews outcome-specific
    retention (completed 30 days, blocked 90 days, abandoned 7 days), and
    `purge` requires one exact closed target and parent authority—there is no
    bulk deletion. Invalid, ambiguous, and active state is preserved.
    Version-1 ledgers remain readable and mutable in place with
    `retry_policy: legacy_unbounded` until every version-1 ledger is terminal.
    Their terminal `integrated` state remains unchanged; `cleaned` is v2-only.
    Current planning-policy cannot approve or dispatch an unversioned version-1
    plan as new work; new documentation uses `init-v2`. Remove legacy support
    only in a later explicit breaking release after no version-1 ledger is
    nonterminal. The optional fresh-context comparison is
    `uv run python scripts/planning_policy_forward_eval.py --harness both
    --output-dir /secure/path --execute`; it stores bounded summaries and reports
    an unavailable mapped model as `blocked:model_unavailable`, never as a
    silent downgrade.
11. Use `software-design` for bounded non-code content edits that require no
    design decision through its early-return File Edit lane. It selects the
    user or repository-required format-aware operation first, uses `jq` for
    JSON and Mike Farah `yq` for YAML/TOML/XML where repository guidance
    applies, and otherwise makes the smallest directly validated edit. Its
    advisory clone-local native-tool state helper emits bounded JSON through
    `tool_state.py list` and `tool_state.py gc`; it never creates a tracked
    preference file or grants target-specific authority.

12. Use `software-design` for capability-based tool selection during design and
    implementation: it checks repository-configured commands, host-exposed
    integrations, and task-relevant installed tools without crawling the
    machine, then prefers the best fit and structured authoritative evidence.
    When Context7 MCP is already exposed and current third-party documentation
    matters, it resolves the library and queries relevant docs; otherwise it
    continues through project docs, local help, official sources, or a bounded
    fallback. The plugin does not install or configure Context7 and does not use
    its CLI as a fallback.
13. Use `software-design` Review's additive fragility check when changed code
    may hide a precondition or scatter a nearby volatile decision. It is an
    evidence-based review of regression risk, not a style rule, speculative
    abstraction demand, analyzer requirement, or development-method mandate.
    Findings pair an `SD-*` code with plain language and finish as pass, warn,
    block, or not-assessed. Project-owned native tool results can support that
    review but remain candidates, never a tool-adoption prerequisite. An explicit
    “no”, “not now”, or “defer” to one optional suggestion is kept clone-local
    for 30 UTC calendar days; it stays silent until the stored date, does not
    suppress fragility findings, and falls back only to one conversation-local
    disclosure if the local write is denied.

## Validation

Run these from the repo root:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .
git diff --check
uv run python -m unittest discover -s tests -p '*_test.py'
```

The parity check validates both marketplaces, both complete manifest families,
and the architecture plugin's native Copilot manifest and MCP adapter. The
fragmentation gate additionally validates native Codex manifest structure; the
first-party Codex plugin validator is run during packaging changes when the
installed CLI exposes one.

The host smoke creates temporary `CODEX_HOME`, `CLAUDE_CONFIG_DIR`,
`COPILOT_HOME`, and `COPILOT_CACHE_HOME` state without replacing `HOME`. It
registers this checkout, installs every supported plugin surface, checks the 15
shared Claude/Codex skills plus the Copilot architecture skill, and drives the
external Dediren JSON-RPC handshake through all three host adapters. It also
checks legacy initialization and current stateless discovery, verifies required
absolute `workspaceRoot` input, and fingerprints the normal host profiles before
and after. The current Codex CLI has no standalone plugin validator, so that is
an explicit skip; Claude strict validation still runs for every plugin.

`scripts/validate-fragmentation.sh` includes
`scripts/test-stop-hooks.sh`.

Optional host-managed Dediren smoke lane:

```text
DEDIREN_RUNTIME_SMOKE=1 uv run python -m unittest tests.architecture_dediren_release_test
```

The smoke lane uses the current `dediren` on `PATH`, or the executable selected
by `DEDIREN_COMMAND`; it never downloads a runtime.

## Detailed docs

- [souroldgeezer-audit/docs/audit-reference/audit-craft.md](souroldgeezer-audit/docs/audit-reference/audit-craft.md)
- [souroldgeezer-audit/docs/audit-reference/materiality.md](souroldgeezer-audit/docs/audit-reference/materiality.md)
- [souroldgeezer-audit/docs/audit-reference/sampling-projection.md](souroldgeezer-audit/docs/audit-reference/sampling-projection.md)
- [souroldgeezer-audit/docs/security-reference/devsecops.md](souroldgeezer-audit/docs/security-reference/devsecops.md)
- [souroldgeezer-audit/docs/quality-reference/unit-testing.md](souroldgeezer-audit/docs/quality-reference/unit-testing.md)
- [souroldgeezer-audit/docs/quality-reference/integration-testing.md](souroldgeezer-audit/docs/quality-reference/integration-testing.md)
- [souroldgeezer-audit/docs/quality-reference/e2e-testing.md](souroldgeezer-audit/docs/quality-reference/e2e-testing.md)
- [souroldgeezer-audit/docs/quality-reference/testing-core.md](souroldgeezer-audit/docs/quality-reference/testing-core.md)
- [souroldgeezer-audit/skills/ip-hygiene/SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md)
- [souroldgeezer-audit/skills/lean-audit/SKILL.md](souroldgeezer-audit/skills/lean-audit/SKILL.md)
- [souroldgeezer-design/docs/software-reference/software-design.md](souroldgeezer-design/docs/software-reference/software-design.md)
- [souroldgeezer-design/docs/app-reference/app-design.md](souroldgeezer-design/docs/app-reference/app-design.md)
- [souroldgeezer-design/docs/api-reference/api-design.md](souroldgeezer-design/docs/api-reference/api-design.md)
- [souroldgeezer-design/docs/infra-reference/infra-design.md](souroldgeezer-design/docs/infra-reference/infra-design.md)
- [souroldgeezer-design/docs/design-reference/architecture-pairing-core.md](souroldgeezer-design/docs/design-reference/architecture-pairing-core.md)
- [souroldgeezer-architecture/docs/architecture-reference/architecture.md](souroldgeezer-architecture/docs/architecture-reference/architecture.md)
- [souroldgeezer-policy/docs/policy-reference/policy-posture-core.md](souroldgeezer-policy/docs/policy-reference/policy-posture-core.md)
- [souroldgeezer-policy/skills/git-workflow-policy/SKILL.md](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md)
- [souroldgeezer-policy/skills/release-policy/SKILL.md](souroldgeezer-policy/skills/release-policy/SKILL.md)
- [souroldgeezer-policy/skills/tdd-policy/SKILL.md](souroldgeezer-policy/skills/tdd-policy/SKILL.md)
- [souroldgeezer-policy/skills/planning-policy/SKILL.md](souroldgeezer-policy/skills/planning-policy/SKILL.md)
- [souroldgeezer-ops/docs/provider-reference/github.md](souroldgeezer-ops/docs/provider-reference/github.md)
- [souroldgeezer-ops/docs/provider-reference/gitlab.md](souroldgeezer-ops/docs/provider-reference/gitlab.md)
- [souroldgeezer-ops/docs/provider-reference/authoring.md](souroldgeezer-ops/docs/provider-reference/authoring.md)
- [souroldgeezer-ops/docs/provider-reference/provider-lifecycle-core.md](souroldgeezer-ops/docs/provider-reference/provider-lifecycle-core.md)
- [souroldgeezer-ops/skills/issue-ops/SKILL.md](souroldgeezer-ops/skills/issue-ops/SKILL.md)
- [souroldgeezer-ops/skills/pr-ops/SKILL.md](souroldgeezer-ops/skills/pr-ops/SKILL.md)
- [docs/release-checklist.md](docs/release-checklist.md)
- [docs/skill-architecture.md](docs/skill-architecture.md)
