# PR Ops Provider Extensions

Provider extensions add pull-request provider mechanics to the core `pr-ops`
workflow. The core skill owns lifecycle authority, queue limits, ledger use,
ask-vs-continue rules, escalation, verification inference, merge/close
authorization, and completion output.

Extensions do not override those core contracts. They add provider state
resolution, tooling order, visible lifecycle markers, review-thread mechanics,
check handling, branch-update mechanics, provider-specific merge and close
rules, and cleanup gates.

## Current Extensions

| File | Provider | Notes |
|---|---|---|
| [github.md](github.md) | GitHub™ | Pull requests, reviews, review threads, comments, checks, branch protection, GitHub™ MCP / `gh` / REST routing, branch update, merge, close, and branch cleanup. |

## Required Sections

Each provider extension is a single markdown file in this directory with:

- **Load condition**: which URLs, remotes, identifiers, tooling, or user wording
  identify this provider.
- **State resolution**: the live provider and local git facts to inspect before
  acting.
- **Tooling order**: provider integrations in preferred order, with auth and
  repository-identity checks.
- **Lifecycle marker or status model**: how visible progress is written, edited,
  or skipped when permission is missing or public noise would be excessive.
- **Review and comment handling**: provider-specific review, thread, reply,
  resolve, and reviewer-request mechanics.
- **Check handling**: provider-specific status, check-run, annotation, rerun,
  and external-provider boundaries.
- **Branch update and push rules**: base/head refresh, fork, protected branch,
  push, force-push, and conflict handling.
- **Merge, close, and cleanup rules**: exact pre-merge refresh checks, merge
  method choice, close handling, and branch deletion safety.
- **Escalation gates**: provider-specific stale-state, permission, concurrent
  actor, public-comment, check, review, and merge-safety stops.
- **Completion rules**: final refresh checks and final reporting requirements.

Add a new provider extension only when the provider has enough lifecycle
mechanics to keep out of the always-loaded core skill. Keep public platform
claims anchored to official provider documentation when they are not obvious
from live tooling behavior.
