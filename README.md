# souroldgeezer

Claude Code and Codex plugin marketplace by Sour Old Geezer. This repository
is the marketplace source and published plugin tree.

## What this is

The repo currently ships four plugins:

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `0.3.2` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | [docs/plugins/audit.md](docs/plugins/audit.md) |
| `souroldgeezer-design` | `1.0.0` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [responsive-design](souroldgeezer-design/skills/responsive-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md) | [docs/plugins/design.md](docs/plugins/design.md) |
| `souroldgeezer-architecture` | `0.1.0` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [docs/plugins/architecture.md](docs/plugins/architecture.md) |
| `souroldgeezer-ops` | `0.3.2` | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | [docs/plugins/ops.md](docs/plugins/ops.md) |

## Install

### Claude Code

Add the shared marketplace, then install the plugins you want:

```text
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
/plugin install souroldgeezer-architecture@souroldgeezer
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
    "souroldgeezer-ops@souroldgeezer": true
  }
}
```

### Codex

Codex reads the same shared marketplace at `.claude-plugin/marketplace.json`.
Add the marketplace, then install or enable the plugins from the plugin
browser:

```text
codex plugin marketplace add tommimarkus/skills
codex
/plugins
```

For local development, point Codex at the clone and refresh the installed copy
after changing plugin sources:

```text
codex plugin marketplace add /absolute/path/to/skills
codex
/plugins
```

After local plugin changes, restart Codex and reinstall the changed plugin from
`/plugins` if the session still shows an older materialized copy. `codex plugin
marketplace upgrade <name>` refreshes Git-backed marketplaces, not local clone
sources. Verify the installed cache under
`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` and confirm the
expected `skills/` directories are present.

Keep `.codex-plugin/plugin.json#interface.defaultPrompt` to three or fewer
entries.

## Local development

- Keep `.claude-plugin/marketplace.json` as the shared marketplace.
- Keep each plugin's Claude and Codex manifests synchronized on `name`,
  `version`, and `description`.
- Use the repo-local `uv` tooling for the skill architecture report.
- Use the validation script before asking for review.

## Examples

1. Audit a workflow or Dockerfile with `devsecops-audit`.
2. Review an API surface or extract an existing contract with `api-design`.
3. Review or extract an architecture model with `architecture-design`.

## Validation

Run these from the repo root:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
git diff --check
python -m unittest
```

## Detailed docs

- [docs/plugins/audit.md](docs/plugins/audit.md)
- [docs/plugins/design.md](docs/plugins/design.md)
- [docs/plugins/architecture.md](docs/plugins/architecture.md)
- [docs/plugins/ops.md](docs/plugins/ops.md)
- [docs/release-checklist.md](docs/release-checklist.md)
- [docs/skill-architecture.md](docs/skill-architecture.md)
