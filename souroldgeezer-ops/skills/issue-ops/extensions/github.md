# GitHub Extension

Load this extension when the repository remote, issue URL, issue number,
provider tooling, or user wording identifies GitHub as the issue tracker.

This extension adds GitHub mechanics to `issue-ops`. It does not replace the
core authority, ledger, ask-vs-continue, escalation, verification, or completion
contracts.

## State Resolution

Resolve current GitHub state before acting:

1. Repository owner/name, default branch, current remote, and current local
   branch or worktree.
2. Issue state, title, body summary, labels, assignees, comments, linked pull
   requests, and visible lifecycle marker comments.
3. Authenticated account and write permissions for comments, branches, pull
   requests, and issue closure.
4. Branch protection or repository rules that affect direct pushes, required
   pull requests, and required checks.
5. Current git state, including dirty files, active worktrees, and whether an
   existing branch clearly owns the issue.

Treat GitHub and git as live authority. Do not rely on a local ledger or stale
prompt context without rechecking material facts.

## Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing and repository identity.
2. `gh` CLI after verifying `gh auth status` and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

If the selected route points at the wrong account or repository, escalate the
item.

## Lifecycle Comment

Every inspected GitHub issue gets a lifecycle marker unless the run lacks
comment permission. Update the latest marker from the same actor when possible.
Add a new comment only when editing is unavailable, editing would hide reply
context, or a fresh visible escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

Implementing state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: implementing

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Current step: working on an isolated branch
Disposition: actionable
Verification: pending
Last reviewed: 2026-05-02T12:00:00+03:00
```

Escalated state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: escalated

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Gate: unclear acceptance criteria
Evidence: issue comments conflict on the required behavior
Verification: not run
Last reviewed: 2026-05-02T12:00:00+03:00
```

Completed state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Result: merged pull request
Verification: passed - unit tests, repository checks, whitespace check
Resolution: implemented the issue request and verified the affected surface
Last reviewed: 2026-05-02T12:00:00+03:00
```

The final lifecycle marker update is sufficient before closing the issue. Do
not add a separate closing comment unless updating the marker fails.

## Integration Strategies

Default public integration strategy is `pr-mode`:

1. Create or reuse an issue-owned branch.
2. Commit focused work.
3. Push the branch.
4. Open or update a pull request.
5. Report the PR and verification state.
6. Close the issue only after merge, or when the user explicitly authorizes
   closure without merge.

Use `direct-main` only when the user or repository guidance explicitly allows
it, branch protection permits it, and live state is clean. In direct-main mode,
prefer one clean commit named `Fix #<number>: <title>` for defects or
`Resolve #<number>: <title>` otherwise.

Resume an existing pull request branch when one clearly owns the issue and is
safe to continue. Escalate on unsafe existing PR state, unclear ownership,
review conflict, or non-trivial branch history cleanup.

## Labels, Projects, Milestones, And Assignees

Use existing labels only when classification is obvious from the repository's
taxonomy. Do not create lifecycle labels.

Treat projects and milestones as read-only context unless the user explicitly
asks to change them. Assign or unassign users only when repository guidance or
the user explicitly requests it.

## GitHub Escalation Gates

Escalate the affected issue on:

- wrong account, wrong repository, missing permission, or unexpected GitHub
  tool routing;
- protected branch mismatch, required PR policy, required status checks, push
  rejection, or local/CI disagreement;
- existing PR with unclear ownership, active review disagreement, merge
  conflict, stale branch, or non-trivial history cleanup;
- concurrent lifecycle marker from another current actor;
- GitHub Actions permissions, workflow token handling, secret handling,
  repository settings, branch rules, or sensitive history cleanup;
- public comment text that rejects a request, assigns blame, makes a commitment,
  asks the reporter to do work, or exposes sensitive detail.

## Completion

Before completion or closure, re-read issue state, comments, lifecycle markers,
linked PR state, and branch/check state. Escalate instead of closing when late
comments, another actor marker, issue or PR state changes, branch drift, or
check changes alter integration or closure safety.

On completion, update the lifecycle marker before closing the issue. If a PR is
created or reused, report the PR URL or number in the final chat output. If the
issue remains open because merge has not happened, report the remaining state
instead of closing it.
