---
name: issue-ops
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more issues or work items end to end; loads provider extensions such as GitHub™ only after the tracker is identified.
---

# Issue Ops

## Purpose

Run an explicit issue or work-item lifecycle after the user asks for it. Own the
cross-provider operating loop: target resolution, mode selection, live-state
authority, queue limits, lifecycle state, escalation, implementation handoff,
local verification, integration handoff, completion reporting, and queue
continuation.

Do not use this skill for incidental issue mentions, ordinary pull-request
review, standalone CI debugging, security posture review, design review, or
general project-management advice.

## Modes

Default mode is `full-cycle`: inspect the requested issue or queue, record
visible lifecycle state when the provider supports it, implement actionable
work, verify locally, hand off pull-request lifecycle work when the selected
strategy requires it, update status, and close or complete the work item when
allowed.

Use a narrower mode only when the user asks for it:

- `triage-only`: classify state, actionability, blockers, and next action.
- `plan-only`: produce an implementation plan without changing repo files.
- `implement-only`: implement a clearly selected issue without queue work.
- `resume`: recover an interrupted lifecycle from live tracker and git state.

Provider extensions may add direct integration, pull-request handoff, or other
provider-specific issue completion modes. Provider modes add mechanics; they do
not replace the core authority, ask-vs-continue, escalation, ledger,
verification, handoff, or completion contracts.

## Evidence Contract

Before acting, inspect the user's requested scope, issue or work-item
identifiers or URLs, repository identity and remotes, repo guidance, current
git branch, status, and worktrees, available provider tooling and auth, linked
work, and existing lifecycle markers.

## Provider Selection

Identify the issue tracker from the issue URL, repository remote, configured
tooling, issue identifier, or explicit user wording.

- For GitHub repositories, issue URLs, or GitHub issue numbers, read
  [extensions/github.md](extensions/github.md) before resolving provider state
  or writing lifecycle comments.
- For new provider extensions, follow the convention in
  [extensions/README.md](extensions/README.md).
- If no provider can be identified, ask one concise question naming the missing
  tracker or repository.
- If a provider is identified but no matching extension exists, stop and report
  that `issue-ops` has no provider extension for that tracker.

## Queue Limits

For one invocation:

- Complete at most 10 issues or work items.
- Inspect at most 25 issues or work items.
- During initial queue triage, inspect each item at most once.

Active items are no longer in initial triage. Re-read active items whenever the
workflow reaches integration, closure, or final lifecycle status writes.

For broad queues, sort by trivial priority signals first, then age. Trivial
signals include existing priority or severity markers, obvious bug, regression,
blocker, security, reproduction, acceptance criteria, and linked work that can
be completed mechanically. Do not perform deep analysis only to rank the queue.

## Authority And Ledger

Live tracker state and live git state are authoritative.

Use a local ledger only as append-only recovery hints:

```text
.cache/issue-ops/ledger.jsonl
```

Never commit the ledger. Never store secrets, tokens, raw logs, full issue
bodies, full comments, or sensitive excerpts in it. On resume, read the ledger
for hints, then verify every material fact against the tracker and git. If they
disagree, trust live state and append a reconciliation entry.

## Normal Flow

For each item:

1. Resolve live tracker state, repository identity, current git state, linked
   work, permissions, and provider tooling.
2. Load the provider extension and follow its provider-specific state and
   lifecycle-marker rules.
3. Create or update current lifecycle status when the provider supports visible
   status updates.
4. Classify actionability, scope, blockers, and integration strategy.
5. Select or create an isolated work area according to repo guidance.
6. Implement only clear, in-scope work.
7. Infer verification from repo guidance, touched-surface docs, scripts,
   package metadata, CI workflows, and touched files.
8. Run item-level verification.
9. Auto-fix only deterministic formatter, generated-file, or lint failures.
10. Refresh live provider state, comments, lifecycle markers, linked work, and
    git state before integration handoff or direct integration; escalate if
    safety changed.
11. If the selected strategy requires a pull request, prepare the issue branch
    and hand off PR creation, updates, checks, reviews, merge, and PR cleanup to
    `pr-ops`; do not perform those PR lifecycle actions in `issue-ops`.
12. If the selected strategy is direct integration, integrate only after live
    state is still safe and rerun required verification when the base branch or
    tested result changes.
13. When a delegated PR lifecycle reports a merged result, refresh live issue
    state, comments, lifecycle markers, and linked work before closure or final
    lifecycle writes.
14. Update lifecycle status, close or complete the item when allowed, and clean
    up only issue work areas owned by this run.

## Ask Vs Continue

Continue autonomously when the item target, repository, provider tooling,
permissions, work area, verification path, and integration or handoff path are
all clear.

Ask the user only for global blockers that stop the run:

- tracker or repository cannot be identified;
- authentication is missing or unusable;
- write permission is missing for a requested write operation;
- required verification tooling is missing and no repo-documented substitute
  exists;
- the base branch, integration policy, or `pr-ops` handoff path cannot be
  determined.

For item-local ambiguity, update the lifecycle status when possible, mark the
item escalated, record the evidence, and continue the queue. Item-local
ambiguity includes unclear acceptance criteria, conflicting maintainer comments,
duplicate precedence, unsafe existing work, uncertain product contract,
non-mechanical verification failure, or any escalation gate.

## Escalation Gates

Escalation means stop the affected item, record current status through the
provider when possible, preserve evidence without exposing sensitive detail,
and continue the queue when possible. Stop the whole run only for global
blockers.

Escalate on:

- wrong repository, wrong account, missing permission, or unexpected provider
  tooling route;
- ambiguous scope, contradictory requirements, unclear product contract, or
  duplicate precedence requiring maintainer judgment;
- security, auth, secrets, credentials, tokens, signing, workflow permissions,
  personal access tokens, secret scanning, repository settings, or sensitive
  history cleanup;
- dependency add, remove, upgrade, downgrade, replacement, or lockfile changes,
  unless the item explicitly targets that dependency change;
- repo-wide guidance or agent behavior policy changes, unless explicitly
  targeted by the item or mechanically required by an in-scope change;
- destructive or hard-to-reverse operations;
- stale state, concurrent actor changes, ownership conflicts, active maintainer
  discussion, or a lifecycle marker from another current actor;
- public communication that rejects a request, assigns blame, makes a
  commitment, asks the reporter to do work, or exposes sensitive detail;
- untrusted issue content execution before inspection proves it safe;
- verification unavailable, non-mechanical failure, local/remote disagreement,
  repeated no-progress auto-fix, conflicts, push rejection, protected-branch
  mismatch, dirty owned work areas, or non-trivial branch history cleanup;
- unclear generated artifact provenance, unusual cost, unusual runtime, unusual
  API use, release/version ambiguity, or external repository boundaries;
- delegated `pr-ops` lifecycle escalation, unless the item can safely complete
  through another explicitly authorized strategy.

## Output

End with a concise report:

- completed count and item identifiers;
- escalated count and item identifiers with gate names;
- skipped count and item identifiers with reasons;
- remaining count when a queue was bounded;
- provider extensions loaded;
- provider tooling route and MCP availability when applicable;
- integration strategy;
- delegated `pr-ops` result when pull-request handoff was used;
- lifecycle marker state;
- verification summary;
- global blocker when the run stopped early;
- lifecycle ledger path when a ledger entry was written.

These fields are the output footer/disclosure contract. Preserve them in
wrappers, delegated agents, and provider-specific completion reports.

Do not write a separate local summary file.
