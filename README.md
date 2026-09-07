# souroldgeezer

Cross-runtime plugin marketplace by Sour Old Geezer. Claude Code™, Codex, and GitHub™ Copilot CLI publish the same shared skill workflows through additive host adapters.

## What this is

Install the plugin that owns the task, then describe the work in ordinary language. Start with [using skills](docs/using-skills.md) for task examples and boundaries, or use [runtime support](docs/runtime-support.md) for host behaviour.

The repo currently ships five plugins:

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `2026.08.19` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md), [lean-audit](souroldgeezer-audit/skills/lean-audit/SKILL.md) | [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md), [security](souroldgeezer-audit/docs/security-reference/devsecops.md), [quality](souroldgeezer-audit/docs/quality-reference/unit-testing.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md) |
| `souroldgeezer-design` | `2026.09.1` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [app-design](souroldgeezer-design/skills/app-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md), [infra-design](souroldgeezer-design/skills/infra-design/SKILL.md) | [software](souroldgeezer-design/docs/software-reference/software-design.md), [app](souroldgeezer-design/docs/app-reference/app-design.md), [api](souroldgeezer-design/docs/api-reference/api-design.md), [infra](souroldgeezer-design/docs/infra-reference/infra-design.md) |
| `souroldgeezer-architecture` | `2026.08.21` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [architecture](souroldgeezer-architecture/docs/architecture-reference/architecture.md) |
| `souroldgeezer-policy` | `2026.09.1` | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md), [scope-policy](souroldgeezer-policy/skills/scope-policy/SKILL.md) | [git workflow](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release](souroldgeezer-policy/skills/release-policy/SKILL.md), [TDD](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning](souroldgeezer-policy/skills/planning-policy/SKILL.md), [scope](souroldgeezer-policy/skills/scope-policy/SKILL.md) |
| `souroldgeezer-ops` | `2026.08.0` | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) |

## Install

### Claude Code

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
  "extraKnownMarketplaces": {"souroldgeezer": {"source": {"source": "directory", "path": "/absolute/path/to/skills"}}},
  "enabledPlugins": {"souroldgeezer-audit@souroldgeezer": true, "souroldgeezer-design@souroldgeezer": true, "souroldgeezer-architecture@souroldgeezer": true, "souroldgeezer-policy@souroldgeezer": true, "souroldgeezer-ops@souroldgeezer": true}
}
```

### Codex

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

Copilot CLI currently consumes the native root `plugin.json` only for the MCP-equipped architecture plugin:

```bash
copilot plugin marketplace add tommimarkus/skills
copilot plugin install souroldgeezer-architecture@souroldgeezer
```

For local development, add the clone path as the marketplace source before running the same install command. See [runtime support](docs/runtime-support.md) for adapter boundaries.

### Dediren runtime (architecture plugin only)

`architecture-design` provisions its pinned, checksum-verified Dediren bundle when the host first lists its tools. Java™ 21+ is the normal prerequisite. The [Dediren runtime guide](souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md) covers air-gapped hosts, overrides, and failures.

## Local development

Use the [contributor guide](docs/contributing.md) for a persistent task worktree, validation, and release boundaries. Its [maintenance procedures](docs/maintenance-procedures.md) cover rare runtime operations.

## Examples

- “Review this API for inconsistent error responses” loads `api-design`.
- “Audit this pull request’s test suite” loads `test-quality-audit`.
- “Create a user-flow and responsive layout for this dashboard” loads `app-design`.
- “Prepare this issue for implementation” loads `issue-ops`.

Each skill’s expected output and boundaries are in [using skills](docs/using-skills.md).

## Validation

Contributors run the documented checks in [contributing](docs/contributing.md), including `scripts/test-stop-hooks.sh` through the fragmentation gate.

## Detailed docs

- [Using skills](docs/using-skills.md): task selection, examples, outputs, and boundaries.
- [Runtime support](docs/runtime-support.md): supported hosts, adapters, hooks, and Dediren.
- [Contributor guide](docs/contributing.md): local setup and validation.
- [Skill architecture standard](docs/skill-architecture.md): authoring and review judgment.
- [Privacy policy](PRIVACY.md) and [terms](TERMS.md).
