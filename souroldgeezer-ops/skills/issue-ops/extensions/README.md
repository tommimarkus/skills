# Issue Ops Provider Extensions

Provider extensions add tracker-specific mechanics to the core `issue-ops`
workflow. The core skill owns lifecycle authority, queue limits, ledger use,
ask-vs-continue rules, escalation, verification inference, integration handoff,
and completion output.

Extensions do not override those core contracts. They add provider state
resolution, tooling order, visible lifecycle markers, provider-specific
integration modes, metadata handling, closure rules, and escalation gates.

## Current Extensions

| File | Provider | Notes |
|---|---|---|
| [github.md](github.md) | GitHub™ | Issues, lifecycle comments, MCP / `gh` / REST routing, PR-mode, direct-main mode, linked pull requests, checks, and closure safety. |

## Required Sections

Each provider extension is a single markdown file in this directory with:

- **Load condition**: which URLs, remotes, identifiers, tooling, or user wording
  identify this tracker.
- **State resolution**: the live tracker and local git facts to inspect before
  acting.
- **Tooling order**: provider integrations in preferred order, with auth and
  repository-identity checks.
- **Lifecycle marker or status model**: how visible progress is written, edited,
  or skipped when permission is missing.
- **Integration strategies**: provider-specific PR, direct-commit, branch,
  merge, or completion mechanics.
- **Metadata policy**: labels, projects, milestones, assignees, components, or
  equivalent tracker fields.
- **Escalation gates**: provider-specific stale-state, permission, concurrent
  actor, public-comment, and closure-safety stops.
- **Completion rules**: exact pre-close refresh checks and final reporting
  requirements.

Add a new provider extension only when the provider has enough lifecycle
mechanics to keep out of the always-loaded core skill. Keep public platform
claims anchored to official provider documentation when they are not obvious
from live tooling behavior.
