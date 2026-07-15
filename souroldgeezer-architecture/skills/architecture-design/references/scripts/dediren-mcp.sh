#!/usr/bin/env bash
# Launcher for the bundled dediren Model Context Protocol (MCP) stdio server.
#
# Declared as the plugin's `mcpServers.dediren` command (plugin.json). Claude Code
# spawns and owns this process when the plugin is enabled; stdout carries JSON-RPC
# only. It resolves the pinned dediren release bundle through the sibling resolver
# (downloading on first use into ${CLAUDE_PLUGIN_DATA} via the DEDIREN_CACHE_DIR the
# mcpServers env block sets), then execs the bundle's `dediren mcp` server rooted at
# the project directory so every tool path resolves inside the user's workspace.
#
# Java 21+ is a host prerequisite (the bundle is Java-backed), exactly as a Node- or
# Python-based plugin MCP server needs its runtime installed. If the bundle cannot be
# resolved or Java 21+ is absent, the resolver exits non-zero and the MCP server never
# starts; the architecture-design skill detects the unavailable server and caps its
# runtime evidence at source-valid rather than failing.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dediren="$("$script_dir/dediren-release.sh" --ensure)"

exec "$dediren" mcp --root "${CLAUDE_PROJECT_DIR:-$PWD}" "$@"
