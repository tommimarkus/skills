# GitLab Provider Reference

The GitLab tooling order below is identical for issue and merge-request work, so
`issue-ops` and `pr-ops` both link it from `extensions/gitlab.md` rather than
restating it. Each extension keeps its own IID handling, authoritative sources,
state resolution, and escalation gates, and its skill's core contracts are
unaffected by this reference.

## Tooling Order

Select the route separately for each operation. Use the best available GitLab
integration in this order:

1. A configured GitLab MCP server, connector, or provider integration after
   verifying active session routing, authenticated account, host, and project,
   when it exposes the requested operation and can perform it.
2. `glab` CLI after verifying `glab auth status`, repository context, and host.
   Use `-R` with `group/project`, full URL, or Git URL when the current
   directory context is ambiguous; use this route when MCP is absent or lacks
   the requested operation.
3. GitLab REST API v4 when provider tooling and `glab` are absent or lack the
   requested operation. Use `PRIVATE-TOKEN` or `Authorization: Bearer`, the
   URL-encoded path form for project paths, the item IID (`issue_iid` or
   `merge_request_iid`), and pagination-aware reads.

A connected server does not establish that every operation is available. If a
route lacks the needed operation, continue down the order for that operation;
never treat missing authentication or permission as a capability gap to bypass.
Before any write, verify the selected route's account, host, project, and write
authority. Never broaden the user's requested action or target when changing
routes.

If the selected route points at the wrong account, host, or project, escalate
the item (issue or PR/MR).
