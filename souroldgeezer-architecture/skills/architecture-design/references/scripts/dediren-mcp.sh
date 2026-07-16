#!/usr/bin/env bash
# Launcher for the bundled dediren Model Context Protocol (MCP) stdio server.
#
# Declared as the plugin's `mcpServers.dediren` command (plugin.json). Claude Code
# spawns and owns this process automatically when the plugin is enabled; stdout
# carries JSON-RPC only.
#
# Fail-fast, no session-start network I/O. Plugin MCP servers auto-start every
# session, so this launcher must stay cheap: it starts the server ONLY when the
# pinned bundle is already resolved on disk (checked via the resolver's
# non-downloading `--print-path` / `--bundle-dir`). It never downloads. When the
# bundle is absent it exits non-zero and the server simply does not start — the
# architecture-design skill's internal fallback lane resolves the bundle on demand
# (via the sibling resolver, into the same ${CLAUDE_PLUGIN_DATA} cache) the first
# time architecture work runs, and the MCP server comes up on the next session or
# after `/reload-plugins`. Java 21+ is a host prerequisite; if it is absent the
# `exec` below fails and the server does not start (non-fatal).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin="$("$script_dir/dediren-release.sh" --print-path)"
bundle_dir="$("$script_dir/dediren-release.sh" --bundle-dir)"

if [ ! -x "$bin" ] || [ ! -f "$bundle_dir/bundle.json" ]; then
  printf 'dediren-mcp: pinned bundle not resolved yet; not starting the MCP server (no session-start download). The architecture-design skill resolves it on demand; the server starts next session or after /reload-plugins.\n' >&2
  exit 1
fi

root="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
  printf 'dediren-mcp: CLAUDE_PROJECT_DIR unset; using %s as the workspace root.\n' "$root" >&2
fi
if [ ! -d "$root" ]; then
  printf 'dediren-mcp: workspace root %s is not a directory; tool paths will not resolve.\n' "$root" >&2
fi
exec "$bin" mcp --root "$root" "$@"
