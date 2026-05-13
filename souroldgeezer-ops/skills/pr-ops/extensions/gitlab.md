# GitLab Extension

Load this extension when the repository remote, merge request URL, GitLab `!123`
reference, prepared branch target, provider tooling, sibling-skill handoff, or
user wording identifies GitLab as the PR/MR provider.

This extension adds GitLab mechanics to `pr-ops`. It does not replace the core
authority, ledger, ask-vs-continue, escalation, verification, merge/close
authorization, or completion contracts.

## Authoritative Sources

Use these official GitLab docs as anchors, then verify live host behavior:

- Merge requests API:
  <https://docs.gitlab.com/api/merge_requests/>
- Notes API:
  <https://docs.gitlab.com/api/notes/>
- Discussions API:
  <https://docs.gitlab.com/api/discussions/>
- Pipelines API:
  <https://docs.gitlab.com/api/pipelines/>
- Jobs API:
  <https://docs.gitlab.com/api/jobs/>
- Merge request approvals API:
  <https://docs.gitlab.com/api/merge_request_approvals/>
- `glab mr create`:
  <https://docs.gitlab.com/cli/mr/create/>
- `glab mr list`:
  <https://docs.gitlab.com/cli/mr/list/>
- `glab mr view`:
  <https://docs.gitlab.com/cli/mr/view/>
- `glab mr note create`:
  <https://docs.gitlab.com/cli/mr/note/create/>
- `glab mr merge`:
  <https://docs.gitlab.com/cli/mr/merge/>
- `glab mr rebase`:
  <https://docs.gitlab.com/cli/mr/rebase/>
- `glab ci get`:
  <https://docs.gitlab.com/cli/ci/get/>

For GitLab Self-Managed, do not assume GitLab.com feature parity, tier-specific
fields, or current-version behavior without checking the live instance.

## State Resolution

Resolve current GitLab MR state before acting:

1. GitLab host, project full path or numeric project ID, default branch,
   current remote, and current local branch or worktree.
2. Prepared branch state when the target is a branch: local branch, remote
   source branch, intended target branch, linked issue context, and existing MR
   candidates by source branch, target branch, or linked issue.
3. Merge request IID (`iid` in payloads and `merge_request_iid` in API routes),
   web URL, state, title, description summary, draft flag, author, assignees,
   reviewers, labels, milestone, source and target branches, source and target
   project IDs, source head SHA, diff version SHAs, and closure references. Do
   not confuse project-local MR IID with the global MR `id`.
4. Mergeability and policy signals: `detailed_merge_status`, conflicts,
   `blocking_discussions_resolved`, `draft`, `merge_after`,
   `merge_when_pipeline_succeeds` or `auto_merge`, `rebase_in_progress`,
   squash policy, source-branch-removal policy, approval state, and merge
   request dependencies.
5. Notes and discussions needed for latest maintainer comments, system
   activity, unresolved threads, inline diff notes, and existing lifecycle
   markers.
6. Pipelines attached to the merge request, `head_pipeline` when available,
   project pipelines for the head SHA when MR pipelines are absent, job details
   needed to classify failures, skipped/manual jobs, child pipelines, and
   external status detail URLs.
7. Authenticated account, selected GitLab host, project route, token scope, and
   write permissions for notes, discussions, branch push, MR creation, rebase,
   approval, merge, close, and branch deletion. Never print tokens or
   token-derived secrets.
8. Current git state, including dirty files, active worktrees, protected branch
   constraints observable from tooling, and whether an existing branch clearly
   owns the MR.

Treat GitLab and git as live authority. Do not rely on a local ledger, stale
prompt context, or earlier pipeline output without rechecking material facts.

Treat a GitLab `404` on a private project, cross-project MR, or confidential
source as ambiguous until auth, host, project path, and permissions are checked;
it can mean missing permission rather than absence.

## Tooling Order

Use the best available GitLab integration in this order:

1. A configured GitLab MCP server, connector, or provider integration after
   verifying active session routing, authenticated account, host, and project.
