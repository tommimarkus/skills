# GitHub Provider Reference

GitHub tooling order for `issue-ops` and `pr-ops`, plus the GitHub view of the
shared [provider-lifecycle-core.md](provider-lifecycle-core.md) lifecycle and
escalation sections. Both skills' `extensions/github.md` link the sections below
and add only the GitHub issue or pull-request specifics.

## Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing and repository identity.
2. `gh` CLI after verifying `gh auth status` and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

If the selected route points at the wrong account or repository, escalate the
item (issue or PR/MR).

## Lifecycle Marker Mechanics

Apply [provider-lifecycle-core.md § Lifecycle marker mechanics](provider-lifecycle-core.md#lifecycle-marker-mechanics).
GitHub templates: `issue-ops:github:v1`, `pr-ops:github:v1`.

## Shared Escalation Gates

Apply [provider-lifecycle-core.md § Escalation gates](provider-lifecycle-core.md#escalation-gates)
(on GitHub, "CI or pipeline permissions" covers GitHub Actions).
