# GitHub Extension

Load this extension once a GitHub issue is the identified tracker — recognised
from a github.com issue URL or number, the repository remote, provider tooling,
or user wording. It adds GitHub issue mechanics to `issue-ops`; the shared GitHub
mechanics and the core-contract boundary live in the
[GitHub provider reference](../../../docs/provider-reference/github.md).

## State Resolution

Resolve current GitHub state before acting:

1. Repository owner/name, default branch, current remote, and current local
   branch or worktree.
2. Issue state, title, body summary, labels, assignees, comments, linked pull
   requests, and visible lifecycle marker comments.
3. Authenticated account and write permissions for issue comments, local branch
   preparation, and issue closure.
4. Branch protection or repository rules that affect direct integration or
   require a pull-request handoff.
5. Current git state, including dirty files, active worktrees, and whether an
   existing branch clearly owns the issue.

Treat GitHub and git as live authority. Do not rely on a local ledger or stale
prompt context without rechecking material facts.

## Tooling Order

Apply [../../../docs/provider-reference/github.md § Tooling Order](../../../docs/provider-reference/github.md#tooling-order).

## Lifecycle Comment

Every inspected GitHub issue gets a lifecycle marker. Apply
[../../../docs/provider-reference/github.md § Lifecycle Marker Mechanics](../../../docs/provider-reference/github.md#lifecycle-marker-mechanics),
then write the `issue-ops` marker:

Implementing state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: implementing

Actor: Claude Code
Mode: full-cycle
Integration: pr-ops handoff
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

Actor: Claude Code
Mode: full-cycle
Integration: pr-ops handoff
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

Actor: Claude Code
Mode: full-cycle
Integration: pr-ops handoff
Scope: #123
Result: delegated pr-ops merged PR #456
Verification: passed - unit tests and delegated PR checks
Resolution: implemented the issue request, delegated PR lifecycle, and verified issue closure safety
Last reviewed: 2026-05-02T12:00:00+03:00
```

## Integration Strategies

Default public integration strategy is `pr-ops-handoff`:

1. Create or reuse an issue-owned branch.
2. Commit focused work.
3. Run issue-level local verification.
4. Hand off to `pr-ops` with repository identity, base branch, prepared branch,
   linked issue, lifecycle marker context, and local verification summary.
5. Let `pr-ops` push, create or reuse the pull request, handle PR checks and
   reviews, merge when authorized and safe, and clean PR-owned work areas.
6. Re-read the issue after `pr-ops` reports a merged pull request, then close
   only when live issue state is still safe. Close without merge only when the
   user explicitly authorizes closure without merge.

Use `direct-main` only when the user or repository guidance explicitly allows
it, branch protection permits it, and live state is clean. In direct-main mode,
prefer one clean commit named `Fix #<number>: <title>` for defects or
`Resolve #<number>: <title>` otherwise.

When an existing linked pull request or issue branch clearly owns the issue,
handoff that target to `pr-ops` instead of assessing PR checks, reviews, branch
updates, merge safety, or PR cleanup in `issue-ops`. Escalate only when no
safe issue-side handoff target can be identified.

## Labels, Projects, Milestones, And Assignees

Use existing labels only when classification is obvious from the repository's
taxonomy. Do not create lifecycle labels.

Treat projects and milestones as read-only context unless the user explicitly
asks to change them. Assign or unassign users only when repository guidance or
the user explicitly requests it.

## GitHub Escalation Gates

Also apply the shared gates in
[../../../docs/provider-reference/github.md § Shared Escalation Gates](../../../docs/provider-reference/github.md#shared-escalation-gates).
Escalate the affected issue additionally on:

- protected branch mismatch that prevents both direct integration and
  `pr-ops` handoff;
- existing linked pull request or issue branch with unclear issue ownership.

## Completion

Before completion or closure, re-read issue state, comments, lifecycle markers,
linked pull requests, and the delegated `pr-ops` result. Escalate instead of
closing when late comments, another actor marker, issue state changes, or a
non-merged or escalated PR result alters closure safety.

On completion, update the lifecycle marker before closing the issue. If `pr-ops`
created, reused, or merged a pull request, report the PR URL or number in the
final chat output. If the issue remains open because the delegated PR lifecycle
did not merge, report the remaining state instead of closing it.
