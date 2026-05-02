---
name: pr-ops
description: Use when the user explicitly asks to review, update, fix, merge, close, resume, or process one or more pull requests end to end; loads provider extensions such as GitHub™ only after the provider is identified.
---

# PR Ops

## Purpose

Run an explicit pull-request or merge-request lifecycle after the user asks for
it. Own the cross-provider operating loop: target resolution, mode selection,
live-state authority, review and comment state, check state, branch-update
safety, remediation handoff, verification, merge or close authority, cleanup,
and completion reporting.

Do not use this skill for incidental PR mentions, issue lifecycle work,
standalone deep CI debugging, security posture review, design review,
test-quality audit, or general project-management advice.

## Modes

Default mode is `full-cycle`: inspect the requested PR or queue, classify
reviews, comments, checks, branch state, and merge safety, address clear
actionable work, verify, update the PR branch when safe, request review when
appropriate, merge or close only when authorized, and clean up owned work areas.

Use a narrower mode only when the user asks for it:

- `review-only`: inspect PR state and produce findings without changing files.
- `checks-only`: inspect checks and classify failure ownership.
- `address-feedback`: implement clear review feedback or check failures.
- `merge-only`: merge or close a PR after live state proves it is safe.
- `resume`: recover an interrupted PR lifecycle from provider and git state.

Provider extensions may add provider-specific review, merge, update, or cleanup
modes. Provider modes add mechanics; they do not replace the core authority,
ask-vs-continue, escalation, ledger, verification, or output contracts.

## Evidence Contract

Before acting, inspect the user's requested scope, PR identifiers or URLs,
repository identity and remotes, repo guidance, current git branch, status,
worktrees, available provider tooling and auth, base and head refs, linked work,
reviews, comments, checks, branch protection or rules, and existing lifecycle
markers.

## Provider Selection

Identify the PR provider from the PR URL, repository remote, configured tooling,
identifier shape, or explicit user wording.

- For GitHub™ repositories, PR URLs, or GitHub™ PR numbers, read
  [extensions/github.md](extensions/github.md) before resolving provider state,
  writing lifecycle comments, replying to review threads, updating branches, or
  merging.
- For new provider extensions, follow the convention in
  [extensions/README.md](extensions/README.md).
- If no provider can be identified, ask one concise question naming the missing
  provider or repository.
- If a provider is identified but no matching extension exists, stop and report
  that `pr-ops` has no provider extension for that provider.

## Queue Limits

For one invocation:

- Complete at most 5 PRs.
- Inspect at most 15 PRs.
- During initial queue triage, inspect each PR at most once.

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

Use a local ledger only as append-only recovery hints:

```text
.cache/pr-ops/ledger.jsonl
```

Never commit the ledger. Never store secrets, tokens, raw logs, full PR bodies,
full comments, patch contents, check logs, or sensitive excerpts in it. On
resume, read the ledger for hints, then verify every material fact against the
provider and git. If they disagree, trust live state and append a
reconciliation entry.

## Normal Flow

For each PR:

1. Resolve live provider state, repository identity, base and head refs,
   current git state, linked work, permissions, and provider tooling.
2. Load the provider extension and follow its provider-specific state, review,
   check, lifecycle-marker, branch-update, merge, close, and cleanup rules.
3. Create or update current lifecycle status when the provider supports visible
   status updates and the action will not create noisy public communication.
4. Classify mode, actionability, blockers, review state, check state, branch
   state, merge safety, and integration strategy.
5. Select or reuse a work area according to repo guidance and PR ownership.
6. Implement only clear, in-scope feedback or check-failure remediation.
7. Infer verification from repo guidance, touched-surface docs, scripts,
   package metadata, CI workflows, check failures, and touched files.
8. Run item-level verification.
9. Auto-fix only deterministic formatter, generated-file, or lint failures.
10. Refresh live provider state, reviews, comments, checks, base/head refs,
    lifecycle markers, linked work, and git state before push or branch update.
11. Push or update the PR branch only when live state is still safe.
12. Refresh live state again before requesting review, resolving threads,
    merging, closing, deleting branches, or final lifecycle writes.
13. Merge, close, request review, resolve threads, or clean up only through the
    selected strategy after live state is still safe.
14. Rerun required verification after any merge, rebase, base update, or branch
    update changes the tested result.
15. Update lifecycle status and clean up only work areas owned by this run.

## Ask Vs Continue

Continue autonomously when the PR target, repository, provider tooling,
permissions, work area, verification path, branch-update path, and merge or
close authorization are all clear.

Ask the user only for global blockers that stop the run:

- provider or repository cannot be identified;
- authentication is missing or unusable;
- write permission is missing for a requested write operation;
- required verification tooling is missing and no repo-documented substitute
  exists;
- base branch, merge method, or repository integration policy cannot be
  determined;
- the user asked for merge or close but authorization is ambiguous.

For item-local ambiguity, update lifecycle status when possible, mark the PR
escalated, record the evidence, and continue the queue. Item-local ambiguity
includes unclear review intent, conflicting reviewer comments, unresolved
product contract, unsafe existing work, non-mechanical verification failure,
unclear check ownership, merge conflict, branch protection mismatch, stale
state, or any escalation gate.

## Escalation Gates

Escalation means stop the affected PR, record current status through the
provider when possible, preserve evidence without exposing sensitive detail,
and continue the queue when possible. Stop the whole run only for global
blockers.

Escalate on:

- wrong repository, wrong account, missing permission, or unexpected provider
  tooling route;
- ambiguous review intent, contradictory requirements, unclear product contract,
  unresolved requested changes, or active human review disagreement;
- security, auth, secrets, credentials, tokens, signing, workflow permissions,
  personal access tokens, secret scanning, repository settings, or sensitive
  history cleanup;
- dependency add, remove, upgrade, downgrade, replacement, or lockfile changes,
  unless the PR or review explicitly targets that dependency change;
- repo-wide guidance or agent behavior policy changes, unless explicitly
  targeted by the PR or mechanically required by an in-scope change;
- destructive or hard-to-reverse operations, including force-push, review
  dismissal, branch deletion, or history rewrite without explicit authority;
- stale state, concurrent actor changes, ownership conflicts, active maintainer
  discussion, or a lifecycle marker from another current actor;
- public communication that rejects a request, assigns blame, makes a
  commitment, asks the reporter to do work, or exposes sensitive detail;
- untrusted PR content execution before inspection proves it safe;
- verification unavailable, non-mechanical failure, local/remote disagreement,
  repeated no-progress auto-fix, conflicts, push rejection, protected-branch
  mismatch, dirty owned work areas, or non-trivial branch history cleanup;
- external fork or cross-repository boundaries, unknown check provider logs,
  missing required checks, pending required checks, code-owner review conflict,
  release/version ambiguity, unusual cost, or unusual runtime.

## Output

End with a concise report:

- completed count and PR identifiers;
- merged, closed, updated, reviewed, or escalated action per PR;
- escalated count and PR identifiers with gate names;
- skipped count and PR identifiers with reasons;
- remaining count when a queue was bounded;
- provider extensions loaded;
- provider tooling route and MCP availability when applicable;
- base/head refs or SHAs inspected;
- review state and check state summary;
- integration or merge strategy;
- lifecycle marker state;
- verification summary;
- global blocker when the run stopped early;
- lifecycle ledger path when a ledger entry was written.

These fields are the output footer/disclosure contract. Preserve them in
wrappers, delegated agents, and provider-specific completion reports.

Do not write a separate local summary file.
