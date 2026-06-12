#!/usr/bin/env bash
set -euo pipefail

hook_name="evaluate-skill"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_init "evaluate-skill" || exit 0
stop_hook_should_continue || exit 0

changed=$(
  {
    git -C "$repo_root" diff --name-only main --
    git -C "$repo_root" ls-files --others --exclude-standard
  } 2>/dev/null |
    awk '
      /^\.claude\/skills\/[^/]+\// { print }
      /^souroldgeezer-[^/]+\/skills\/[^/]+\// { print }
    ' |
    sort -u
)

if [[ -z "$changed" ]]; then
  debug_log "skip-no-skill-changes"
  exit 0
fi

targets=$(
  awk -F/ '
    $1 == ".claude" && $2 == "skills" && NF >= 3 {
      print ".claude/skills/" $3
    }
    $1 ~ /^souroldgeezer-/ && $2 == "skills" && NF >= 3 {
      print $1 "/skills/" $3
    }
  ' <<<"$changed" |
    sort -u
)

stop_hook_mark_prompted

# Runtime split: Claude Code (CLAUDECODE set) routes to the plugin-dev LLM-agent
# skills; Codex keeps the openai-curated plugin-eval plugin. Both runtimes exec
# this same script with no args, so the branch is on the runtime env signal.
if [[ -n "${CLAUDECODE:-}" ]]; then
  instruction="Before finishing, invoke the \`plugin-dev:skill-reviewer\` agent on these skill targets."
  hint="Run the plugin-dev:skill-reviewer agent (Claude Code) on each target and report the relevant findings, or explicitly state why a target is out of scope."
else
  instruction="Before finishing, invoke \`\$plugin-eval:evaluate-skill\` on these skill targets."
  hint="Use \`plugin-eval analyze <skill-dir> --format markdown\` and report the relevant findings or explicitly state why a target is out of scope."
fi

stop_hook_emit_block \
  "Skill files changed in this task." \
  "$instruction" \
  "$hint"
