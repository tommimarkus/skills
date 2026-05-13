# GitLab Extension

Load this extension when the repository remote, issue URL, provider tooling, or
user wording identifies GitLab as the issue tracker.

This extension adds GitLab mechanics to `issue-ops`. It does not replace the
core authority, ledger, ask-vs-continue, escalation, verification, handoff, or
completion contracts.

## Authoritative Sources

Use these official GitLab docs as anchors, then verify live host behavior:

- REST API authentication:
  <https://docs.gitlab.com/api/rest/authentication/>
- Issues API:
  <https://docs.gitlab.com/api/issues/>
- Notes API:
  <https://docs.gitlab.com/api/notes/>
- Issue links API:
  <https://docs.gitlab.com/api/issue_links/>
- Merge requests API:
  <https://docs.gitlab.com/api/merge_requests/>
- `glab issue` CLI:
  <https://docs.gitlab.com/cli/issue/>
- GitLab issue management and closing behavior:
  <https://docs.gitlab.com/user/project/issues/managing_issues/>

For GitLab Self-Managed, do not assume GitLab.com feature parity, tier-specific
fields, or current-version behavior without checking the live instance.

## State Resolution

Resolve current GitLab state before acting:

1. GitLab host, project full path or numeric project ID, default branch, current
   remote, and current local branch or worktree.
2. Issue `issue_iid`, state, title, body summary, labels, assignees, milestone,
   confidential flag, issue type, task-completion status, and web URL. Do not
   confuse project-local `issue_iid` with the global issue `id`.
3. Issue notes needed for latest maintainer comments, system activity, and
   existing lifecycle markers.
4. Linked issues from the Issue links API, including `relates_to`, `blocks`, and
   `is_blocked_by`.
5. Related merge requests from `related_merge_requests`; when an MR is involved
   in closure, use `closes_issues` on the merge request to verify which issues
   GitLab expects to close on merge.
6. Authenticated account, selected GitLab host, and write permissions for issue
   notes, metadata updates, branch preparation, and issue closure. Never print
   tokens or token-derived secrets.
7. Current git state, including dirty files, active worktrees, protected branch
   constraints observable from tooling, and whether an existing branch clearly
   owns the issue.

Treat GitLab and git as live authority. Do not rely on a local ledger or stale
prompt context without rechecking material facts.

Treat a GitLab `404` on a private project or confidential issue as ambiguous
until auth, host, project path, and permissions are checked; it can mean
"missing permission" rather than "the issue does not exist."

## Tooling Order

Use the best available GitLab integration in this order:

1. A configured GitLab MCP server, connector, or provider integration after
   verifying active session routing, authenticated account, host, and project.
2. `glab` CLI after verifying `glab auth status`, repository context, and host.
   Use `-R` with `group/project`, full URL, or Git URL when the current
   directory context is ambiguous.
3. GitLab REST API v4 when provider tooling and `glab` are unavailable or
   insufficient. Use `PRIVATE-TOKEN` or `Authorization: Bearer`, the
   URL-encoded path form for project paths, `issue_iid`, and pagination-aware
   reads.

If the selected route points at the wrong account, host, or project, escalate
the item.

## Lifecycle Status

Every inspected GitLab issue gets a lifecycle marker note unless the run lacks
note permission. Update the latest marker from the same actor when the selected
route supports note editing. Add a new note only when editing is unavailable,
editing would hide reply context, or a fresh visible escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

For confidential issues, avoid sensitive detail in public notes. Use internal
notes only when the selected tooling supports them and repository guidance
expects internal lifecycle state; otherwise write a terse public marker or
escalate if no safe marker can be written.

Implementing state:

```md
<!-- issue-ops:gitlab:v1 -->
Lifecycle status: implementing

Actor: Codex
Mode: full-cycle
Integration: pr-ops handoff
Scope: group/project#123
Current step: working on an isolated branch
Disposition: actionable
Verification: pending
Last reviewed: 2026-05-13T12:00:00+03:00
```

Escalated state:

```md
<!-- issue-ops:gitlab:v1 -->
Lifecycle status: escalated

Actor: Codex
Mode: full-cycle
Integration: pr-ops handoff
Scope: group/project#123
Gate: missing GitLab merge-request provider support in pr-ops
Evidence: implementation requires an MR lifecycle but no supported handoff route is available
Verification: local verification passed
Last reviewed: 2026-05-13T12:00:00+03:00
```

Completed state:

