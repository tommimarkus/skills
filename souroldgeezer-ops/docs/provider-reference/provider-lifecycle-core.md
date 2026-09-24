# Provider Lifecycle Core

The provider-agnostic lifecycle-marker mechanics and escalation gates for
`issue-ops` and `pr-ops`. The provider references and each skill's provider
extension cite the two sections below and layer their own provider- and
item-specific detail on top.

## Lifecycle marker mechanics

When a skill's trigger calls for a marker, write it on the item unless the run
lacks comment or note permission. Update the latest marker from the same actor
when possible. Add a new comment or note only when editing is unavailable,
editing would hide reply context, or a fresh visible escalation is needed. Use
current state only, not an event log. Summarize verification instead of dumping
command output. Use strict offset timestamps. `Actor` identifies the agent
runtime, such as `Claude Code`.

Each skill and provider defines its own lifecycle-status marker templates — for
example `issue-ops:github:v1` or `pr-ops:gitlab:v1` — with the fields that matter
for the item; keep the marker to one current-state block per item. Complete
verification and write the required final issue marker before explicitly
closing an issue. The final marker update is sufficient before that terminal
action — closing the issue, or merging or closing the PR/MR — so do not add a
separate closing or completion comment unless updating the marker fails.

When commit messages or PR/MR text can trigger automatic issue closure, use a
non-closing issue reference until verification and the required final issue
marker are complete. Then close explicitly after re-reading live state. If an
integration already auto-closed the issue, report and reconcile the observed
state after verification; preserve the actual order of events and never claim
the marker preceded closure.

## Escalation gates

Escalate the affected item (issue or PR/MR) on:

- wrong account, wrong host or repository, missing permission, or unexpected
  provider tool routing;
- a concurrent lifecycle marker from another current actor;
- CI or pipeline permissions, workflow or job token handling, secret or CI/CD
  variable handling, repository or project settings, branch or protection
  rules, or sensitive history cleanup;
- public comment or note text that rejects a request, assigns blame, makes a
  commitment, asks the reporter to do work, or exposes sensitive detail.

Each provider extension adds its own gates on top — provider-specific routing
and reference ambiguity, tier or version differences, blocker and link state,
and handoff limits.
