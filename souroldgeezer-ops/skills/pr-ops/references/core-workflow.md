# PR Ops Core Workflow

Provider extensions add mechanics; they do not replace this authority,
ask-vs-continue, escalation, ledger, verification, or completion contract.

## Evidence Contract

Before acting, inspect the user's requested scope, PR/MR identifiers or URLs,
prepared branch targets, repository identity and remotes, repo guidance, current
git branch, status, worktrees, available provider tooling and auth, base and
head refs, linked work, reviews, comments, checks, branch protection or rules,
and existing lifecycle markers.

## Queue Limits

For one invocation:

- Complete at most 5 PRs/MRs.
- Inspect at most 15 PRs/MRs.
- During initial queue triage, inspect each PR/MR at most once.

Active PRs are no longer in initial triage. Re-read active PRs whenever the
workflow reaches branch update, push, review request, merge, close, cleanup, or
final lifecycle status writes.

For broad queues, sort by trivial priority signals first, then age. Trivial
signals include existing priority markers, failing required checks, requested
changes, merge conflicts, stale branch state, security-sensitive labels, blocked
release labels, and explicit user ordering. Do not perform deep analysis only
to rank the queue.

## Authority And Ledger

Live provider state and live git state are authoritative.

Use `.cache/pr-ops/ledger.jsonl` only as append-only recovery hints. Never
commit the ledger. Never store secrets, tokens, raw logs, full PR/MR bodies,
full comments, patch contents, check logs, or sensitive excerpts in it. On
resume, read the ledger for hints, then verify every material fact against the
provider and git. If they disagree, trust live state and append a reconciliation
entry.

## Normal Flow

For each PR/MR or prepared branch:

1. Resolve live provider state, repository identity, base/head refs, current git
   state, linked work, permissions, provider tooling, and existing PR/MR
   candidates when the target is a branch.
2. Load the provider extension and follow its provider-specific state, PR/MR
   creation or reuse, review, check, lifecycle-marker, branch-update, merge,
   close, and cleanup rules.
3. Create or update current lifecycle status when the provider supports visible
   status updates and the action will not create noisy public communication.
4. Classify mode, actionability, blockers, PR/MR creation or reuse state, review
   state, check state, branch state, merge safety, and integration strategy.
5. Select or reuse a work area according to repo guidance and PR/MR ownership.
6. Implement only clear, in-scope feedback or check-failure remediation.
7. Infer verification from repo guidance, touched-surface docs, scripts,
   package metadata, CI workflows, check failures, and touched files.
8. Run item-level verification.
9. Auto-fix only deterministic formatter, generated-file, or lint failures.
10. Refresh live provider state, reviews, comments, checks, base/head refs,
    lifecycle markers, linked work, and git state before PR/MR creation, push, or
    branch update.
11. Create, reuse, push, or update the PR/MR branch only when live state is still
    safe.
12. Refresh live state again before requesting review, resolving threads,
    merging, closing, deleting branches, or final lifecycle writes.
13. Create or update the PR/MR, merge, close, request review, resolve threads, or
    clean up only through the selected strategy after live state is still safe.
14. In `full-cycle`, when required checks are pending after PR/MR creation,
    branch update, push, or explicit check refresh, keep monitoring live check
    state through the provider extension. Do not produce a normal final report
    while checks are still pending; if monitoring cannot continue, update
    lifecycle state as escalated and report the stop gate.
15. Rerun required verification after any merge, rebase, base update, or branch
    update changes the tested result.
16. Update lifecycle status and clean up only work areas owned by this run.

## Ask Vs Continue

Continue autonomously when the PR/MR or prepared branch target, repository,
provider tooling, permissions, work area, verification path, PR/MR creation or
branch-update path, and merge or close authorization are all clear.

Ask the user only for global blockers that stop the run: provider or repository
cannot be identified; authentication is missing or unusable; write permission is
missing for a requested write operation; required verification tooling is missing
and no repo-documented substitute exists; base branch, PR/MR creation policy,
merge method, or repository integration policy cannot be determined; or the
user asked for PR/MR creation, merge, or close but authorization is ambiguous.

For item-local ambiguity, update lifecycle status when possible, mark the PR/MR
escalated, record the evidence, and continue the queue.

## Escalation Gates

Escalation means stop the affected PR/MR, record current status through the
provider when possible, preserve evidence without exposing sensitive detail, and
continue the queue when possible. Stop the whole run only for global blockers.

Escalate on wrong repository/account, missing permission, unexpected provider
route, unclear branch ownership, unresolved requested changes, active human
review disagreement, security/auth/secrets/history cleanup, dependency changes
outside scope, repo-wide policy changes outside scope, destructive operations
without authority, stale or concurrently changed state, public communication
that rejects/blames/commits/asks reporters for work/exposes sensitive detail,
untrusted PR content execution before inspection, unavailable verification,
non-mechanical failures, push rejection, protected-branch mismatch, dirty owned
work areas, external fork boundaries, unknown check provider logs, missing
required checks, code-owner review conflict, release/version ambiguity, unusual
cost, or unusual runtime.

## Output

End with a concise report containing: completed count and PR/MR identifiers or
prepared branch targets; created/reused/merged/closed/updated/reviewed/escalated
action per item; escalated count with gate names; skipped count with reasons;
remaining count when a queue was bounded; provider extensions loaded; provider
tooling route and MCP availability when applicable; base/head refs or SHAs
inspected; linked issues or sibling-skill handoff context when applicable;
review state and check state summary; full-cycle terminal-check or escalation
state; integration or merge strategy; lifecycle marker state; verification
summary; global blocker when stopped early; and lifecycle ledger path when a
ledger entry was written.

These fields are the output footer/disclosure contract. Preserve them in
wrappers, delegated agents, and provider-specific completion reports. Do not
write a separate local summary file.
