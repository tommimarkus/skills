# souroldgeezer

Claude Code™ plugin marketplace by Sour Old Geezer. This repository
is the marketplace source and published plugin tree. Codex support is additive
through parallel runtime metadata over the same plugin and skill sources.

## What this is

The repo currently ships five plugins:

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `2026.08.5` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md), [lean-audit](souroldgeezer-audit/skills/lean-audit/SKILL.md) | [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md), [security](souroldgeezer-audit/docs/security-reference/devsecops.md), [quality](souroldgeezer-audit/docs/quality-reference/unit-testing.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md) |
| `souroldgeezer-design` | `2026.08.0` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [app-design](souroldgeezer-design/skills/app-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md), [infra-design](souroldgeezer-design/skills/infra-design/SKILL.md) | [software](souroldgeezer-design/docs/software-reference/software-design.md), [app](souroldgeezer-design/docs/app-reference/app-design.md), [api](souroldgeezer-design/docs/api-reference/api-design.md), [infra](souroldgeezer-design/docs/infra-reference/infra-design.md) |
| `souroldgeezer-architecture` | `2026.08.3` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [architecture](souroldgeezer-architecture/docs/architecture-reference/architecture.md) |
| `souroldgeezer-policy` | `2026.08.5` | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) |
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
- `architecture-design` drives Dediren through the plugin's bundled MCP server
  (inline in the Claude manifest and file-backed by
  `souroldgeezer-architecture/.mcp.json` from the Codex manifest); its
  launcher resolves the pinned Dediren runtime from GitHub™ Releases on first use —
  into `${CLAUDE_PLUGIN_DATA}` for installed Claude users, or a writable
  per-user/temp fallback for Codex and the internal CLI lane — and needs Java™ 21
  or newer. The Codex MCP config discovers the installed launcher without changing
  directory, preserving the caller's workspace as Dediren's path boundary.
- Use the repo-local `uv` tooling for the skill architecture report.
- Use the validation script before asking for review.

## Examples

1. Audit a workflow, Dockerfile, or .NET™ logging path with `devsecops-audit`. All four audit skills (`devsecops-audit`, `test-quality-audit`, `ip-hygiene`, `lean-audit`) now disclose auditor independence and assurance level and weight findings by subject materiality via the shared [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md).
2. Review an API surface, extract an existing contract, or build against a brownfield API baseline with `api-design`; its stack packs load a compact core plus only the requested build or review lane.
3. Design or review a frontend app route, screen, or component set with `app-design`, including React, Next.js, and Blazor WebAssembly app surfaces; existing app work uses project assimilation to reuse compliant local tokens/components and avoid extending legacy debt.
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

The parity check validates both marketplaces and both manifest families. The
fragmentation gate additionally validates native Codex manifest structure; the
first-party Codex plugin validator is run during packaging changes when the
installed CLI exposes one.

The host smoke creates temporary `CODEX_HOME` and `CLAUDE_CONFIG_DIR` state,
registers this checkout as both marketplaces, installs all five plugins, checks
the 15 shared skills through Codex prompt discovery and Claude component
inventory, and drives the bundled Dediren JSON-RPC handshake through both host
adapters. It fingerprints the normal plugin/config profile surfaces before and
after and fails if they change. The current Codex CLI has no standalone plugin
validator, so that capability is reported as an explicit skip; Claude strict
validation still runs for every plugin. The cold Dediren path may download the
pinned bundle into the command's temporary runtime-data directory and requires
Java™ 21 or newer.

`scripts/validate-fragmentation.sh` includes
`scripts/test-stop-hooks.sh`.

Optional release-resolved Dediren smoke lane:

```text
DEDIREN_RELEASE_SMOKE=1 uv run python -m unittest tests.architecture_dediren_release_test
```

The smoke lane downloads the pinned Dediren release bundle and requires Java™ 21
or newer on `JAVA_HOME`, `JAVACMD`, or `PATH`.

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
