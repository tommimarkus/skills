#!/usr/bin/env bash
# lean-audit:dup-intentional — irreducible Stop-hook wrapper: every hook must
# independently self-locate, source stop-hook-lib.sh, and emit the same
# bootstrap/mark/emit contract; the shared logic is already extracted to the lib.
set -euo pipefail

hook_name="lesson-capture"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_bootstrap "lesson-capture" || exit 0

# Layer 2 gate: a skill-authoring surface changed (developing the skills, not
# running them), OR the transcript records an audit-skill / skill-architecture
# report run — a read-only audit session leaves no changed file but can still hold
# a lesson. Any transcript parse error fails open to the authoring-only behavior.
transcript_path=$(jq -r 'if (.transcript_path | type) == "string" then .transcript_path else "" end' <<<"$input")
changed=$(stop_hook_changed_since_main | stop_hook_filter_authoring_surfaces)
audit_runs=""
if [[ -z "$changed" && -n "$transcript_path" ]]; then
  audit_runs=$(python3 "$hook_dir/../lessons_capture_signals.py" --audit-runs "$transcript_path" 2>/dev/null || true)
  if [[ -z "$audit_runs" ]]; then
    debug_log "skip-no-authoring-surface"
    exit 0
  fi
elif [[ -z "$changed" ]]; then
  debug_log "skip-no-authoring-surface"
  exit 0
fi

# Authoring surface changed → wake the capture skill's judgment. The capture skill
# (the same in-session model, with full conversation context) decides whether any
# user correction / question / steering OR a self-correction this session holds a
# generalizable Layer-2 lesson. Deterministic correction phrases are passed only as
# an orienting hint — never a gate.
signals=""
if [[ -n "$transcript_path" ]]; then
  signals=$(python3 "$hook_dir/../lessons_capture_signals.py" "$transcript_path" 2>/dev/null || true)
fi

targets=""
if [[ -n "$signals" ]]; then
  phrase_hint="Explicit correction phrases seen this session (hint, not a gate): ${signals//$'\n'/, }."
else
  phrase_hint="No explicit correction phrases matched — judge from the session yourself, including any wrong path you reversed."
fi

session_kind="This skill-authoring session"
if [[ -n "$audit_runs" ]]; then
  session_kind="This read-only audit session (no authoring surface changed; ran: ${audit_runs//$'\n'/, })"
fi

stop_hook_mark_prompted
stop_hook_emit_block \
  "$session_kind may hold a reusable lesson." \
  "Before finishing, follow the lesson-capture workflow in \`internal-skills/lesson-capture/SKILL.md\` for the changed skill-craft surfaces. Judge whether anything this session revealed a generalizable Layer-2 rule — a correction, pointed question, or steering from the user, OR a wrong path you took and corrected yourself. Confirm it is Layer-2 (developing the skills), not Layer-1 (a skill's runtime output), and not a one-off; if not, record nothing. $phrase_hint" \
  "Stage at most one generalizable candidate as a \`lesson-candidate\` GitHub issue per the lesson-capture workflow (render + secret-scan + dedup + create; fail-open)."
