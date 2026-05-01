#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
python_cache="${PYTHONPYCACHEPREFIX:-$repo_root/.cache/python/pycache}"

cd "$repo_root"
mkdir -p "$python_cache"
exec env -u VIRTUAL_ENV PYTHONPYCACHEPREFIX="$python_cache" uv run python scripts/skill_architecture_report.py "$@"
