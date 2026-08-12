#!/usr/bin/env bash
# Launcher for the Dediren Model Context Protocol (MCP) stdio server.
#
# The default lane starts a compatibility router. It answers both legacy
# initialize and current stateless discovery, then gets the live tool catalog
# from the resolved Dediren CLI. Each tool call supplies an explicit
# workspaceRoot and is routed to one Dediren process for that root.
#
# The --upstream lane resolves the runtime and execs it. Resolution and
# provisioning live in dediren_runtime.py, which installs a pinned,
# checksum-verified release into the host's plugin data directory when no
# runtime is already available. Java stays host-managed.
# stdout carries JSON-RPC only.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${1:-}" != "--upstream" ]; then
  exec python3 "$script_dir/dediren-mcp-router.py" "$@"
fi

shift
if [ "$#" -lt 1 ]; then
  printf 'dediren-mcp: --upstream requires one workspace directory.\n' >&2
  exit 64
fi

exec python3 "$script_dir/dediren_runtime.py" --exec-upstream "$@"