2. `glab` CLI after verifying `glab auth status`, repository context, and host.
   Use `-R` with `group/project`, full URL, or Git URL when the current
   directory context is ambiguous.
3. GitLab REST API v4 when provider tooling and `glab` are unavailable or
   insufficient. Use `PRIVATE-TOKEN` or `Authorization: Bearer`, the
   URL-encoded path form for project paths, `merge_request_iid`, and
   pagination-aware reads.

If the selected route points at the wrong account, host, or project, escalate
the MR.

Prefer stable REST endpoints for automation that needs precise lifecycle marker
edits, thread replies, thread resolution, or line-level discussions. Treat
experimental `glab mr note` commands as convenience routes only after checking
that their current behavior is adequate for the requested operation.

## Lifecycle Note

For long-running write work, add or update an MR lifecycle marker unless the
run lacks note permission or the user asked for read-only review. When a
prepared branch target has no MR yet, defer the MR marker until after MR
creation and use the issue lifecycle marker or final chat output for
pre-creation status. Update the latest marker from the same actor when
possible. Add a new note only when editing is unavailable, editing would hide
reply context, or a fresh visible escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

Working state:

```md
<!-- pr-ops:gitlab:v1 -->
Lifecycle status: working

Actor: Codex
Mode: full-cycle
Scope: group/project!123
Current step: monitoring merge request pipelines
Review state: unresolved discussions
Pipelines: pending - test
Verification: pending
Last reviewed: 2026-05-13T12:00:00+03:00
```

Escalated state:

```md
<!-- pr-ops:gitlab:v1 -->
Lifecycle status: escalated

Actor: Codex
Mode: full-cycle
Scope: group/project!123
Gate: required pipeline still manual after monitoring
Evidence: latest head SHA has a required manual job without documented allowance
Pipelines: manual
Verification: local checks passed
Last reviewed: 2026-05-13T12:00:00+03:00
```

Completed state:

```md
<!-- pr-ops:gitlab:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: merge-only
Scope: group/project!123
Result: merged merge request
Review state: approved
Pipelines: passed - head pipeline green
Verification: passed - repository checks
Last reviewed: 2026-05-13T12:00:00+03:00
```

The final lifecycle marker update is sufficient before merge or close. Do not
add a separate completion note unless updating the marker fails or the user
explicitly asks for a public summary.

## MR Creation Or Reuse

When the target is a prepared branch, create or reuse the GitLab merge request
before applying discussion, pipeline, approval, merge, close, or cleanup rules.

1. Re-read project identity, default/target branch, local branch, remote source
   branch, linked issue context, existing MR candidates, permissions,
   lifecycle markers, and protected branch state.
2. Reuse an existing open MR when the source branch, target branch, project, and
   linked issue context show clear ownership and live state is safe.
3. If no safe MR exists, push the prepared branch only after confirming the
   local branch is clean enough for the requested operation, the branch has the
   intended target, and the actor has permission to create or update the
   source branch.
4. Create the MR using repository title/body conventions when available.
   Include linked issue context supplied by `issue-ops` or the user. Set draft
   state, reviewers, labels, milestones, assignees, squash, source-branch
   deletion, and auto-merge only when the user or repository guidance asks for
   them.
5. After the MR exists, continue through lifecycle marker, discussion,
   pipeline, approval, branch-update, merge, close, and cleanup rules in this
   extension.

Escalate when branch ownership is unclear, no safe target branch can be
selected, an existing MR candidate has active conflicting ownership, the actor
cannot push or create the MR, or creating the MR would cross an external fork or
project boundary without explicit authorization.

## Review And Discussion Handling

Distinguish MR notes, discussions, diff notes, system notes, approvals,
reviewer assignment, and pipeline/job annotations. Reply in the same discussion
when addressing an inline diff note. Do not answer inline feedback as a
top-level MR note unless discussion replies are unavailable.

Treat review and discussion states as live merge gates:

- Unresolved discussions block merge when the project requires resolved
  discussions or when the thread contains actionable human feedback.
