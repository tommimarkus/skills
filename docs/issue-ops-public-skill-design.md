# Issue Ops Public Skill Design

## Goal

Publish the current repo-internal GitHub issue lifecycle workflow as a public,
tracker-agnostic operations skill without hardcoding this repository's GitHub,
direct-main, or skill-authoring policy into the public core.

## Decision

Create a new plugin named `souroldgeezer-ops` and a public skill named
`issue-ops`.

The public skill uses a generic core plus provider extensions:

- Core skill: `souroldgeezer-ops/skills/issue-ops/SKILL.md`
- GitHub extension: `souroldgeezer-ops/skills/issue-ops/extensions/github.md`
- Claude Code subagent: `souroldgeezer-ops/agents/issue-ops.md`
- Codex skill metadata: `souroldgeezer-ops/skills/issue-ops/agents/openai.yaml`
- Project-scoped Codex wrapper: `.codex/agents/issue-ops.toml`

The existing repo-internal workflow at
`.claude/skills/github-issue-lifecycle/SKILL.md` remains as a local overlay or
compatibility wrapper. It should point to the public `issue-ops` skill and add
this repository's defaults: GitHub extension, `ip-hygiene`, fixed `.worktrees`
paths, direct-main integration when safe, skill-architecture verification, and
published plugin surface synchronization.

## Why A New Plugin

`issue-ops` is operational lifecycle work. It is not an audit rubric and not a
design/reference workflow.

Adding it to `souroldgeezer-audit` would mix read-oriented review skills with a
write-heavy workflow that comments on issues, changes branches, pushes commits,
and closes work items. Adding it to `souroldgeezer-design` would broaden a
design plugin into project management and repository operations. A dedicated
`souroldgeezer-ops` plugin keeps trigger metadata precise and avoids making
existing plugin descriptions noisier.

## Core Skill Boundary

`issue-ops` owns work-item lifecycle operation independent of a tracker vendor.
It should trigger when the user explicitly asks the agent to handle, triage,
resume, implement, close, or process one or more issues or work items end to
end.

The core must not contain GitHub-specific mechanics. It must not name GitHub
MCP, `gh`, REST endpoints, labels, milestones, projects, PR comments, or GitHub
issue comment markers except as examples of extension-owned behavior.

The core should exclude:

- Incidental issue mentions.
- Ordinary PR review.
- CI failure debugging as a standalone task.
- Security posture review.
- Design review.
- General project-management advice.

The core should define:

- Modes: `full-cycle`, `triage-only`, `plan-only`, `implement-only`, `resume`,
  and provider-specific integration modes exposed by loaded extensions.
- Queue limits: inspect and complete bounded counts per invocation, with oldest
  first after trivial priority sorting.
- Authority: live tracker state and live git state outrank local recovery
  hints.
- Local ledger contract: append-only recovery hints under a cache path, never
  committed and never containing secrets, raw logs, full issue bodies, or
  sensitive excerpts.
- Ask-vs-continue rules: continue when target, authority, permissions,
  worktree state, verification, and integration path are clear; ask only for
  global blockers.
- Escalation behavior: stop the affected item, record current status in the
  provider-visible lifecycle marker when available, and continue the queue when
  possible.
- Verification inference: read repo guidance, touched-surface docs, scripts,
  package metadata, CI workflows, and touched files before choosing commands.
- Completion output: concise counts for completed, escalated, skipped, and
  remaining items, plus verification summaries and global blockers.

## GitHub Extension Boundary

`extensions/github.md` owns GitHub-specific execution.

It should load when the repository remote, user wording, issue URL, or issue
identifier resolves to GitHub. It should say that it adds provider mechanics to
the core workflow and does not replace the core ask-vs-continue, escalation,
ledger, or verification contracts.

The GitHub extension should define:

- GitHub state resolution: issue state, comments, labels, assignees, linked PRs,
  repository identity, default branch, permissions, and current auth/tool
  routing.
- Tooling order: GitHub MCP when available and correctly routed, then `gh` CLI
  after auth and repository verification, then REST only when the first two are
  unavailable or insufficient.
- Lifecycle marker comment templates, including current-state-only comments and
  strict offset timestamps.
