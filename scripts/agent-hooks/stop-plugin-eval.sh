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

# Runtime split: Claude Code (CLAUDECODE set) routes to the plugin-dev LLM-agent
# skills; Codex keeps the openai-curated plugin-eval plugin. Both runtimes exec
# this same script with no args, so the branch is on the runtime env signal.
if [[ -n "${CLAUDECODE:-}" ]]; then
  instruction="Before finishing, invoke the \`plugin-dev:plugin-validator\` agent and evaluate these targets."
  hint="Run the plugin-dev:plugin-validator agent (Claude Code) to check plugin structure and manifest sync, and report the findings or route to the right plugin-dev workflow."
else
  instruction="Before finishing, invoke \`\$plugin-eval:plugin-eval\` and evaluate these targets or use it to route to the right plugin-eval workflow."
  hint="Use \`plugin-eval start <target> --request \"What should I run next?\" --format markdown\` when the target is ambiguous."
fi

stop_hook_emit_block \
  "Plugin metadata or runtime surfaces changed in this task." \
  "$instruction" \
  "$hint"
