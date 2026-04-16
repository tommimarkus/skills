# souroldgeezer

Claude Code plugin marketplace by Sour Old Geezer. Currently ships one plugin:
**souroldgeezer-audit** — rubric-driven audits for DevSecOps posture and test
quality, with per-stack extensions and matching subagents.

## Install

Add this marketplace and enable the plugin in Claude Code:

```
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
```

Or, for local development against a clone:

```json
// ~/.claude/settings.json
{
  "extraKnownMarketplaces": {
    "souroldgeezer": {
      "source": { "source": "directory", "path": "/absolute/path/to/skills" }
    }
  },
  "enabledPlugins": {
    "souroldgeezer-audit@souroldgeezer": true
  }
}
```

## What's in `souroldgeezer-audit`

Two audit skills, each with a matching one-shot subagent:

| Skill | Audits | Stack extensions |
|---|---|---|
| [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | Pipelines, IaC, release artifacts, code-level security smells | [bicep](souroldgeezer-audit/skills/devsecops-audit/extensions/bicep.md), [dockerfile](souroldgeezer-audit/skills/devsecops-audit/extensions/dockerfile.md), [dotnet-security](souroldgeezer-audit/skills/devsecops-audit/extensions/dotnet-security.md), [github-actions](souroldgeezer-audit/skills/devsecops-audit/extensions/github-actions.md) |
| [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | Unit, integration, and E2E test quality (dispatches on detected test type) | [dotnet-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/), built on a shared [dotnet-core](souroldgeezer-audit/skills/test-quality-audit/extensions/dotnet-core.md) |

Subagents live alongside in [souroldgeezer-audit/agents/](souroldgeezer-audit/agents/)
and invoke the same skills, making them usable as delegated one-shots.

## How the audits work

- **Rubric-driven.** The skills are *workflows* that apply an external rubric.
  Findings cite smell codes (e.g. `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`); the prose
  lives in the rubric, not in the skill.
- **You bring the rubric.** The audited repo is expected to provide:
  - `docs/security-reference/devsecops.md` for `devsecops-audit`
  - `docs/quality-reference/unit-testing.md` (and siblings for integration / E2E)
    for `test-quality-audit`

  Without a rubric the skill will tell you what's missing rather than fabricate
  codes.
- **Quick vs Deep modes.** Every audit exposes both. *Quick* = single file or PR
  diff, per-finding output. *Deep* = whole-repo, sectioned rollup, optional MCP
  live-state probes. If the request is ambiguous, the skill asks.
- **Per-stack extensions.** Detected on demand. Extensions **add** namespaced
  smells or **carve out** core smells for idiomatic framework patterns — they
  never override core rules. See each skill's `extensions/README.md` for the
  authoring convention.
- **Disclosure footer.** Every report ends with a footer listing which
  extensions loaded, MCP availability, cost stance (where applicable), and the
  rubric path. This is how you audit the auditor.

## Repository layout

```
.claude-plugin/marketplace.json    # marketplace manifest
souroldgeezer-audit/               # the plugin
  .claude-plugin/plugin.json
  agents/*.md                      # subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # workflow
    extensions/                    # per-stack smell packs
    references/                    # smell catalog + reusable procedures
    config.yaml                    # optional, skill-specific
undecided/                         # skills not yet assigned to a plugin
```

See [CLAUDE.md](CLAUDE.md) for the full authoring conventions (shared skill
architecture, subagent pairing rules, skill-specific notes).

## License

MIT. See plugin manifests for per-plugin metadata.