- Missing required approvals, ineligible self-approval, or approval state that
  changed after the current head SHA blocks merge until live state is safe.
- Bot or automated comments are actionable when they point to concrete
  repo-local defects; otherwise classify them as advisory or escalate.

Resolve discussions only after the fix is present, verified, and a same-thread
reply records the action. Do not reset approvals, approve your own MR, edit
approval rules, or change reviewer policy unless the user explicitly asks and
the selected GitLab route proves the actor has permission.

Request reviewers only when the user or repository guidance asks for review, or
when the MR was updated and the existing reviewer set is clearly the correct
audience. Do not create or alter labels, milestones, iterations, approval
rules, assignees, or project settings unless explicitly asked.

## Pipeline Handling

Inspect MR pipelines, `head_pipeline`, project pipelines for the source head
SHA when needed, job details, child pipelines, required/manual jobs, and recent
pipeline details before classifying the MR.

Fix only clear in-repo failures: deterministic formatting, lint, compile, unit,
integration, generated-file, or narrow test failures with enough logs to
identify the repository-owned defect. Escalate external-provider failures,
missing logs, unknown required pipelines or jobs, infrastructure outages, flaky
non-reproducible failures, permission failures, and failures that require
secrets or third-party service access.

Rerun or create pipelines only when the provider route supports it, the
pipeline is safe to rerun, and repository guidance or the user allows reruns.
Never claim remote pipelines are green from local verification alone.

### Pending Pipeline Monitoring

In `full-cycle`, pending required pipelines or jobs after MR creation, MR
reuse, push, rebase, branch update, or explicit pipeline refresh are active
work. Keep polling live GitLab MR state, pipeline state, job state, source head
SHA, discussions, approvals, and lifecycle markers until every required
pipeline and required job reaches a safe terminal state or a GitLab escalation
gate is hit. Do not stop after one retry, and do not final-report a normal
completion while required pipelines are still pending.

Use a provider-respectful cadence and avoid noisy public notes. Update an MR
lifecycle marker only when the visible state changes materially, for example
from `working` to `escalated` or `completed`; do not add one note per poll.

Classify terminal states this way:

- `passed`: the relevant GitLab status is `success`; continue the requested
  lifecycle, including merge when authorized and all other live gates are safe.
- `failed`: address clear in-repo failures when the mode allows it; otherwise
  escalate with the failing pipeline or job names and the ownership
  classification.
- `canceled`, `skipped`, `manual`, `missing`, or `unknown`: escalate unless
  repository guidance explicitly documents that state as acceptable for the MR.
- `pending`, `created`, `preparing`, `running`, `scheduled`, or
  `waiting_for_resource` on the current head SHA: continue monitoring until the
  state changes or a real stop gate is hit.
- Any pipeline on a newer head SHA than previously inspected: restart
  monitoring from the newer head after re-reading discussions, approvals, and
  lifecycle markers.

Stop monitoring only for a real gate: provider queries are unavailable, the
route is rate-limited, required pipeline identity is unknown, an external
provider does not expose enough state to continue, a repo-defined monitoring
budget is exhausted, the user interrupts, or session/context limits make
continued polling unsafe. In that case, update the lifecycle marker as
`escalated` with a gate such as `required pipelines still pending after
monitoring stopped`, and report `created/reused and monitoring stopped due to
escalation` rather than a completed lifecycle.

## Branch Update And Push

Prefer the MR's existing source branch when it clearly owns the work and is
safe to update. For prepared branch targets, treat the selected branch as the
candidate MR source only after ownership, target, and permission checks pass.
Create a local worktree or branch only when needed to inspect, test, create, or
patch the MR.

Before creating, pushing, rebasing, or updating:

1. Re-read MR or MR-candidate state, source and target branch SHAs,
   discussions, notes, approvals, pipelines, lifecycle markers, protected
   branch state, and mergeability when an MR already exists.
2. Confirm the local branch descends from the current MR source head when an MR
   exists; for a prepared branch without an MR, confirm the intended target and
   no unsafe remote divergence unless the update strategy is explicitly
   authorized.
