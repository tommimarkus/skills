# souroldgeezer

Cross-runtime plugin marketplace by Sour Old Geezer. The same skill workflows run in Claude Code™, Codex, and Antigravity / Gemini CLI (`agy`), with native GitHub™ Copilot CLI support for the architecture plugin.

Published plugins package shared skills with their on-demand references,
extensions, and evaluation evidence for supported runtimes. Host manifests,
marketplaces, agents, hooks, and MCP adapters provide runtime packaging around
those shared workflows. Repo-only authoring workflows live under
`internal-skills/` and are not published in the marketplaces.

## What this is

Install the plugin that owns the task, then describe the work in ordinary language. Start with [using skills](docs/using-skills.md) for task examples and boundaries, or use [runtime support](docs/runtime-support.md) for host behaviour.

The repo currently ships five plugins:

The workflows use judgment-led defaults: preserve compatible project contracts,
read guidance relevant to the decision, and scale preparation and checks to the
consequences. Reports give the result, useful evidence, and material limits;
detailed classifications remain available for explicit requests and consumers.

`planning-policy` follows the consuming repository's initialized scope. Standard
work uses a proportionate approach: settled authorized implementation may proceed
inline, explicit plan-first requests retain approval, and delegation is selected
when parallelism, isolation, or independent analysis warrants it. Necessary
adjacent work stays within the approved outcome under parent review. Material
scope/authority changes and risk-based independent review remain explicit. See
the [shared workflow](souroldgeezer-policy/skills/planning-policy/references/core-workflow.md).

Explicit `workflow: strict` retains validated v5 plans, exact capability
bindings, managed workers, ledger recovery, changeset budgets, pin scans, and
per-leaf verification. Path `precision` is a separate v5 setting; existing
approved plans and runs retain their recorded settings. New unpinned runs may
use available suitable executors through existing explicit capability bindings. Tier mix and execution
cost findings are advisory in both workflows; detailed forecasts and tracing
are opt-in. See the [strict workflow](souroldgeezer-policy/skills/planning-policy/references/strict-workflow.md),
[worker handoff](souroldgeezer-policy/skills/planning-policy/references/worker-handoff.md),
and [legacy compatibility](souroldgeezer-policy/skills/planning-policy/references/ledger-compatibility.md).

`software-design` includes a narrow File Edit lane for bounded non-code text or
data changes that need no code/module, API/schema, IaC, security, test, or
other sibling-owned decision. It validates the named content operation directly
and returns before loading normal design guidance.

`tdd-policy` measures observable behavior at a declared seam, by default each
module's public API. An internal refactor or trivial wiring therefore adds no
test, a scaffold test below the seam is rewritten at the seam or deleted before
GREEN lands, and removing a behavior removes its tests in the same change. Tests
that a behavior-preserving refactor had to edit are listed as
`structure-coupled`, which `test-quality-audit` reads as `verify-then-retire`
evidence, never as grounds for deletion on its own.

`tdd-policy` stays stack-neutral about how a test is written: tests reuse the
suite's shared helpers, share only immutable setup, avoid fixed sleeps and real
clocks, give the same result under any machine locale or timezone, and run RED
under a value that can actually fail. It hands language idioms to
`software-design` by skill name, whose per-stack test-code lane covers shared
test support, setup lifetime, time and locale control, parallel runs, lanes, and
per-test durations; test adequacy stays with `test-quality-audit`.

`software-design` owns general [data-efficiency](souroldgeezer-design/docs/design-reference/data-efficiency.md) mechanics; `api-design` applies
the shared procedure to HTTP-to-storage access paths, including query shaping,
resource lifetime, and API-owned amplification findings.

The design skills treat a long operation as a user-facing contract: known slow
work is acknowledged, background status stays discoverable, measured progress
is distinct from unknown work, and completion means the result is usable. CLI
and agent adapters preserve their data channels and disclose host limits rather
than fabricating status.

Delegated Deep/in-depth audits establish their population from authoritative
item enumeration and reconcile returned identities and counts; see the shared
[scaled-audit procedure](souroldgeezer-audit/docs/audit-reference/scaled-audit.md).

| Plugin | Version | Skills | Docs |
|---|---:|---|---|
| `souroldgeezer-audit` | `2026.10.22` | [devsecops-audit](souroldgeezer-audit/skills/devsecops-audit/SKILL.md), [test-quality-audit](souroldgeezer-audit/skills/test-quality-audit/SKILL.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md), [lean-audit](souroldgeezer-audit/skills/lean-audit/SKILL.md) | [audit-craft core](souroldgeezer-audit/docs/audit-reference/audit-craft.md), [security](souroldgeezer-audit/docs/security-reference/devsecops.md), [quality](souroldgeezer-audit/docs/quality-reference/unit-testing.md), [ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md) |
| `souroldgeezer-design` | `2026.10.3` | [software-design](souroldgeezer-design/skills/software-design/SKILL.md), [app-design](souroldgeezer-design/skills/app-design/SKILL.md), [api-design](souroldgeezer-design/skills/api-design/SKILL.md), [infra-design](souroldgeezer-design/skills/infra-design/SKILL.md) | [software](souroldgeezer-design/docs/software-reference/software-design.md), [app](souroldgeezer-design/docs/app-reference/app-design.md), [api](souroldgeezer-design/docs/api-reference/api-design.md), [infra](souroldgeezer-design/docs/infra-reference/infra-design.md) |
| `souroldgeezer-architecture` | `2026.10.4` | [architecture-design](souroldgeezer-architecture/skills/architecture-design/SKILL.md) | [architecture](souroldgeezer-architecture/docs/architecture-reference/architecture.md) |
| `souroldgeezer-policy` | `2026.10.22` | [git-workflow-policy](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release-policy](souroldgeezer-policy/skills/release-policy/SKILL.md), [tdd-policy](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning-policy](souroldgeezer-policy/skills/planning-policy/SKILL.md), [scope-policy](souroldgeezer-policy/skills/scope-policy/SKILL.md) | [git workflow](souroldgeezer-policy/skills/git-workflow-policy/SKILL.md), [release](souroldgeezer-policy/skills/release-policy/SKILL.md), [TDD](souroldgeezer-policy/skills/tdd-policy/SKILL.md), [planning](souroldgeezer-policy/skills/planning-policy/SKILL.md), [scope](souroldgeezer-policy/skills/scope-policy/SKILL.md) |
| `souroldgeezer-ops` | `2026.10.2` | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) | [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md), [pr-ops](souroldgeezer-ops/skills/pr-ops/SKILL.md) |

