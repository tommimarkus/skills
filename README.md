# souroldgeezer

Claude Code plugin marketplace by Sour Old Geezer. Currently ships two plugins:

- **souroldgeezer-audit** — rubric-driven audits for DevSecOps posture and
  test quality, with per-stack extensions and matching subagents.
- **souroldgeezer-design** — reference-driven responsive UI design in build,
  review, and lookup modes, enforcing WCAG 2.2 AA, internationalization
  (LTR + RTL + text expansion), and Core Web Vitals, with a Blazor
  WebAssembly extension and a matching subagent.

## Install

Add this marketplace and enable the plugins you want:

```
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
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
    "souroldgeezer-audit@souroldgeezer": true,
    "souroldgeezer-design@souroldgeezer": true
  }
}
```

## What's in `souroldgeezer-audit`

Two audit skills, each with a matching one-shot subagent:

| Skill | Audits | Stack extensions |
|---|---|---|
| [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | Pipelines, IaC, release artifacts, code-level security smells | [bicep](souroldgeezer-audit/skills/devsecops-audit/extensions/bicep.md), [dockerfile](souroldgeezer-audit/skills/devsecops-audit/extensions/dockerfile.md), [dotnet-security](souroldgeezer-audit/skills/devsecops-audit/extensions/dotnet-security.md), [github-actions](souroldgeezer-audit/skills/devsecops-audit/extensions/github-actions.md) |
| [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | Unit, integration, and E2E test quality (dispatches on detected test type) | [dotnet-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [dotnet-core](souroldgeezer-audit/skills/test-quality-audit/extensions/dotnet-core.md); [nodejs-unit / integration / e2e](souroldgeezer-audit/skills/test-quality-audit/extensions/) on a shared [nodejs-core](souroldgeezer-audit/skills/test-quality-audit/extensions/nodejs-core.md) |

Subagents live alongside in [souroldgeezer-audit/agents/](souroldgeezer-audit/agents/)
and invoke the same skills, making them usable as delegated one-shots.

## What's in `souroldgeezer-design`

One design skill with a matching one-shot subagent:

| Skill | Covers | Stack extensions |
|---|---|---|
| [responsive-design](souroldgeezer-design/skills/responsive-design/SKILL.md) | Modern responsive web UI in HTML / CSS / JS — enforces WCAG 2.2 AA, internationalization (LTR + RTL + text expansion), and Core Web Vitals (LCP / CLS / INP) as hard baselines | [blazor-wasm](souroldgeezer-design/skills/responsive-design/extensions/blazor-wasm.md) (covers both standalone Blazor WebAssembly and Blazor Web App `.Client` hosting) |

Reference lives at [souroldgeezer-design/docs/ui-reference/responsive-design.md](souroldgeezer-design/docs/ui-reference/responsive-design.md).
The matching subagent is at [souroldgeezer-design/agents/responsive-design.md](souroldgeezer-design/agents/responsive-design.md).

## How the audits work

- **Rubric-driven.** The skills are *workflows* that apply an external rubric.
  Findings cite smell codes (e.g. `DSO-HC-2`, `HC-1`, `dotnet.I-HC-A1`); the prose
  lives in the rubric, not in the skill.
- **Rubric ships with the plugin.** No setup in the audited repo required. The
  rubric docs live at:
  - [souroldgeezer-audit/docs/security-reference/devsecops.md](souroldgeezer-audit/docs/security-reference/devsecops.md) for `devsecops-audit`
  - [souroldgeezer-audit/docs/quality-reference/unit-testing.md](souroldgeezer-audit/docs/quality-reference/unit-testing.md) (and siblings for integration / E2E) for `test-quality-audit`

  The skill reads these by relative path from its own location, so they travel
  with the installed plugin.
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

## How `responsive-design` works

- **Reference-driven.** Like the audit skills, it's a workflow that applies
  an external reference. Output cites reference sections (e.g. `§3.11`,
  `§5.8`) and WCAG Success Criteria (e.g. `SC 1.4.10`, `SC 2.5.8`); the
  prose lives in the reference, not in the skill.
- **Three modes.** **Build** produces code embodying the reference's
  decision defaults. **Review** walks the §7 checklist and emits per-finding
  output. **Lookup** answers a narrow question with a citation. If the
  request is ambiguous, the skill asks.
- **Verification-layer tags.** Every §7 checklist item carries a tag —
  `[static]` (grep / lint), `[dom]` (DevTools / Playwright), `[behaviour]`
  (keyboard / focus / interaction), `[visual]` (RTL / theme / zoom /
  non-Latin), `[a11y-tool]` (axe / Pa11y / Lighthouse), `[runtime]`
  (RUM / CrUX / Lighthouse-CI). The skill never claims a runtime
  Core Web Vitals pass from a static review.
- **Project assimilation — one-way.** Used in an existing project, the
  skill pulls the project *up to* the reference. New code is always
  reference-compliant; compliant existing infrastructure is reused;
  non-compliant infrastructure is flagged as legacy debt, never silently
  extended.
- **Per-stack extensions.** `blazor-wasm` covers both standalone Blazor
  WebAssembly and Blazor Web App `.Client` projects, plus component-library
  reuse rules (MudBlazor / FluentUI Blazor / Radzen / Blazorise — reuse
  conditional on each library's primitive actually satisfying the
  reference rule it would replace).
- **Disclosure footer.** Every output ends with a footer listing which
  extensions loaded, self-check counts by verification layer,
  project-assimilation summary (tokens reused, legacy debt flagged,
  migrations performed), and the reference path.

## Repository layout

```
.claude-plugin/marketplace.json    # marketplace manifest (lists plugins)
souroldgeezer-audit/               # audit plugin
  .claude-plugin/plugin.json
  docs/                            # bundled rubrics
    security-reference/            # devsecops.md
    quality-reference/             # unit / integration / e2e-testing.md
  agents/*.md                      # subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                       # workflow
    extensions/                    # per-stack smell packs
    references/                    # smell catalog + reusable procedures
    config.yaml                    # optional, skill-specific
souroldgeezer-design/              # design plugin
  .claude-plugin/plugin.json
  docs/ui-reference/               # bundled reference (responsive-design.md)
  agents/*.md                      # subagents
  skills/<name>/
    SKILL.md                       # workflow
    extensions/                    # per-stack packs (primitives + patterns + project-assimilation)
undecided/                         # skills not yet assigned to a plugin — NOT production-ready;
                                   # do not reference from published skills
```

See [CLAUDE.md](CLAUDE.md) for the full authoring conventions (shared skill
architecture, subagent pairing rules, skill-specific notes).

## Attribution

Developed with assistance from [Claude](https://www.anthropic.com/claude)
(Anthropic) via [Claude Code](https://claude.com/claude-code). Per-commit
co-authorship trailers are intentionally omitted — this repo-wide acknowledgement
covers the contribution.

## License

MIT. See plugin manifests for per-plugin metadata.