3. Confirm no other current actor owns the lifecycle marker or active branch
   work.

Use GitLab's rebase operation or merge target into the source branch only when
safe and non-destructive. Rebase, force-push, branch recreation, `--skip-ci`,
and non-trivial history cleanup require explicit user authorization unless
repository guidance already grants it for this operation.

Escalate on fork or cross-project permission ambiguity, MR creation failure,
push rejection, merge conflict, protected source branch mismatch, stale branch
with active reviewer discussion, or local and remote SHA disagreement.

## Merge, Close, And Cleanup

Merge or close only when the user requested or authorized it and live state is
safe.

Before merge, re-read MR state, source/target branch SHAs, draft state,
`detailed_merge_status`, conflicts, approvals, unresolved discussions, required
pipelines and jobs, merge request dependencies, protected branch state,
lifecycle markers, and linked issues. Escalate instead of merging when any
required pipeline or job is failed, pending, missing, skipped/manual without
documented allowance, or unknown; when approvals are missing or stale; when the
MR is draft; when blocking discussions are unresolved; when merge dependencies
or branch protection requirements are unclear; or when late notes alter safety.

Use the repository's documented merge strategy. If no strategy is documented,
use the provider default only when the user explicitly asked to merge and the
route does not require selecting a strategy. Do not squash, rebase, auto-merge,
remove the source branch, or edit commit messages to change history semantics
unless requested or documented by repository policy.

Prefer merge operations that include the current source head SHA when the route
supports it. If `glab mr merge` enables auto-merge because a pipeline is still
running, treat that as "auto-merge armed" and keep monitoring until GitLab
reports a merged state, or escalate if continued monitoring is not possible.

Close without merge only when the user explicitly asks, the MR is obsolete or
superseded by live evidence, or repository guidance defines a safe close rule.
Do not delete the remote source branch unless it is owned by this run, merged
with a documented remove-source-branch policy, or the user explicitly
authorizes deletion. Local branch and worktree cleanup is allowed only for work
areas owned by this run.

## GitLab Escalation Gates

Escalate the affected MR on:

- wrong account, wrong host, wrong project path, missing permission, ambiguous
  `id` versus `iid`, or unexpected GitLab tooling route;
- prepared branch ownership ambiguity, MR creation permission failure, unsafe
  existing MR reuse candidate, or cross-project/fork boundary without explicit
  authorization;
- GitLab Self-Managed version or tier differences that make a required field,
  endpoint, approval signal, or permission unavailable;
- protected branch mismatch, required MR policy, required pipeline or job
  ambiguity, push rejection, rebase rejection, merge queue or auto-merge
  ambiguity, or local/pipeline disagreement;
- unresolved human feedback, missing or stale approvals, active review
  disagreement, unresolved discussions, late notes, draft MR state, merge
  conflict, stale branch, dependency blocks, or non-trivial history cleanup;
- existing MR branch with unclear ownership or a concurrent lifecycle marker
  from another current actor;
- GitLab token scopes, protected branches, project settings, webhooks, CI/CD
  variables, repository settings, or sensitive history cleanup;
- external fork or cross-project boundary, unavailable job logs, unknown
  external provider failures, or public note text that rejects a request,
  assigns blame, makes a commitment, asks the reporter to do work, or exposes
  sensitive detail.

## Completion

Before completion, final lifecycle writes, merge, close, or branch deletion,
re-read MR state, notes, discussions, approvals, lifecycle markers, linked
work, source/target branch SHAs, pipeline state, and mergeability. Escalate
instead of finishing when late notes, another actor marker, MR state changes,
branch drift, approval changes, or pipeline changes alter safety.

Report the MR URL or `group/project!iid`, whether it was created or reused,
final discussion and approval state, final pipeline state, merge or close
result when applicable, verification run locally, provider route, MCP
availability, and any remaining manual action. If linked issues remain open or
need separate lifecycle work, report that as a linked-work implication rather
than closing them by default.
