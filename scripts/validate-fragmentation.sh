#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

cd "$repo_root"

validate_json() {
  find . \
    -path './.worktrees' -prune -o \
    -name '*.json' -type f -print0 \
    | xargs -0 -n1 jq -e . >/dev/null

  echo "JSON OK"
}

validate_toml() {
  python - <<'PY'
from pathlib import Path
import tomllib

for path in Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text(encoding="utf-8"))

print("TOML OK")
PY
}

validate_marketplace_paths() {
  jq -c '.plugins[]' .claude-plugin/marketplace.json | while IFS= read -r plugin; do
    source="$(jq -r '.source' <<<"$plugin")"

    case "$source" in
      ./*) ;;
      *)
        printf 'Invalid marketplace source: %s\n' "$source" >&2
        return 1
        ;;
    esac

    plugin_dir="${source#./}"

    test -d "$plugin_dir"
    test -f "$plugin_dir/.claude-plugin/plugin.json"
    test -f "$plugin_dir/.codex-plugin/plugin.json"
    test -d "$plugin_dir/skills"
  done

  echo "Marketplace paths OK"
}

validate_plugin_manifests() {
  jq -c '.plugins[]' .claude-plugin/marketplace.json | while IFS= read -r plugin; do
    plugin_dir="$(jq -r '.source | sub("^./"; "")' <<<"$plugin")"
    claude_manifest="$plugin_dir/.claude-plugin/plugin.json"
    codex_manifest="$plugin_dir/.codex-plugin/plugin.json"

    jq -e '
      type == "object" and
      (.name | type == "string") and
      (.version | type == "string") and
      (.description | type == "string") and
      (.author | type == "object") and
      (.license | type == "string")
    ' "$claude_manifest" >/dev/null

    jq -e '
      type == "object" and
      (.name | type == "string") and
      (.version | type == "string") and
      (.description | type == "string") and
      (.skills == "./skills/") and
      (.interface | type == "object") and
      (.interface.defaultPrompt | type == "array") and
      (.interface.defaultPrompt | length <= 3)
    ' "$codex_manifest" >/dev/null

    jq -s -e '
      .[0].name == .[1].name and
      .[0].version == .[1].version and
      .[0].description == .[1].description
    ' "$claude_manifest" "$codex_manifest" >/dev/null

    jq -n -e \
      --argjson marketplace "$plugin" \
      --slurpfile claude "$claude_manifest" \
      '
      $marketplace.name == $claude[0].name and
      $marketplace.version == $claude[0].version and
      $marketplace.description == $claude[0].description
      ' >/dev/null
  done

  echo "Plugin manifests OK"
}

validate_json
validate_toml
validate_marketplace_paths
validate_plugin_manifests
python scripts/check-runtime-metadata-parity.py --check .
python -m unittest
