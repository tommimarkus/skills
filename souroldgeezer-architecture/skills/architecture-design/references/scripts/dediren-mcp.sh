#!/usr/bin/env bash
# Launcher for the host-managed Dediren Model Context Protocol (MCP) stdio server.
#
# The default lane starts a compatibility router. It answers both legacy
# initialize and current stateless discovery, then gets the live tool catalog
# from the externally installed Dediren CLI. Each tool call supplies an explicit
# workspaceRoot and is routed to one Dediren process for that root. The plugin
# neither bundles nor pins Dediren; update the host installation independently.
# stdout carries JSON-RPC only.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${1:-}" != "--upstream" ]; then
  exec python3 "$script_dir/dediren-mcp-router.py" "$@"
fi

shift
if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
  printf 'dediren-mcp: --upstream requires one workspace directory.\n' >&2
  exit 64
fi
root="$(cd "$1" && pwd -P)"
shift
dediren_command="${DEDIREN_COMMAND:-dediren}"
if [[ "$dediren_command" == */* ]]; then
  if [ ! -x "$dediren_command" ]; then
    printf 'dediren-mcp: DEDIREN_COMMAND is not executable: %s\n' "$dediren_command" >&2
    exit 127
  fi
elif ! command -v "$dediren_command" >/dev/null 2>&1; then
  printf 'dediren-mcp: install the current Dediren CLI on PATH or set DEDIREN_COMMAND.\n' >&2
  exit 127
fi
exec "$dediren_command" mcp --root "$root" "$@"
