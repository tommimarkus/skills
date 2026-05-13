---
name: issue-ops
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more issues or work items end to end; loads provider extensions such as GitHub™ or GitLab™ only after the tracker is identified.
---

# Issue Ops

Use only for explicit issue or work-item lifecycle requests. Do not use for
incidental issue mentions, ordinary PR review, standalone CI debugging,
security posture review, design review, or general project-management advice.

Before acting on a real lifecycle, read
[`references/core-workflow.md`](references/core-workflow.md). When editing this
skill's triggers, behavior, provider handoff rules, source grounding, or evals,
also read `references/evals` and `references/source-grounding.md`.

## Provider

Identify the tracker from the issue URL, repo remote, configured tooling, issue
identifier, or user wording.

- GitHub: read [`extensions/github.md`](extensions/github.md) before resolving
  or writing provider state.
- GitLab: read [`extensions/gitlab.md`](extensions/gitlab.md) before resolving
  or writing provider state.
- New providers follow [`extensions/README.md`](extensions/README.md).
- If the provider is unknown, ask one concise tracker/repository question.
- If the provider is known but unsupported, stop and report the missing
  extension.

## Mode

Default to `full-cycle`: inspect the item or queue, record lifecycle state when
supported, implement actionable work, verify locally, delegate PR/MR lifecycle
work to `pr-ops` when needed, update status, and close or complete the item
when allowed.

Use narrower modes only when requested: `triage-only`, `plan-only`,
`implement-only`, or `resume`. Provider modes add mechanics; they do not replace
the core authority, escalation, ledger, verification, handoff, or completion
contracts.

## Core Rules

- Inputs: before acting, inspect the requested scope, issue/work-item
  IDs or URLs, repository identity and remotes, repo guidance, git branch,
  status, worktrees, provider tooling/auth, linked work, and existing lifecycle
  markers.
- Evidence contract: final output must disclose the inspected provider state,
  git state, provider extension, integration strategy, lifecycle-marker state,
  and verification run or blocker.
- Live tracker state and live git state are authoritative.
- For one invocation, complete at most 10 items, inspect at most 25 items, and
  inspect each queued item at most once during initial triage.
- Use `.cache/issue-ops/ledger.jsonl` only as an uncommitted recovery hint; do
  not store secrets, raw tracker text, logs, or sensitive excerpts in it.
- Continue autonomously only when target, repo, provider tooling, permissions,
  work area, verification, and integration or handoff path are all clear.
- Escalate item-local ambiguity through the provider when possible and continue
  the queue; ask the user only for global blockers.
- Implement only clear, in-scope work and auto-fix only deterministic formatter,
  generated-file, or lint failures.
- Delegate pull-request or merge-request creation, updates, checks, reviews,
  merge, and cleanup to `pr-ops`.
- Direct integration requires safe refreshed live state and rerun verification
  whenever the base branch or tested result changes.

End with the output footer from `references/core-workflow.md`. Do not write a
separate local summary file.
