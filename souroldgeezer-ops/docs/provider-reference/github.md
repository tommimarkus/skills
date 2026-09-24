# GitHub Provider Reference

GitHub tooling order for `issue-ops` and `pr-ops`, plus the GitHub view of the
shared [provider-lifecycle-core.md](provider-lifecycle-core.md) lifecycle and
escalation sections. Both skills' `extensions/github.md` link the sections below
and add only the GitHub issue or pull-request specifics.

## Tooling Order

Select the route separately for each operation. Use the best available GitHub
integration in this order:

1. GitHub MCP after verifying active session routing and repository identity,
   when it exposes the requested operation and can perform it.
2. `gh` CLI after verifying `gh auth status` and repository context, when the
   MCP route is absent or lacks that operation.
3. GitHub REST API when the MCP and `gh` routes are absent or lack that
   operation, after verifying an authorized credential and repository identity.

A connected server does not establish that every operation is available. If a
route lacks the needed operation, continue down the order for that operation;
never treat missing authentication or permission as a capability gap to bypass.
Before any write, verify the selected route's account, repository, and write
authority. Never broaden the user's requested action or target when changing
routes.

Issue references in commits and PR text must not trigger provider auto-close
before issue verification and the required final lifecycle marker are complete.
Use a non-closing reference until then, and explicitly close the issue only
after re-reading live state and writing the final marker. If integration has
already auto-closed it, reconcile the live closed state after verification and
write the marker as a later event; do not report that the marker preceded
closure. See [GitHub's closing-keyword behavior](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).

If the selected route points at the wrong account or repository, escalate the
item (issue or PR/MR).

## Lifecycle Marker Mechanics

Apply [provider-lifecycle-core.md § Lifecycle marker mechanics](provider-lifecycle-core.md#lifecycle-marker-mechanics).
GitHub templates: `issue-ops:github:v1`, `pr-ops:github:v1`.

## Shared Escalation Gates

Apply [provider-lifecycle-core.md § Escalation gates](provider-lifecycle-core.md#escalation-gates)
(on GitHub, "CI or pipeline permissions" covers GitHub Actions).
