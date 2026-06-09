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

# Authoring surface changed → wake the capture skill's judgment. The capture skill
# (the same in-session model, with full conversation context) decides whether any
# user correction / question / steering OR a self-correction this session holds a
# generalizable Layer-2 lesson. Deterministic correction phrases are passed only as
# an orienting hint — never a gate.
transcript_path=$(jq -r 'if (.transcript_path | type) == "string" then .transcript_path else "" end' <<<"$input")
signals=""
if [[ -n "$transcript_path" ]]; then
  signals=$(python3 "$hook_dir/../lessons_capture_signals.py" "$transcript_path" 2>/dev/null || true)
fi

targets="$signals"
if [[ -n "$signals" ]]; then
  phrase_hint="Explicit correction phrases seen this session (hint, not a gate): ${signals//$'\n'/, }."
else
  phrase_hint="No explicit correction phrases matched — judge from the session yourself, including any wrong path you reversed."
fi

stop_hook_mark_prompted
stop_hook_emit_block \
  "This skill-authoring session may hold a reusable lesson." \
  "Before finishing, follow the lesson-capture workflow in \`.claude/skills/lesson-capture/SKILL.md\` for the changed skill-craft surfaces. Judge whether anything this session revealed a generalizable Layer-2 rule — a correction, pointed question, or steering from the user, OR a wrong path you took and corrected yourself. Confirm it is Layer-2 (developing the skills), not Layer-1 (a skill's runtime output), and not a one-off; if not, record nothing. $phrase_hint" \
  "Stage at most one generalizable candidate via \`python3 scripts/lessons_ledger.py append ...\`."