```md
<!-- issue-ops:gitlab:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: full-cycle
Integration: direct integration
Scope: group/project#123
Result: integrated on the default branch
Verification: passed - unit tests
Resolution: implemented the issue request and verified closure safety
Last reviewed: 2026-05-13T12:00:00+03:00
```

The final lifecycle marker update is sufficient before closing the issue. Do
not add a separate closing note unless updating the marker fails.

## Integration Strategies

Default public integration strategy is `pr-ops-handoff` when an implementation
requires a merge request:

1. Create or reuse an issue-owned branch.
2. Commit focused work.
3. Run issue-level local verification.
4. Hand off to `pr-ops` with GitLab host, project path, base branch, prepared
   branch, linked issue `issue_iid`, lifecycle marker context, and local
   verification summary.
5. If no GitLab merge-request provider extension is available in `pr-ops`,
   escalate instead of creating, updating, monitoring, merging, or cleaning up a
   GitLab merge request inside `issue-ops`.
6. Re-read the issue after `pr-ops` reports a merged merge request, then close
   only when live issue state, notes, linked issues, and MR closure evidence are
   still safe.

Use `direct-main` only when the user or repository guidance explicitly allows
it, branch protection permits it, and live state is clean. In direct-main mode,
prefer one clean commit named `Fix #<issue_iid>: <title>` for defects or
`Resolve #<issue_iid>: <title>` otherwise when the issue is in the same project.
Use a full GitLab issue reference for cross-project closure text.

When an existing related merge request or issue branch clearly owns the issue,
handoff that target to `pr-ops` instead of assessing MR checks, discussions,
branch updates, merge safety, or cleanup in `issue-ops`. Escalate only when no
safe issue-side handoff target can be identified.

Do not assume an MR merge will close an issue solely because the branch or MR
description appears to mention it. Use live issue state, related MRs, and
`closes_issues` where available before final closure.

## Metadata Policy

Use existing labels only when classification is obvious from the repository's
taxonomy. Do not create lifecycle labels.

Treat labels, milestones, iterations, weight, health status, assignees, and
confidentiality as read-only context unless the user or repository guidance
explicitly requests a change. Premium or Ultimate fields may be absent; absence
is not evidence that the work item lacks that concept.

Do not move, promote, clone, duplicate, or convert issues unless the user
explicitly asks for that operation and live permissions are clear. Moves can
close and copy issues across projects, so treat them as destructive or
hard-to-reverse unless the task is specifically about moving.

## GitLab Escalation Gates

Escalate the affected issue on:

- wrong account, wrong host, wrong project path, missing permission, or
  unexpected GitLab tooling route;
- ambiguous numeric reference where `id`, `iid`, `issue_iid`, and
  `merge_request_iid` could be confused;
- GitLab Self-Managed version or tier differences that make a required field,
  endpoint, or permission unavailable;
- protected branch mismatch that prevents both direct integration and
  `pr-ops` handoff;
- existing related merge request or issue branch with unclear issue ownership;
- concurrent lifecycle marker from another current actor;
- open blockers, unresolved linked `blocks` / `is_blocked_by` state, or late
  comments that change closure safety;
- confidential issue detail that cannot be safely summarized in a lifecycle
  note with available tooling;
- GitLab token scopes, protected branches, project settings, webhooks, CI/CD
  variables, repository settings, or sensitive history cleanup;
- public note text that rejects a request, assigns blame, makes a commitment,
  asks the reporter to do work, or exposes sensitive detail;
- implementation requires GitLab merge-request lifecycle work but no safe
  `pr-ops` GitLab handoff exists.

## Completion

Before completion or closure, re-read issue state, notes, lifecycle markers,
linked issues, related merge requests, `closes_issues` for relevant MRs, and
the delegated `pr-ops` result. Escalate instead of closing when late comments,
another actor marker, issue state changes, unresolved blockers, or a non-merged
or escalated MR result alters closure safety.

On completion, update the lifecycle marker before closing the issue. Close with
the selected provider route only when live issue state is still safe and the
user, repository guidance, or completed integration strategy authorizes closure.
For REST close or reopen operations, use the Issues API update route with
`state_event=close` or `state_event=reopen`; do not delete issues as a closure
shortcut.
If `pr-ops` created, reused, or merged a merge request, report the MR URL or IID
in the final chat output. If the issue remains open because the delegated MR
lifecycle did not merge, report the remaining state instead of closing it.
