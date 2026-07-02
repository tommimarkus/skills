# GitHub Provider Reference

Tooling order, lifecycle-marker mechanics, and escalation gates that `issue-ops`
and `pr-ops` share when GitHub is the provider. Both skills' `extensions/github.md`
link the sections below and add only what differs for their own item — a GitHub
issue for `issue-ops`, a pull request for `pr-ops`. A skill's own core contracts
are unaffected by this reference.

## Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing and repository identity.
2. `gh` CLI after verifying `gh auth status` and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

If the selected route points at the wrong account or repository, escalate the
item (issue or PR/MR).

## Lifecycle Marker Mechanics

Write a lifecycle marker comment on the item unless the run lacks comment
permission. Update the latest marker from the same actor when possible. Add a new
comment only when editing is unavailable, editing would hide reply context, or a
fresh visible escalation is needed. Use current state only, not an event log.
Summarize verification instead of dumping command output. Use strict offset
timestamps. `Actor` identifies the agent runtime, such as `Claude Code`.

Each skill defines its own lifecycle-status marker templates (`issue-ops:github:v1`
and `pr-ops:github:v1`) with skill-relevant fields; keep the marker to one
current-state block per item. The final marker update is sufficient before the
terminal action — closing the issue, or merging or closing the PR — so do not add
a separate closing or completion comment unless updating the marker fails.

## Shared Escalation Gates

Escalate the affected item (issue or PR/MR) on:

- wrong account, wrong repository, missing permission, or unexpected GitHub tool
  routing;
- a concurrent lifecycle marker from another current actor;
- GitHub Actions permissions, workflow token handling, secret handling,
  repository settings, branch rules, or sensitive history cleanup;
- public comment text that rejects a request, assigns blame, makes a commitment,
  asks the reporter to do work, or exposes sensitive detail.
