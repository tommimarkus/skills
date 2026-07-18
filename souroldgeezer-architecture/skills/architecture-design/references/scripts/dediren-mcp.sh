#!/usr/bin/env bash
# Launcher for the bundled dediren Model Context Protocol (MCP) stdio server.
#
# Declared as the plugin's `mcpServers.dediren` command (plugin.json). Claude Code
# spawns and owns this process automatically when the plugin is enabled; stdout
# carries JSON-RPC only.
#
# Resolve-on-demand, bounded. Plugin MCP servers auto-start every session, and a
# stdio server that exits at spawn gets no auto-retry — it stays dead until the
# next session or `/reload-plugins`. So a launcher that merely fail-fasts when the
# bundle is missing guarantees a dead session after every pin bump (the pinned
# bundle changes; the shared ${CLAUDE_PLUGIN_DATA} cache still holds the old one).
#
# The bundle caches per-user under ${CLAUDE_PLUGIN_DATA} (set in plugin.json), not
# per-project, so resolving here downloads at most once per pinned version per user
# — not once per repo. The fast path (bundle already resolved) does NO network I/O.
# Only a cold cache resolves, and that resolve is bounded (the resolver caps curl
# with --connect-timeout/--max-time and the install lock with `flock -w`) so it can
# never hang session start. Session start is non-blocking in Claude Code — only a
# turn that needs a `dediren_*` tool waits — so the one-time resolve is cheap.
# `--ensure-bundle` prints to stdout, which on this launcher is the JSON-RPC
# channel, so its output is redirected away. Java 21+ is a host prerequisite; if it
# is absent the `exec` below fails and the server does not start (non-fatal).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin="$("$script_dir/dediren-release.sh" --print-path)"
bundle_dir="$("$script_dir/dediren-release.sh" --bundle-dir)"

if [ ! -x "$bin" ] || [ ! -f "$bundle_dir/bundle.json" ]; then
  if ! "$script_dir/dediren-release.sh" --ensure-bundle >&2; then
    printf 'dediren-mcp: on-demand bundle resolve failed; MCP server not started (will retry next session).\n' >&2
    exit 1
  fi
fi

root="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
  printf 'dediren-mcp: CLAUDE_PROJECT_DIR unset; using %s as the workspace root.\n' "$root" >&2
fi
if [ ! -d "$root" ]; then
  printf 'dediren-mcp: workspace root %s is not a directory; tool paths will not resolve.\n' "$root" >&2
fi
exec "$bin" mcp --root "$root" "$@"
