#!/usr/bin/env bash
set -euo pipefail

hook_name="skill-architecture"
hook_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=scripts/agent-hooks/stop-hook-lib.sh
source "$hook_dir/stop-hook-lib.sh"

stop_hook_bootstrap "skill-architecture" || exit 0

# Union of the surfaces the removed evaluate-skill + plugin-eval hooks watched
# (deliberately narrower than stop_hook_filter_authoring_surfaces).
changed=$(
  stop_hook_changed_since_main |
    awk '
      /^internal-skills\/[^/]+\// { print; next }
      /^\.claude\/skills\/[^/]+\// { print; next }
      /^\.claude-plugin\/marketplace\.json$/ { print; next }
      /^souroldgeezer-[^/]+\/skills\/[^/]+\// { print; next }
      /^souroldgeezer-[^/]+\/agents\/[^/]+\.md$/ { print; next }
      /^souroldgeezer-[^/]+\/\.claude-plugin\/plugin\.json$/ { print; next }
    ' |
    sort -u
)

if [[ -z "$changed" ]]; then
  debug_log "skip-no-architecture-surface"
  exit 0
fi

targets=$(
  awk -F/ '
    $1 == "internal-skills" && NF >= 2 { print "internal-skills/" $2 }
    $1 == ".claude" && $2 == "skills" && NF >= 3 { print ".claude/skills/" $3 }
    $1 == ".claude-plugin" && $2 == "marketplace.json" { print "." }
    $1 ~ /^souroldgeezer-/ && $2 == "skills" && NF >= 3 { print $1 "/skills/" $3 }
    $1 ~ /^souroldgeezer-/ && $2 == "agents" && NF >= 3 { print $1 }
    $1 ~ /^souroldgeezer-/ && $2 == ".claude-plugin" { print $1 }
  ' <<<"$changed" |
    sort -u
)

stop_hook_mark_prompted

stop_hook_emit_block \
  "Skill or plugin surfaces changed in this task." \
  "Before finishing, run the first-party skill-architecture report (\`bash scripts/skill-architecture-report.sh\`, or \`uv run python scripts/skill_architecture_report.py .\`) and address its findings on these changed targets." \
  "Report the relevant findings (trigger metadata, manifest/marketplace sync, agent drift) or explicitly state why a target is out of scope. The report scans the whole repo; do not introduce new findings beyond the existing baseline."
