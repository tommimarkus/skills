# Runtime support

Use the [README installation commands](../README.md#install) for your host.
Claude Code and Codex support all five plugins and all 16 shared public skills.
Native Copilot CLI support currently covers `souroldgeezer-architecture` and
its `architecture-design` skill. The workflows are shared; discovery, tool
launch, permissions, and configuration belong to each host.

## Install and adapters

Claude reads `.claude-plugin/marketplace.json`; Codex reads
`.agents/plugins/marketplace.json`. Every plugin has Claude and legacy Codex
manifests. The architecture plugin also has the current Agent Plugins root
`plugin.json` and `mcp.json`, used by Codex and spec-aware Copilot.

| Host | Architecture MCP configuration | Runtime data |
|---|---|---|
| Claude Code | Inline launcher in `.claude-plugin/plugin.json` | Explicit `DEDIREN_HOME` from `${CLAUDE_PLUGIN_DATA}`. |
| Codex, Agent Plugins | Root `plugin.json` and `mcp.json` | Host exports `PLUGIN_ROOT` and `PLUGIN_DATA` into the child. |
| Codex, legacy fallback | `.codex-plugin/plugin.json` and `mcp/codex.mcp.json` | Literal paths, plugin-relative `cwd: "."`, no supplied plugin-data root. |
| Copilot CLI, Agent Plugins | Root `plugin.json` and `mcp.json`; ignores the legacy MCP file | Host exports absolute plugin-data variables; does not expand root-file tokens. |
| Copilot CLI, legacy fallback | `mcp/copilot.mcp.json` | Uses `${PLUGIN_ROOT}` and explicit `DEDIREN_HOME` from `${COPILOT_PLUGIN_DATA}`. |

The shared root `mcp.json` deliberately declares no `env` or `cwd`: Codex would
expand a token there while Copilot would leave it literal. The shared
launcher/router has no harness detection. It requires absolute `workspaceRoot`
per tool call and starts the upstream process in that project.

The router's startup/catalog timeout is 120 seconds and its tool-call timeout
is 360 seconds by default, configurable through the documented `DEDIREN_*`
overrides. Codex Agent Plugins uses the host's 30-second startup default; the
router answers initialization itself, before provisioning. In legacy adapters,
`startup_timeout_sec` is seconds and Copilot `timeout` is milliseconds. See the
[architecture adapter contract](../AGENTS.md#dediren-mcp-adapter-contract) for
all environment and process details.

Generic local-client compatibility means local stdio launch with Bash, Python,
Java 21+, absolute `workspaceRoot` per tool call, and either a host-provided
writable data directory, absolute `DEDIREN_HOME`, or explicit `DEDIREN_COMMAND`.
It is not a promise to maintain another harness. Streamable HTTP is future work
only for an explicit remote/shared multi-client service requirement.

## Dediren

For normal Linux, macOS, or WSL use, make Java 21+ available to the host; the
plugin provisions the pinned Dediren release when tools are first listed.
Java is host managed and is never downloaded by the plugin. An existing runtime
can take precedence: resolution is explicit command, managed install,
floor-compatible `PATH` executable, legacy migration cache, then provisioning.

Use the [Dediren runtime guide](../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md)
for the current pin/floor, download checks, environment overrides, offline
setup, and exact error codes. `--print-path` resolves an existing executable
without downloading; `--ensure` can provision one. Run diagnostics with the
MCP host's environment and check the returned executable, rather than assuming
`dediren` is on your shell's `PATH`.

Keep these limits beside architecture results:

- Direct UML/XMI exports expose assurance data. Native package-build results
  expose export status, artifact, and diagnostics; do not infer the same
  assurance from them.
- draw.io imports become generic graphs, not promoted ArchiMate/UML models.
  The layout engine replaces imported geometry and presentation hints.
- The standalone ASCII/text lane does not replace SVG as the evidence of
  record, and package builds do not select it.
- `DEDIREN_RENDER_EDGE_LABEL_OCCLUDED` retains the SVG but maps to `ARCH-R-3`
  until the affected label is visually clear or the limitation is disclosed.

The [architecture reference](../souroldgeezer-architecture/docs/architecture-reference/architecture.md)
owns these output contracts. Runtime smoke checks tool transport and discovery;
it does not prove that a particular rendered diagram is visually clear.

## Troubleshooting

| Symptom | Check and next action |
|---|---|
| A skill is missing | Confirm its plugin is installed: use Claude's `/plugin`, `codex plugin list --json`, or `copilot plugin list`. Compare with the support scope above; Copilot support is architecture-only. |
| Source edits do not appear | Inspect the installed cache path. Hosts can run a materialized copy rather than the source checkout. Refresh or reinstall that plugin from the intended local marketplace; restart a session that still loads the older copy. |
| Dediren tools are missing | Inspect the MCP server error and the host's selected adapter. Use the [server self-check](../souroldgeezer-architecture/skills/architecture-design/references/procedures/self-check.md); do not treat a shell-only missing environment variable as proof the host installation failed. |
| No data directory or runtime (exit 78) | Supply an absolute `DEDIREN_HOME` in the host's MCP environment, or point `DEDIREN_COMMAND` at an existing executable. Legacy Codex does not supply a plugin-data root. |
| Java is missing or too old (exit 69) | Run `java -version`, then make Java 21+ visible to the host process through its environment. A shell-only Java configuration may not reach the host. |
| Download or checksum failure | Follow the exact row in the [Dediren troubleshooting table](../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md#troubleshooting). Configure the documented proxy/offline lane for connection failures; do not bypass checksum or archive checks. |
| A lean hook does not fire | Confirm opt-in configuration, the current installed script path, Python 3.11+, and applicable trust review. The guards fail open on errors, so silence is not proof that enforcement ran. |
| A requested tool or model is unavailable | Follow the skill's reported stop or documented fallback. Installed skill text does not make the host expose that capability. |

## Optional hooks

Installing `lean-audit` enables neither of its guards. The
[hook recipe](../souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md)
explains the duplication PreToolUse guard and the fidelity/cost guard. It gives
separate Claude and Codex configuration, overrides, prerequisites, and
fail-open behavior.

Consumer-project hook commands need the real installed script path. Plugin
root variables belong to plugin-owned hook definitions; do not assume they
exist in project configuration. Review and trust new or changed Codex hooks.
For load-cost checks, Codex supports the post-edit Stop form; the Claude
PreToolUse load-cost adapter is not a supported Codex equivalent. Update
consumer paths after a plugin update.

## Verify or report a problem

Record the host/version, plugin/version and installed path, the requested
skill/task, and the exact error with credentials removed. Separate an
installation problem from a missing capability or an incorrect task result.
Use [contributing](contributing.md#validate-the-change) for the full local
validation and isolated host smoke. The
[maintenance smoke recipe](maintenance-procedures.md#dediren-upstream-release-adoption)
shows how to pin one executable with `DEDIREN_COMMAND` for the optional
`DEDIREN_RUNTIME_SMOKE=1` lane.

A missing standalone Codex plugin validator is a reported skip, not a pass.
CLI help and the repository smoke verify the installed host; upstream
[OpenAI plugin guidance](https://developers.openai.com/plugins/build/plugins)
provides additional packaging and hook context but may describe a different
manifest lane from the root adapter this repository tests.
