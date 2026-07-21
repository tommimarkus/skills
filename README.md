# souroldgeezer

Claude Code™ plugin marketplace by Sour Old Geezer. This repository
is the marketplace source and published plugin tree.

## What this is

The repo currently ships five plugins:

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `2026.07.22` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md), [lean-audit](souroldgeezer-audit/skills/lean-audit/SKILL.md) | [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md), [security](souroldgeezer-audit/docs/security-reference/devsecops.md), [quality](souroldgeezer-audit/docs/quality-reference/unit-testing.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md) |
| `souroldgeezer-design` | `2026.07.10` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [app-design](souroldgeezer-design/skills/app-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md), [infra-design](souroldgeezer-design/skills/infra-design/SKILL.md) | [software](souroldgeezer-design/docs/software-reference/software-design.md), [app](souroldgeezer-design/docs/app-reference/app-design.md), [api](souroldgeezer-design/docs/api-reference/api-design.md), [infra](souroldgeezer-design/docs/infra-reference/infra-design.md) |
| `souroldgeezer-architecture` | `2026.07.45` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [architecture](souroldgeezer-architecture/docs/architecture-reference/architecture.md) |
| `souroldgeezer-policy` | `2026.07.2` | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md) |
| `souroldgeezer-ops` | `2026.07.2` | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) |

## Install

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

## Local development

- Keep `.claude-plugin/marketplace.json` as the shared marketplace.
- Keep each plugin's `.claude-plugin/plugin.json` manifest synchronized with its
  marketplace entry on `name` and `description`. `version` lives only in
  `plugin.json` — Claude Code always resolves it over a marketplace-entry copy
  without warning, so marketplace entries never carry a `version` key.
- `architecture-design` drives Dediren through the plugin's bundled MCP server
  (`souroldgeezer-architecture/.claude-plugin/plugin.json` `mcpServers`); its
  launcher resolves the pinned Dediren runtime from GitHub™ Releases on first use —
  into `${CLAUDE_PLUGIN_DATA}` for installed users, or `.cache/dediren/releases/` in
  this repo (do not commit that cache) — and needs Java™ 21 or newer.
- Use the repo-local `uv` tooling for the skill architecture report.
- Use the validation script before asking for review.

## Examples

1. Audit a workflow, Dockerfile, or .NET™ logging path with `devsecops-audit`. All four audit skills (`devsecops-audit`, `test-quality-audit`, `ip-hygiene`, `lean-audit`) now disclose auditor independence and assurance level and weight findings by subject materiality via the shared [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md).
2. Review an API surface, extract an existing contract, or build against a brownfield API baseline with `api-design`.
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
9. Audit a repo, file, or diff for duplication and waste — near-duplicate or restated prose, broken or stale references, dead files, oversized always-loaded context, wastefully verbose passages — with `lean-audit` (read-only; a bundled deterministic engine plus a judgment layer for the cases it cannot decide). When the scope contains skills, commands, or agents, a surface-gated per-use cost lens additionally measures per-mode load cost and recommends fidelity-safe reductions (`LA-PUC-*`). Opt-in hooks can soft-block *new* duplication (PreToolUse) and per-use fidelity regressions (PreToolUse or session-end Stop) and warn on per-use cost growth — fail-open and overridable; see [hook-recipe](souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md). On explicit request only, an opt-in platform-redundancy lens (`LA-NAT-*`) flags custom hooks/scripts, guidance prose, skills/commands/agents, or MCP servers that reinvent a native Claude Code™ capability — verified live via the `claude-code-guide` subagent (never a bundled feature list), surfaced as review-not-delete, and never run as part of a normal waste audit. Also on explicit request only, an opt-in minify lens turns the detected waste into a propose-only reduction: a reviewable diff plus an adversarial fidelity report (verified pointers, target-eval re-run, intent diff, token and per-use closure deltas via the bundled harness) — it never applies edits, and failed reductions are rejected with a reason, never merged.

## Validation

Run these from the repo root:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
git diff --check
python -m unittest
```

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
- [souroldgeezer-architecture/docs/architecture-reference/architecture.md](souroldgeezer-architecture/docs/architecture-reference/architecture.md)
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
