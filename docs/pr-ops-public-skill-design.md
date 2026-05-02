# PR Ops Public Skill Design

## Goal

Add a public `pr-ops` skill as a sibling to `issue-ops` in the
`souroldgeezer-ops` plugin. The skill should handle explicit pull-request
lifecycle work end to end without hardcoding GitHub-specific mechanics into the
always-loaded core.

## Decision

Create `souroldgeezer-ops/skills/pr-ops` with the same public-surface pattern
as `issue-ops`:

- Core skill: `souroldgeezer-ops/skills/pr-ops/SKILL.md`
- GitHub extension: `souroldgeezer-ops/skills/pr-ops/extensions/github.md`
- Extension convention: `souroldgeezer-ops/skills/pr-ops/extensions/README.md`
- Claude Code subagent: `souroldgeezer-ops/agents/pr-ops.md`
- Codex skill metadata: `souroldgeezer-ops/skills/pr-ops/agents/openai.yaml`
- Project-scoped Codex wrapper: `.codex/agents/pr-ops.toml`

Because this adds a new shipped skill, bump `souroldgeezer-ops` from `0.1.0` to
`0.2.0` across both plugin manifests and the shared marketplace entry.

## Core Skill Boundary

`pr-ops` owns explicit pull-request or merge-request lifecycle requests:
inspect, review, address feedback, inspect checks, update the branch, request
review, merge or close when authorized, and clean up work owned by the run.

The core remains provider-agnostic. It owns:

- mode selection and queue limits;
- live provider state and git state authority;
- local recovery ledger use;
- ask-vs-continue rules;
- review, check, branch-update, merge, and closure safety gates;
- verification inference and rerun guidance;
- completion output and disclosure fields.

The core excludes:

- incidental PR mentions;
- issue lifecycle closure, unless the user explicitly asks and `issue-ops`
  should be used or coordinated;
- standalone deep CI debugging, security audit, design review, or test-quality
  audit;
- general project-management advice.

## GitHub Extension Boundary

`extensions/github.md` owns GitHub-specific PR mechanics:

- repository, pull request, base/head, fork, branch, review, thread, comment,
  check, status, ruleset, and permission state resolution;
- GitHub MCP / `gh` / REST tooling order;
- visible lifecycle marker comments for long-running work;
- review-thread reply and resolution rules;
- check-run inspection and rerun boundaries;
- branch-update and push safety;
- merge, close, and branch cleanup safety;
- GitHub-specific escalation gates.

The extension must not replace the core authority, ask-vs-continue,
verification, escalation, ledger, or output contracts.

## Relationship To `issue-ops`

`pr-ops` and `issue-ops` are siblings. `pr-ops` handles PR state. When a PR is
linked to an issue, `pr-ops` reports issue implications but does not close or
complete issues unless the user explicitly asks for that work or a loaded
provider extension has a safe, explicit rule for it.

## Public Runtime Surfaces

The plugin description should expand from issue/work-item operations to issue,
work-item, and pull-request lifecycle operations.

The matching Claude Code subagent and Codex wrapper should be thin. They point
back to `pr-ops` as the source of truth, preserve the output footer, and avoid
duplicating GitHub mechanics.

Codex `interface.defaultPrompt` remains capped at three entries and should
include both `issue-ops` and `pr-ops` examples.

## Validation

Before finishing, run:

- `jq empty .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json`
- `uv run python -m unittest tests.skill_architecture_report_test`
- `uv run python scripts/skill_architecture_report.py --format json --strict .`
- `bash scripts/skill-architecture-report.sh .`
- `git diff --check`

Manual checks:

- Trigger quality: `pr-ops` triggers only for explicit PR lifecycle work.
- Context efficiency: GitHub mechanics live in the extension, not the core.
- Runtime parity: Claude Code and Codex surfaces describe the same capability.
- Release hygiene: version, manifests, marketplace entry, README, CLAUDE, AGENTS,
  subagent, wrapper, and `agents/openai.yaml` move together.

## Implementation Status

Implemented on branch `pr-ops-public-skill` via the companion plan in
[pr-ops-public-skill-implementation-plan.md](pr-ops-public-skill-implementation-plan.md).
