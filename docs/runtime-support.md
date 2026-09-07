# Runtime support

The marketplace publishes one shared workflow per skill and host-specific packaging around it. Claude Code and Codex support all 16 shared public skills. Copilot CLI currently supports the MCP-equipped `architecture-design` plugin.

## Install and adapters

Use the [README install commands](../README.md#install). Claude’s marketplace is `.claude-plugin/marketplace.json`; Codex uses `.agents/plugins/marketplace.json` and legacy `.codex-plugin` manifests. The architecture plugin also supplies the current root Agent Plugins `plugin.json` and `mcp.json`; that root manifest is the native Copilot surface. The legacy Codex and Copilot MCP files remain fallback adapters.

| Host | Current architecture MCP lane | Plugin data behaviour |
|---|---|---|
| Claude Code | Claude manifest launches the shared router | `${CLAUDE_PLUGIN_DATA}` supplies the managed Dediren directory. |
| Codex | Root `plugin.json` plus `mcp.json`; legacy `.codex-plugin` remains available | Agent Plugins exports `PLUGIN_ROOT` and `PLUGIN_DATA`; the legacy lane receives no plugin data root. |
| Copilot CLI | Root Agent Plugins manifest and `mcp.json` | It exports plugin data variables but does not interpolate root `mcp.json`; `mcp/copilot.mcp.json` is legacy only. |

The shared root `mcp.json` declares no `env` or `cwd`: root-token expansion differs by host. The router receives an absolute `workspaceRoot` for every tool call and starts Dediren in that project. Generic local-client compatibility is limited to local stdio launch, Bash, Python, Java 21+, an absolute `workspaceRoot`, and either host data, absolute `DEDIREN_HOME`, or explicit `DEDIREN_COMMAND`.

## Dediren

The architecture plugin provisions the pinned Dediren release on first `tools/list`, after the router has answered initialization. Java 21+ is host managed. Runtime resolution is explicit command, managed install, compatible `PATH` executable, legacy cache, then provisioning. `--print-path` only resolves an existing runtime; `--ensure` may provision. The complete procedure is [dediren-install.md](../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md). Direct UML/XMI exports carry assurance data, while package builds carry only status, artifact, and diagnostics. Draw.io imports remain generic graphs, SVG remains the evidence of record, and `DEDIREN_RENDER_EDGE_LABEL_OCCLUDED` needs review or disclosure; the [architecture skill](../souroldgeezer-architecture/skills/architecture-design/SKILL.md) owns those task limits.

## Troubleshooting

| Symptom | Check | Action |
|---|---|---|
| A skill is missing or stale | Confirm its marketplace source and installed plugin | Re-add the current local clone path, then refresh or reinstall the named plugin. |
| MCP cannot find storage or a runtime | Read the server error; `--print-path` only works with host runtime variables | Provide absolute `DEDIREN_HOME` or `DEDIREN_COMMAND`; `--ensure` is the provisioning action. |
| Dediren reports Java or download failure | Check `java -version` and the procedure’s error row | Expose Java 21+ to the host; configure a proxy or use the documented air-gapped lane. |
| A lean hook does not fire | Confirm the consumer project’s opt-in hook and trust review | Use the installed script path and follow the [hook recipe](../souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md); installation alone never enables it. |

## Optional hooks

Installing `lean-audit` does not enable hooks. The guard is deliberately opt-in, fail-open, and requires a user-maintained installed script path in a consumer project. Claude and Codex configurations, trust review, and overrides are in the [hook recipe](../souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md).

## Support limits

Host capabilities, installed CLI versions, project configuration, and actual tool output determine what is available. A missing standalone Codex plugin validator is a reported skip, not a successful validation result. For repository changes, use [contributing](contributing.md).
