#!/usr/bin/env bash
set -euo pipefail

# First-party wrapper for Lean's nonblocking reference/inventory/cost notice.
# The guard (load_cost_guard.py) does its own session enumeration, skill mapping,
# baseline lookup, and fail-open handling, reading the Stop JSON from stdin
# (it derives the repo root from payload.cwd). This wrapper only resolves the
# in-repo guard path and passes stdin through. No once-per-session marker: the
# guard is silent unless a reference defect, inventory change, or cost increase
# needs attention. Stop output is always nonblocking.

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
guard="$repo_root/souroldgeezer-audit/skills/lean-audit/references/scripts/load_cost_guard.py"
test -f "$guard" || exit 0
# uv is primary: it provisions/selects the required Python >=3.11 even when the
# system python3 is older. Pre-flight the interpreter so a missing/too-old one
# fails open (exit 0) rather than surfacing as a hook error; the guard's own exit
# code is propagated faithfully by exec; Stop notifications never deny completion.
if command -v uv >/dev/null 2>&1 && uv python find '>=3.11' >/dev/null 2>&1; then
  exec uv run "$guard"
elif command -v python3 >/dev/null 2>&1 \
  && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  exec python3 "$guard"
else
  exit 0
fi
