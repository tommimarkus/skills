# GitHub Extension

Load this extension when the repository remote, pull request URL, PR number,
provider tooling, or user wording identifies GitHub as the PR provider.

This extension adds GitHub mechanics to `pr-ops`. It does not replace the core
authority, ledger, ask-vs-continue, escalation, verification, merge/close
authorization, or completion contracts.

## State Resolution

Resolve current GitHub PR state before acting:

1. Repository owner/name, default branch, current remote, and current local
   branch or worktree.
2. PR state, title, body summary, draft flag, author, labels, assignees,
   requested reviewers, linked issues, visible lifecycle marker comments, and
   existing review state.
3. Base repository/branch/SHA and head repository/branch/SHA, including fork
   status and whether the current user can push to the head branch.
4. Review comments, review threads, PR comments, unresolved conversations, and
   latest reviews by reviewer.
5. Status checks, check runs, required checks, pending checks, skipped checks,
   cancelled checks, annotations when available, and external-provider detail
   URLs.
6. Branch protection or repository rules that affect pushes, branch updates,
   review requirements, required checks, merge queue, merge methods, and branch
   deletion.
7. Current git state, including dirty files, active worktrees, and whether an
   existing branch clearly owns the PR.

Treat GitHub and git as live authority. Do not rely on a local ledger, stale
prompt context, or earlier check output without rechecking material facts.

## Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing and repository identity.
2. `gh` CLI after verifying `gh auth status` and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

If the selected route points at the wrong account or repository, escalate the
PR.

## Lifecycle Comment

For long-running write work, add or update a PR lifecycle marker unless the run
lacks comment permission or the user asked for read-only review. Update the
latest marker from the same actor when possible. Add a new comment only when
editing is unavailable, editing would hide reply context, or a fresh visible
escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

Working state:

```md
<!-- pr-ops:github:v1 -->
Lifecycle status: working

Actor: Codex
Mode: full-cycle
Scope: PR #123
Current step: addressing review feedback
Review state: requested changes
Checks: failing - unit tests
Verification: pending
Last reviewed: 2026-05-02T12:00:00+03:00
```

Escalated state:

```md
<!-- pr-ops:github:v1 -->
Lifecycle status: escalated

Actor: Codex
Mode: full-cycle
Scope: PR #123
Gate: unresolved requested changes
Evidence: latest human review still requests changes after branch refresh
Checks: not run
Verification: not run
Last reviewed: 2026-05-02T12:00:00+03:00
```

Completed state:

```md
<!-- pr-ops:github:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: merge-only
Scope: PR #123
Result: merged pull request
Review state: approved
Checks: passed - required checks green
Verification: passed - repository checks
Last reviewed: 2026-05-02T12:00:00+03:00
```

The final lifecycle marker update is sufficient before merge or close. Do not
add a separate completion comment unless updating the marker fails or the user
explicitly asks for a public summary.

## Review And Comment Handling

Distinguish PR comments, reviews, review threads, inline review comments, and
check annotations. Reply in the same review thread when addressing an inline
review comment. Do not answer inline feedback as a top-level PR comment unless
thread replies are unavailable.

Treat review states as live merge gates:

- `REQUEST_CHANGES` from a current human reviewer blocks merge until superseded
  by approval, dismissed by an authorized human, or explicitly overridden by the
  user with clear authority.
- Unresolved conversations block merge unless repository guidance says they are
  advisory and the requested action is complete.
- Bot or automated review comments are actionable when they point to concrete
  repo-local defects; otherwise classify them as advisory or escalate.

Resolve review threads only after the fix is present, verified, and a same-thread
reply records the action. Do not dismiss reviews unless the user explicitly asks
and the selected GitHub route proves the actor has permission.

Request reviewers only when the user or repository guidance asks for review, or
when the PR was updated and the existing reviewer set is clearly the correct
audience. Do not create or alter CODEOWNERS, labels, projects, milestones, or
assignees unless explicitly asked.

