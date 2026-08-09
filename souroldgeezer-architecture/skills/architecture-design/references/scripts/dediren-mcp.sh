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

if [ -n "${DEDIREN_COMMAND:-}" ]; then
  dediren_command="$DEDIREN_COMMAND"
  if [[ "$dediren_command" == */* ]] && [ ! -x "$dediren_command" ]; then
    printf 'dediren-mcp: DEDIREN_COMMAND is not executable: %s\n' "$dediren_command" >&2
    exit 127
  fi
  if [[ "$dediren_command" != */* ]] && ! command -v "$dediren_command" >/dev/null 2>&1; then
    printf 'dediren-mcp: DEDIREN_COMMAND was not found on PATH: %s\n' "$dediren_command" >&2
    exit 127
  fi
elif command -v dediren >/dev/null 2>&1; then
  dediren_command="dediren"
else
  # The pre-multi-harness adapter installed verified release bundles here. Do
  # not strand that existing installation during the host-managed migration:
  # use the newest executable already present, but never download or pin one.
  legacy_root="${XDG_CACHE_HOME:-$HOME/.cache}/dediren/releases"
  dediren_command=""
  best_key=""
  shopt -s nullglob
  for candidate in "$legacy_root"/dediren-agent-bundle-*/bin/dediren; do
    [ -x "$candidate" ] || continue
    bundle="${candidate%/bin/dediren}"
    version="${bundle##*/dediren-agent-bundle-}"
    if [[ "$version" =~ ^([0-9]{4})\.([0-9]{2})\.([0-9]+)$ ]]; then
      printf -v key '%04d%02d%09d' \
        "$((10#${BASH_REMATCH[1]}))" \
        "$((10#${BASH_REMATCH[2]}))" \
        "$((10#${BASH_REMATCH[3]}))"
      if [ -z "$best_key" ] || [[ "$key" > "$best_key" ]]; then
        best_key="$key"
        dediren_command="$candidate"
      fi
    fi
  done
  shopt -u nullglob
  if [ -z "$dediren_command" ]; then
    printf 'dediren-mcp: install the current Dediren CLI on PATH or set DEDIREN_COMMAND.\n' >&2
    exit 127
  fi
fi

if [[ "$dediren_command" == */* ]]; then
  dediren_dir="$(cd "$(dirname "$dediren_command")" && pwd -P)"
  dediren_command="$dediren_dir/${dediren_command##*/}"
else
  dediren_command="$(command -v "$dediren_command")"
fi

printf 'dediren-mcp: exec' >&2
printf ' %q' "$dediren_command" mcp --root "$root" "$@" >&2
printf '\n' >&2
exec "$dediren_command" mcp --root "$root" "$@"
