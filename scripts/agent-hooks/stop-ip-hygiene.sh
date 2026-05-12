#!/usr/bin/env bash
set -euo pipefail

hook_name="ip-hygiene"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_init "ip-hygiene" || exit 0
stop_hook_should_continue || exit 0

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
      /^\.agents\/plugins\/marketplace\.json$/ { print; next }
      /^\.codex\/agents\/[^/]+\.toml$/ { print; next }
      /^\.claude\/skills\/[^/]+\// { print; next }
      /^(CLAUDE|AGENTS|README)\.md$/ { print; next }
    ' |
    sort -u
)

if [[ -z "$changed" ]]; then
  debug_log "skip-no-ip-hygiene-changes"
  exit 0
fi

targets=$(
  awk -F/ '
    $1 == ".claude" && $2 == "skills" && NF >= 3 {
      print ".claude/skills/" $3
    }
    $1 == ".codex" && $2 == "agents" && NF >= 3 {
      print ".codex/agents/" $3
    }
    $1 == ".agents" && $2 == "plugins" {
      print ".agents/plugins/marketplace.json"
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
    $1 ~ /^souroldgeezer-/ && ($2 == ".claude-plugin" || $2 == ".codex-plugin") {
      print $1
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
  "Before finishing, run the repo-internal IP hygiene triage in \`.claude/skills/ip-hygiene/SKILL.md\` for these changed surfaces." \
  "Report the resulting output contract line: \`nothing to check\`, \`checked: ...\`, \`fixed: ...\`, or \`deferred drive-by observation ...\`."
