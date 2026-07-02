#!/usr/bin/env bash
set -euo pipefail

hook_name="ip-hygiene"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_init "ip-hygiene" || exit 0
stop_hook_should_continue || exit 0

changed=$(stop_hook_changed_since_main | stop_hook_filter_authoring_surfaces)

if [[ -z "$changed" ]]; then
  debug_log "skip-no-ip-hygiene-changes"
  exit 0
fi

targets=$(
  awk -F/ '
    $1 == ".claude" && $2 == "skills" && NF >= 3 {
      print ".claude/skills/" $3
    }
    $1 == "internal-skills" && NF >= 2 {
      print "internal-skills/" $2
    }
    $1 == ".claude-plugin" && $2 == "marketplace.json" {
      print ".claude-plugin/marketplace.json"
    }
    $1 ~ /^souroldgeezer-/ && $2 == "skills" && NF >= 3 {
      print $1 "/skills/" $3
    }
    $1 ~ /^souroldgeezer-/ && $2 == "agents" && NF >= 3 {
      print $1 "/agents/" $3
    }
    $1 ~ /^souroldgeezer-/ && $2 == "docs" && NF >= 3 {
      print $1 "/docs/" $3
    }
    $1 ~ /^souroldgeezer-/ && $2 == ".claude-plugin" {
      print $1
    }
    $1 == "CLAUDE.md" || $1 == "README.md" {
      print $1
    }
  ' <<<"$changed" |
    sort -u
)

stop_hook_mark_prompted

stop_hook_emit_block \
  "IP hygiene scoped surfaces changed in this task." \
  "Before finishing, run the IP hygiene triage in \`souroldgeezer-audit/skills/ip-hygiene/SKILL.md\` for these changed surfaces." \
  "Report the resulting output contract line: \`nothing to check\`, \`checked: ...\`, \`fixed: ...\`, or \`deferred drive-by observation ...\`."
