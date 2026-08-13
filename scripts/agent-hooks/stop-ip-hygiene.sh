#!/usr/bin/env bash
# lean-audit:dup-intentional — irreducible Stop-hook wrapper: every hook must
# independently self-locate, source stop-hook-lib.sh, and emit the same
# bootstrap/mark/emit contract; the shared logic is already extracted to the lib.
set -euo pipefail

hook_name="ip-hygiene"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_bootstrap "ip-hygiene" || exit 0
stop_hook_require_authoring_changes "skip-no-ip-hygiene-changes"

targets=$(
  awk -F/ '
    $1 == ".claude" && $2 == "skills" && NF >= 3 {
      print ".claude/skills/" $3
    }
    $1 == ".agents" && $2 == "skills" && NF >= 3 {
      print ".agents/skills/" $3
    }
    $1 == "internal-skills" && NF >= 2 {
      print "internal-skills/" $2
    }
    $1 == ".claude-plugin" && $2 == "marketplace.json" {
      print ".claude-plugin/marketplace.json"
    }
    $1 == ".agents" && $2 == "plugins" && $3 == "marketplace.json" {
      print ".agents/plugins/marketplace.json"
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
    $1 ~ /^souroldgeezer-/ && $2 == ".codex-plugin" {
      print $1
    }
    $1 ~ /^souroldgeezer-/ && ($2 == "plugin.json" || $2 == "mcp.json" || $2 == "mcp") {
      print $1
    }
    $1 == ".codex" && $2 == "hooks.json" {
      print ".codex/hooks.json"
    }
    $1 == ".claude" && $2 == "settings.json" {
      print ".claude/settings.json"
    }
    $1 == "docs" && $2 == "skill-architecture.md" {
      print "docs/skill-architecture.md"
    }
    $1 == "CLAUDE.md" || $1 == "AGENTS.md" || $1 == "README.md" {
      print $1
    }
  ' <<<"$changed" |
    sort -u
)

stop_hook_mark_prompted

stop_hook_emit_block \
  "IP hygiene scoped surfaces changed in this task." \
  "Before finishing, run the IP hygiene triage in \`souroldgeezer-audit/skills/ip-hygiene/SKILL.md\` for these changed surfaces." \
  "Report the resulting coded output contract: \`nothing to check\` or \`checked: ...\`; each finding's criterion, authority, severity, fact/inference, remediation or deferred observation, and counsel outcome; then exactly one \`triage gate:\` (triage) or \`in-depth verdict:\` (in-depth) line. Never report legal clearance."