Testing guidance judges distinct observable obligations across the suite,
permits bounded readiness synchronization, and preserves the configured runner
for repeated-run comparisons. Local performance budgets are valid within their
declared scope; unqualified timing increases do not create new budget breaches.

## Install

### Claude Code

Run these in Claude Code. Add the marketplace, then install the plugins you need:

```text
/plugin marketplace add tommimarkus/skills
/plugin install souroldgeezer-audit@souroldgeezer
/plugin install souroldgeezer-design@souroldgeezer
/plugin install souroldgeezer-architecture@souroldgeezer
/plugin install souroldgeezer-policy@souroldgeezer
/plugin install souroldgeezer-ops@souroldgeezer
```

For local development, merge this configuration into `~/.claude/settings.json`
using the absolute path of your task checkout:

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

Run these in a terminal, selecting the plugins you need:

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

### Antigravity / Gemini CLI

Install individual plugins directly from GitHub or a local checkout:

```bash
agy plugin install https://github.com/tommimarkus/skills/tree/main/souroldgeezer-audit
agy plugin install https://github.com/tommimarkus/skills/tree/main/souroldgeezer-design
agy plugin install https://github.com/tommimarkus/skills/tree/main/souroldgeezer-architecture
agy plugin install https://github.com/tommimarkus/skills/tree/main/souroldgeezer-policy
agy plugin install https://github.com/tommimarkus/skills/tree/main/souroldgeezer-ops
```

For local checkout registration without copying, add an `entries` item in `~/.gemini/config/plugins.json` (or `.agents/plugins.json`) pointing at the repository root with `include_only` listing the plugins you want enabled.

### Dediren runtime (architecture plugin only)

`architecture-design` provisions its pinned, checksum-verified Dediren bundle when the host first lists its tools. The pin is Dediren **2026.10.0**. Since 2026.09.0, generated layouts use `layout-result.schema.v3` with typed edge routes; regenerate stored layouts and migrate consumers of edge `points`. Authored models and render policies remain compatible. Java™ 21+ is the normal prerequisite. The [Dediren runtime guide](souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md) covers air-gapped hosts, overrides, and failures.

Architecture Review preserves original source and artifacts as review evidence. When a build is needed, it uses one retained isolated copy; a successful rebuild does not clear stale or missing originals.

## Local development

Use the [contributor guide](docs/contributing.md) for a persistent task worktree, validation, and release boundaries. Its [maintenance procedures](docs/maintenance-procedures.md) cover rare runtime operations.

Security reports, response targets, and supported versions are in the
[security policy](SECURITY.md). The [security baseline](docs/security-baseline.md)
documents the marketplace threat model, local-publication control, OWASP SCVS
Level 1 target and current gaps. Private vulnerability reporting is the chosen
channel, but its enablement is pending and must not be represented as live until
it is verified on GitHub.

Lean Audit reports explicit requested-scope coverage for normal Markdown scans and treats an empty eligible scope as an input error. Its workflow forecast reports `indeterminate` until its declared core budget evidence is complete, except when known expected usage already proves an overflow.
Intentional clone regions preserve detection between unmarked copies. The sole
default Stop notice reports reference defects and advisory inventory/cost changes
without blocking completion. Lesson capture is explicitly invoked; names and counts
do not establish semantic fidelity. Trace totals include provider-specific cache input.

## Examples

- “Review this API for inconsistent error responses” loads `api-design`.
- “Audit this pull request’s test suite” loads `test-quality-audit`.
- “Our suite takes an hour; plan how to get it under ten minutes” loads `test-quality-audit` in Deep mode with its propose-only recovery program.
- “Create a user-flow and responsive layout for this dashboard” loads `app-design`.
- “Prepare this issue for implementation” loads `issue-ops`.

Each skill’s expected output and boundaries are in [using skills](docs/using-skills.md).

## Validation

The [contributor guide](docs/contributing.md#validate-the-change) defines focused
local checks and the full cross-cutting candidate sequence. Fragmentation owns
metadata parity. Full-suite and isolated host verification remain mandatory for
cross-cutting changes and publication, rather than every bounded prose edit.
Local evidence is reused according to its actual scope; publication still needs
an exact clean commit/tree receipt, with only the documented atomic version-only
follow-up. The [release checklist](docs/release-checklist.md) covers that boundary.

## Detailed docs

- [Using skills](docs/using-skills.md): task selection, examples, outputs, and boundaries.
- [Runtime support](docs/runtime-support.md): supported hosts, adapters, hooks, and Dediren.
- [Contributor guide](docs/contributing.md): local setup and validation.
- [Security policy](SECURITY.md): private reporting status, supported versions, and response targets.
- [Security baseline](docs/security-baseline.md): threats, controls, assurance targets, and residual risks.
- [Skill architecture standard](docs/skill-architecture.md): authoring and review judgment.
- [Privacy policy](PRIVACY.md) and [terms](TERMS.md).
