#!/usr/bin/env bash
set -euo pipefail

# First-party wrapper for lean-audit's per-use cost/fidelity guard at Stop.
# The guard (load_cost_guard.py) does its own session enumeration, skill mapping,
# baseline lookup, and fail-open handling, reading the Stop JSON from stdin
# (it derives the repo root from payload.cwd). This wrapper only resolves the
# in-repo guard path and passes stdin through. No once-per-session marker: the
# guard is silent unless a fidelity floor is breached (block) or cost grows
# (advisory).

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
guard="$repo_root/souroldgeezer-audit/skills/lean-audit/references/scripts/load_cost_guard.py"
test -f "$guard" || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

exec python3 "$guard"
