# PR Ops Provider Extensions

Provider extensions add pull-request provider mechanics to the core `pr-ops`
workflow. The core skill owns lifecycle authority, queue limits, ledger use,
ask-vs-continue rules, escalation, verification inference, merge/close
authorization, and completion output.

Extensions do not override those core contracts. They add provider state
resolution, tooling order, visible lifecycle markers, PR creation or reuse
mechanics, review-thread mechanics, check handling, branch-update mechanics,
provider-specific merge and close rules, and cleanup gates.

## Current Extensions

| File | Provider | Notes |
|---|---|---|
| [github.md](github.md) | GitHub™ | Pull requests, prepared branches, PR creation/reuse, reviews, review threads, comments, checks, branch protection, GitHub™ MCP / `gh` / REST routing, branch update, merge, close, and branch cleanup. |
| [gitlab.md](gitlab.md) | GitLab™ | Merge requests, prepared branches, MR creation/reuse, discussions, notes, approvals, pipelines, branch protection, GitLab™ integration / `glab` / REST routing, rebase, merge, close, and branch cleanup. |

## Required Sections

See [../../../docs/provider-reference/authoring.md](../../../docs/provider-reference/authoring.md);
the sections below are additions specific to this skill:

- **PR creation or reuse**: provider-specific prepared-branch, existing-PR, and
  branch-push mechanics.
- **Review and comment handling**: provider-specific review, thread, reply,
  resolve, and reviewer-request mechanics.
- **Check handling**: provider-specific status, check-run, annotation, rerun,
  and external-provider boundaries.
- **Branch update and push rules**: base/head refresh, fork, protected branch,
  push, force-push, and conflict handling.
- **Merge, close, and cleanup rules**: exact pre-merge refresh checks, merge
  method choice, close handling, and branch deletion safety.
