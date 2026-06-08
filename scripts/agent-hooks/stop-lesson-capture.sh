#!/usr/bin/env bash
set -euo pipefail

hook_name="lesson-capture"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_init "lesson-capture" || exit 0
stop_hook_should_continue || exit 0

# Layer 2 gate: only skill-authoring surfaces count (developing the skills,
# not running them). Same surface set as stop-ip-hygiene.sh.
changed=$(
  {
    git -C "$repo_root" diff --name-only main --
    git -C "$repo_root" ls-files --others --exclude-standard
  } 2>/dev/null |
    awk '
      /^souroldgeezer-[^/]+\/skills\/[^/]+\/(SKILL\.md$|extensions\/|references\/|fixtures\/|templates\/|scripts\/|agents\/openai\.yaml$)/ { print; next }
      /^souroldgeezer-[^/]+\/agents\/[^/]+\.md$/ { print; next }
      /^souroldgeezer-[^/]+\/docs\/[^/]+-reference\// { print; next }
      /^souroldgeezer-[^/]+\/\.(claude-plugin|codex-plugin)\/plugin\.json$/ { print; next }
      /^\.claude-plugin\/marketplace\.json$/ { print; next }
      /^\.claude\/skills\/[^/]+\// { print; next }
      /^(CLAUDE|AGENTS|README)\.md$/ { print; next }
    ' |
    sort -u
)
if [[ -z "$changed" ]]; then
  debug_log "skip-no-authoring-surface"
  exit 0
fi

# Correction signal in this session's user turns? Deterministic, conservative.
transcript_path=$(jq -r 'if (.transcript_path | type) == "string" then .transcript_path else "" end' <<<"$input")
if [[ -z "$transcript_path" ]]; then
  debug_log "skip-no-transcript"
  exit 0
fi
signals=$(python3 "$hook_dir/../lessons_capture_signals.py" "$transcript_path" 2>/dev/null || true)
if [[ -z "$signals" ]]; then
  debug_log "skip-no-correction-signal"
  exit 0
fi

targets="$signals"
stop_hook_mark_prompted
stop_hook_emit_block \
  "Skill-authoring corrections this session may hold a reusable lesson." \
  "Before finishing, follow the lesson-capture workflow in \`.claude/skills/lesson-capture/SKILL.md\` for the changed skill-craft surfaces. First confirm this was Layer-2 (developing the skills), not Layer-1 (a skill's runtime output), and not a one-off; if so, record nothing." \
  "Stage at most one generalizable candidate via \`python3 scripts/lessons_ledger.py append ...\`."
