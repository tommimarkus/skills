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
  validate_marketplace_entry() {
    local runtime="$1" plugin="$2" source source_kind plugin_dir manifest invalid_label
    if [ "$runtime" = "claude" ]; then
      source="$(jq -r '.source' <<<"$plugin")"
      manifest=".claude-plugin/plugin.json"
      invalid_label="Invalid marketplace source"
    else
      source_kind="$(jq -r '.source.source' <<<"$plugin")"
      source="$(jq -r '.source.path' <<<"$plugin")"
      test "$source_kind" = "local"
      manifest=".codex-plugin/plugin.json"
      invalid_label="Invalid Codex marketplace source"
    fi

    case "$source" in
      ./*) ;;
      *)
        printf '%s: %s\n' "$invalid_label" "$source" >&2
        return 1
        ;;
    esac

    plugin_dir="${source#./}"
    test -d "$plugin_dir"
    test -f "$plugin_dir/$manifest"
    test -d "$plugin_dir/skills"
  }

  # lean-audit:dup-intentional:begin -- each marketplace is enumerated locally;
  # the shared entry helper owns all validation mechanics and runtime differences.
  jq -c '.plugins[]' .claude-plugin/marketplace.json | while IFS= read -r plugin; do
    validate_marketplace_entry claude "$plugin"
  done
  # lean-audit:dup-intentional:end

  jq -c '.plugins[]' .agents/plugins/marketplace.json | while IFS= read -r plugin; do
    validate_marketplace_entry codex "$plugin"
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
      (.version | type == "string" and test("^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$")) and
      (.description | type == "string") and
      (.author | type == "object") and
      (.license | type == "string") and
      .skills == "./skills/" and
      (.interface | type == "object")
    ' "$codex_manifest" >/dev/null

    # Runtime manifests own version identity; marketplace entries must never
    # carry a copy that can drift silently.
    jq -n -e \
      --argjson marketplace "$plugin" \
      --slurpfile claude "$claude_manifest" \
      '
      $marketplace.name == $claude[0].name and
      $marketplace.description == $claude[0].description and
      ($marketplace | has("version") | not)
      ' >/dev/null
  done
  jq -e 'all(.plugins[]; has("version") | not)' \
    .agents/plugins/marketplace.json >/dev/null

  echo "Plugin manifests OK"
}

validate_json
validate_toml
validate_marketplace_paths
validate_plugin_manifests
python scripts/check-runtime-metadata-parity.py --check .
bash scripts/test-stop-hooks.sh
echo "Stop hook regressions OK"
python -m unittest
