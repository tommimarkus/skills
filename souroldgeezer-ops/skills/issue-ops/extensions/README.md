# Issue Ops Provider Extensions

Provider extensions add tracker-specific mechanics to the core `issue-ops`
workflow. The core skill owns lifecycle authority, queue limits, ledger use,
ask-vs-continue rules, escalation, verification inference, integration handoff,
and completion output.

Extensions do not override those core contracts. They add provider state
resolution, tooling order, visible lifecycle markers, provider-specific issue
integration or PR-lifecycle handoff modes, metadata handling, closure rules,
and escalation gates.

## Current Extensions

| File | Provider | Notes |
|---|---|---|
| [github.md](github.md) | GitHub™ | Issues, lifecycle comments, MCP / `gh` / REST routing, `pr-ops` handoff, direct-main mode, linked pull requests, and closure safety. |
| [gitlab.md](gitlab.md) | GitLab™ | Issues, lifecycle notes, GitLab integration / `glab` / REST routing, `pr-ops` handoff limits, direct integration, linked issues, related merge requests, and closure safety. |

## Required Sections

See [../../../docs/provider-reference/authoring.md](../../../docs/provider-reference/authoring.md);
the sections below are additions specific to this skill:

- **Integration strategies**: provider-specific direct-commit, branch
  preparation, sibling PR-lifecycle handoff, or completion mechanics.
- **Metadata policy**: labels, projects, milestones, assignees, components, or
  equivalent tracker fields.
