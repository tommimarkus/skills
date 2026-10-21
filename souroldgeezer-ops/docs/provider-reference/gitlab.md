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

Apply [provider-lifecycle-core.md § Route selection](provider-lifecycle-core.md#route-selection)
to this order; the target is the host and project.