## Check Handling

Inspect combined status, check runs, required checks, and recent check details
before classifying the PR.

Fix only clear in-repo failures: deterministic formatting, lint, compile, unit,
integration, generated-file, or narrow test failures with enough logs to
identify the repository-owned defect. Escalate external-provider failures,
missing logs, unknown required checks, infrastructure outages, flaky
non-reproducible failures, permission failures, and failures that require
secrets or third-party service access.

Rerun checks only when the provider route supports it, the check is safe to
rerun, and repository guidance or the user allows reruns. Never claim remote
checks are green from local verification alone.

## Branch Update And Push

Prefer the PR's existing head branch when it clearly owns the work and is safe
to update. Create a local worktree or branch only when needed to inspect, test,
or patch the PR.

Before pushing or updating:

1. Re-read PR state, base/head SHA, reviews, comments, checks, lifecycle
   markers, branch protection, and mergeability.
2. Confirm the local branch descends from the current PR head or that the update
   strategy is explicitly authorized.
3. Confirm no other current actor owns the lifecycle marker or active branch
   work.

Use GitHub's branch update operation or merge base into the PR branch only when
safe and non-destructive. Rebase, force-push, branch recreation, and non-trivial
history cleanup require explicit user authorization.

Escalate on fork permission ambiguity, push rejection, merge conflict, protected
head branch mismatch, stale branch with active reviewer discussion, or local and
remote SHA disagreement.

## Merge, Close, And Cleanup

Merge or close only when the user requested or authorized it and live state is
safe.

Before merge, re-read PR state, base/head SHA, draft state, mergeability,
reviews, unresolved conversations, required checks, check conclusions, branch
protection, merge queue state, lifecycle markers, and linked issues. Escalate
instead of merging when any required check is failed, pending, missing, skipped
without documented allowance, or unknown; when requested changes remain current;
when the PR is draft; when conversations are unresolved; when branch protection
or merge queue requirements are unclear; or when late comments alter safety.

Use the repository's documented merge method. If no method is documented, use
the provider default only when the user explicitly asked to merge and the route
does not require selecting a method. Do not squash, rebase, or edit commit
messages to change history semantics unless requested.

Close without merge only when the user explicitly asks, the PR is obsolete or
superseded by live evidence, or repository guidance defines a safe close rule.
Do not delete the remote head branch unless it is owned by this run or the user
explicitly authorizes deletion. Local branch and worktree cleanup is allowed
only for work areas owned by this run.

## GitHub Escalation Gates

Escalate the affected PR on:

- wrong account, wrong repository, missing permission, or unexpected GitHub
  tool routing;
- protected branch mismatch, required PR policy, required status checks, merge
  queue ambiguity, push rejection, or local/CI disagreement;
- unresolved requested changes, active review disagreement, unresolved
  conversations, late comments, draft PR state, merge conflict, stale branch, or
  non-trivial history cleanup;
- existing PR branch with unclear ownership or a concurrent lifecycle marker
  from another current actor;
- GitHub Actions permissions, workflow token handling, secret handling,
  repository settings, branch rules, or sensitive history cleanup;
- external fork boundary, unavailable check logs, unknown external provider
  failures, or public comment text that rejects a request, assigns blame, makes
  a commitment, asks the reporter to do work, or exposes sensitive detail.

## Completion

Before completion, final lifecycle writes, merge, close, or branch deletion,
re-read PR state, comments, reviews, review threads, lifecycle markers, linked
work, base/head SHA, branch/check state, and mergeability. Escalate instead of
finishing when late comments, another actor marker, PR state changes, branch
drift, or check changes alter safety.

Report the PR URL or number, final review state, final check state, merge or
close result when applicable, verification run locally, provider route, MCP
availability, and any remaining manual action. If linked issues remain open or
need separate lifecycle work, report that as a linked-work implication rather
than closing them by default.
