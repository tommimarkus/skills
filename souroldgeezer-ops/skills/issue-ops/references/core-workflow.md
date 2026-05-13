# Issue Ops Core Workflow

This reference contains the provider-neutral operating contract. Provider
extensions add mechanics; they do not override these rules unless the core skill
or the user explicitly says so.

## Evidence Contract

Before acting, inspect the user's requested scope, issue or work-item
identifiers or URLs, repository identity and remotes, repo guidance, current git
branch, status, and worktrees, available provider tooling and auth, linked work,
and existing lifecycle markers.

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
7. Infer verification from repo guidance, touched-surface docs, scripts, package
   metadata, CI workflows, and touched files.
8. Run item-level verification.
9. Auto-fix only deterministic formatter, generated-file, or lint failures.
10. Refresh live provider state, comments or notes, lifecycle markers, linked
    work, and git state before integration handoff or direct integration;
    escalate if safety changed.
11. If the selected strategy requires a pull request or merge request, prepare
    the issue branch and hand off creation, updates, checks, reviews, merge, and
    cleanup to `pr-ops`; do not perform those lifecycle actions in `issue-ops`.
12. If the selected strategy is direct integration, integrate only after live
    state is still safe and rerun required verification when the base branch or
    tested result changes.
13. When a delegated PR/MR lifecycle reports a merged result, refresh live issue
    state, comments or notes, lifecycle markers, and linked work before closure
    or final lifecycle writes.
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
provider when possible, preserve evidence without exposing sensitive detail, and
continue the queue when possible. Stop the whole run only for global blockers.

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

## Output Footer

End with a concise report that includes:

- completed count and item identifiers;
- escalated count and item identifiers with gate names;
- skipped count and item identifiers with reasons;
- remaining count when a queue was bounded;
- provider extensions loaded;
- provider tooling route and MCP availability when applicable;
- integration strategy;
- delegated `pr-ops` result when pull-request or merge-request handoff was used;
- lifecycle marker state;
- verification summary;
- global blocker when the run stopped early;
- lifecycle ledger path when a ledger entry was written.

These fields are the output footer/disclosure contract. Preserve them in
wrappers, delegated agents, and provider-specific completion reports.
