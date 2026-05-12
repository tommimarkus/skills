#!/usr/bin/env bash
set -euo pipefail

hook_name="plugin-eval"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_init "plugin-eval" || exit 0
stop_hook_should_continue || exit 0

changed=$(
  {
    git -C "$repo_root" diff --name-only main --
    git -C "$repo_root" ls-files --others --exclude-standard
  } 2>/dev/null |
    awk '
      /^\.claude-plugin\/marketplace\.json$/ { print }
      /^\.codex\/agents\/[^/]+\.toml$/ { print }
      /^souroldgeezer-[^/]+\/\.(claude-plugin|codex-plugin)\/plugin\.json$/ { print }
      /^souroldgeezer-[^/]+\/agents\/[^/]+\.md$/ { print }
      /^souroldgeezer-[^/]+\/skills\/[^/]+\/agents\/openai\.yaml$/ { print }
    ' |
    sort -u
)

if [[ -z "$changed" ]]; then
  debug_log "skip-no-plugin-changes"
  exit 0
fi

targets=$(
  awk -F/ '
    $1 == ".claude-plugin" && $2 == "marketplace.json" {
      print "."
    }
    $1 == ".codex" && $2 == "agents" {
      print "."
    }
    $1 ~ /^souroldgeezer-/ {
      print $1
    }
  ' <<<"$changed" |
    sort -u
)

stop_hook_mark_prompted

stop_hook_emit_block \
  "Plugin metadata or runtime surfaces changed in this task." \
  "Before finishing, invoke \`\$plugin-eval:plugin-eval\` and evaluate these targets or use it to route to the right plugin-eval workflow." \
  "Use \`plugin-eval start <target> --request \"What should I run next?\" --format markdown\` when the target is ambiguous."