- Label, project, milestone, and assignee behavior: use existing taxonomy when
  obvious, treat projects and milestones as read-only unless explicitly asked,
  and do not create lifecycle labels.
- Integration strategies: PR-mode default for public use, direct-main only when
  user or repo guidance explicitly allows it and branch protection permits it.
- GitHub-specific escalation gates: wrong account, wrong repository, missing
  permission, unsafe existing PR state, concurrent actor markers, protected
  branch restrictions, public communication judgment, GitHub Actions permission
  or secret handling, push rejection, and local/CI disagreement.
- Issue close/update behavior: update lifecycle marker before closure, avoid a
  separate closing comment unless marker update fails.

## Repo-Internal Overlay

The internal `.claude/skills/github-issue-lifecycle/SKILL.md` should stop being
the canonical full workflow. It should become a narrow overlay:

1. Invoke or follow public `issue-ops`.
2. Load the GitHub extension.
3. Apply this repo's extra gates and defaults:
   - run `.claude/skills/ip-hygiene/SKILL.md` before implementing issue content
     that touches skill, agent, manifest, reference, or repo-documentation
     surfaces;
   - use `.worktrees/github-issue-lifecycle-main` and
     `.worktrees/issue-<number>` unless they are dirty or occupied;
   - allow direct-main integration for clearly actionable repo-maintenance
     issues when permissions and state are safe;
   - run the skill architecture report and relevant unit tests for published
     skill/plugin or repo-doc changes;
   - keep public plugin manifests, marketplace entry, README, CLAUDE, AGENTS,
     Claude subagent, Codex wrapper, and `agents/openai.yaml` synchronized.

This preserves the behavior that works well in this repository while making the
public skill safe for repositories with different branch policies.

## Public Runtime Surfaces

`souroldgeezer-ops` starts at version `0.1.0`.

Both plugin manifests and the shared marketplace entry must use the same name,
version, and description. The Codex manifest must include `"skills": "./skills/"`
and at most three `interface.defaultPrompt` entries.

Proposed plugin description:

> Operations skills for issue and work-item lifecycle handling, with a
> tracker-agnostic core and provider-specific extensions.

Proposed skill description:

> Use when the user explicitly asks to handle, triage, resume, implement, close,
> or process one or more issues or work items end to end; loads provider
> extensions such as GitHub only after the tracker is identified.

The matching Claude Code subagent and Codex wrapper should be thin. They should
point back to `issue-ops` as the source of truth, preserve the completion output
contract, and avoid duplicating provider-specific details.

## Progressive Disclosure

Keep the always-loaded `SKILL.md` compact. It should contain the ownership
boundary, mode selection, provider-extension selection, core flow, ask/continue
rules, escalation model, ledger contract, verification contract, and completion
output.

Move provider mechanics into `extensions/github.md`. If the GitHub extension
grows too large, split stable templates or sub-procedures into one-hop support
files under `references/` and link them from the extension with explicit load
conditions.

Do not create placeholder extensions for non-GitHub trackers in v1. The core
should be shaped so future `linear.md`, `jira.md`, or `azure-devops.md`
extensions can be added later, but v1 should ship only the GitHub extension.

## Validation

Before finishing implementation, run:

- `jq empty .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json`
- `uv run python -m unittest tests.skill_architecture_report_test`
- `uv run python scripts/skill_architecture_report.py --format json --strict .`
- `bash scripts/skill-architecture-report.sh .`
- `git diff --check`

Manual skill-architecture checks:

- Trigger quality: `issue-ops` activates for explicit lifecycle work and does
  not steal PR review, CI debugging, security audit, design review, or incidental
  issue mentions.
- Task-value lift: the skill changes decisions around authority, queue limits,
  lifecycle markers, escalation, integration, and verification beyond generic
  coding-agent behavior.
- Context efficiency: GitHub mechanics are not in the always-loaded core.
- Runtime parity: Claude Code and Codex surfaces describe the same public
  capability.
- Release hygiene: new plugin manifests, marketplace entry, README, CLAUDE,
  AGENTS if needed, subagent, wrapper, and Codex metadata land together.

## Open Follow-Up

After this spec is approved, write an implementation plan that creates the new
plugin and skill surfaces first, then migrates the internal GitHub workflow into
the public core plus GitHub extension without changing repository behavior.
