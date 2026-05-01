---
name: github-issue-lifecycle
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more GitHub™ issues end to end in this repository.
---

# GitHub Issue Lifecycle

## Purpose

Run a mostly autonomous issue lifecycle for this repository after the user
explicitly invokes it. Default to full-cycle handling: triage, lifecycle
comment, isolated implementation, verification, direct-main integration, push,
issue close, cleanup, and queue continuation.

Do not use this skill for incidental issue mentions, ordinary PR review,
general GitHub questions, or published marketplace/plugin distribution.

## Invocation

Default mode is `full-cycle`. Narrow modes apply only when the user explicitly
asks: `triage-only`, `plan-only`, `implement-only`, `resume`, or `pr-mode`.

Scope can be one issue, an explicit list, or `all open`. For `all open`, inspect
all open issues, sort by trivially determinable priority, and then use oldest
first. Trivial priority signals include existing priority or severity labels,
obvious bug/regression/blocker/security signals, clear reproduction or
acceptance criteria, and already-linked work that can be completed mechanically.
Do not perform deep analysis only to rank the queue.

Default queue limits:

- Complete at most 10 issues per invocation.
- Inspect at most 25 issues per invocation.
- Inspect each issue at most once per invocation.

## Authority And State

Treat live GitHub state and git state as authoritative. Use the local ledger
only as an append-only recovery hint:

```text
.cache/github-issue-lifecycle/ledger.jsonl
```

Never commit the ledger. Never store secrets, tokens, raw logs, full issue
bodies, or sensitive excerpts in it. On resume, read the ledger for hints, then
verify every material fact against GitHub and git. If they disagree, trust
GitHub/git and append a reconciliation entry.

## Normal Flow

For each issue:

1. Resolve live issue state, comments, labels, linked PRs, repository identity,
   and GitHub auth/tool routing.
2. Run the repo-internal `ip-hygiene` triage against the issue body, comments,
   referenced material, and likely touched surfaces.
3. Create or update the lifecycle comment marker.
4. Classify actionability, scope, and integration path.
5. Resume an existing PR branch if one clearly owns the issue; otherwise use
   direct-main mode.
6. Use `.worktrees/github-issue-lifecycle-main` as the dedicated integration
   worktree and `.worktrees/issue-<number>` as the issue worktree.
7. Keep direct-main issue branches local. Prefer one clean commit named
   `Fix #<number>: <title>` for defects or `Resolve #<number>: <title>`
   otherwise.
8. Infer verification from repo guidance, touched-surface docs, scripts,
   package metadata, CI workflows, and finally the touched files.
9. Run issue-branch verification.
10. Auto-fix only deterministic mechanical formatter or lint failures.
11. Fetch `main`. If remote `main` moved, rebase only when conflict-free.
12. Fast-forward integration `main`, rerun verification, push `main`, update
    the lifecycle comment to completed, close the issue, and clean up.

## Ask Vs Continue

Continue autonomously when the issue target, repository, auth, worktree state,
verification path, and integration path are all clear under this skill's normal
flow.

Ask the user only for global blockers that stop the whole run, such as unusable
GitHub auth, missing push permission, missing required verification tooling, or
an unusable base branch.

For issue-local ambiguity, do not ask immediately during queue processing.
Escalate that issue with a lifecycle marker, record the evidence, and continue
to the next issue when possible. Issue-local ambiguity includes missing
acceptance criteria, conflicting comments, duplicate precedence, uncertain
product/skill contract, unsafe existing PR state, or any escalation gate below.

## Lifecycle Comment

Every inspected issue gets a lifecycle marker, including fast-triage skips and
escalations. Update the latest marker in place where possible. Add a new
comment only when editing is unavailable, editing would hide reply context, or
a fresh visible escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

```md
<!-- github-issue-lifecycle:v1 -->
Lifecycle status: implementing

Actor: Codex
Mode: full-cycle
Integration: direct-main
Scope: #123
Current step: working on a temporary branch
Disposition: actionable
Verification: pending
Last reviewed: 2026-05-02T12:00:00+03:00
```

Completed state:

```md
<!-- github-issue-lifecycle:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: full-cycle
Integration: direct-main
Scope: #123
Result: pushed to `main`
Verification: passed - skill architecture report, unit tests, whitespace check
Resolution: implemented the issue request and verified the affected surface
Last reviewed: 2026-05-02T12:00:00+03:00
```

The final lifecycle comment update is sufficient before closing the issue. Do
not add a separate closing comment unless updating the lifecycle comment fails.

## GitHub Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing.
2. `gh` CLI after verifying auth and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

## Labels, Projects, And Milestones

Use existing labels when classification is obvious. Create or normalize labels
only when following the repository's existing taxonomy. Do not create lifecycle
labels. Treat projects and milestones as read-only context when permissions
allow.

## Escalation Gates

Escalation means stop the affected issue, update its lifecycle marker with the
gate and evidence, and continue the queue when possible. Stop the whole run only
for global blockers such as unusable auth, unusable base branch, missing
required verification tooling, or missing push permission.

Escalate on:

- wrong repository, wrong account, missing permission, or unexpected GitHub
  tool routing;
- `ip-hygiene` risk in issue content, referenced material, or likely touched
  surfaces;
- ambiguous scope, contradictory requirements, unclear product or skill
  contract, or duplicate precedence requiring maintainer judgment;
- security, auth, secrets, credentials, tokens, signing, GitHub Actions
  permissions, MCP/PAT handling, secret scanning, repository settings, or
  sensitive history cleanup;
- dependency add, remove, upgrade, downgrade, replacement, or lockfile changes,
  unless the issue explicitly targets that exact dependency change;
- repo-wide guidance or agent behavior policy changes, unless explicitly
  targeted by the issue or mechanically required by an in-scope published-skill
  change;
- destructive or hard-to-reverse operations;
- stale state, concurrent actor changes, ownership conflicts, active maintainer
  discussion, or a lifecycle marker from another current actor;
- public communication that rejects a request, assigns blame, makes a
  commitment, asks the reporter to do work, or exposes sensitive detail;
- untrusted issue content execution before inspection proves it safe;
- verification unavailable, non-mechanical failure, local/CI disagreement,
  repeated no-progress auto-fix, conflicts, push rejection, protected `main`,
  dirty lifecycle worktrees, or non-trivial branch history cleanup;
- unclear generated artifact provenance, unusual cost/runtime/API use, release
  or versioning ambiguity, external repository boundaries, human review
  conflict, or unsafe existing PR state.

Autonomous handling is allowed for:

- published skill/plugin changes when the issue target is clear;
- architecture/model/rendering issues, provided real validation or render
  evidence is used where relevant;
- mechanical formatting/lint fixes;
- obvious label use, creation, or normalization.

## Completion Output

End with a concise chat report listing completed, escalated, skipped, and
remaining issue counts. Include verification summaries and any global blocker.
Do not write a separate local summary file.
