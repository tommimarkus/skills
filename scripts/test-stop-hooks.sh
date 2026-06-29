#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

make_fixture() {
  local fixture=$1
  mkdir -p "$fixture/scripts/agent-hooks" \
    "$fixture/souroldgeezer-design/.codex-plugin" \
    "$fixture/souroldgeezer-design/skills/software-design/agents" \
    "$fixture/.claude-plugin"

  cp "$repo_root"/scripts/agent-hooks/stop-*.sh "$fixture/scripts/agent-hooks/"

  cat >"$fixture/souroldgeezer-design/.codex-plugin/plugin.json" <<'JSON'
{"name":"souroldgeezer-design","version":"0.0.0","description":"Fixture plugin"}
JSON
  cat >"$fixture/.claude-plugin/marketplace.json" <<'JSON'
{"plugins":[{"name":"souroldgeezer-design","source":"./souroldgeezer-design"}]}
JSON
  cat >"$fixture/souroldgeezer-design/skills/software-design/SKILL.md" <<'MD'
---
name: software-design
description: Use when validating fixture skill changes.
---

# Software Design
MD
  cat >"$fixture/souroldgeezer-design/skills/software-design/agents/openai.yaml" <<'YAML'
name: software-design
YAML

  git -C "$fixture" init -q -b main
  git -C "$fixture" config user.email "hook-test@example.invalid"
  git -C "$fixture" config user.name "Hook Test"
  git -C "$fixture" add .
  git -C "$fixture" commit -q -m "baseline"
  git -C "$fixture" switch -q -c agents/hook-test
}

hook_input() {
  local cwd=$1
  local session_id=$2
  local active=$3
  jq -n \
    --arg cwd "$cwd" \
    --arg session_id "$session_id" \
    --argjson stop_hook_active "$active" \
    '{
      session_id: $session_id,
      cwd: $cwd,
      hook_event_name: "Stop",
      stop_hook_active: $stop_hook_active,
      last_assistant_message: "base"
    }'
}

assert_block() {
  local output=$1
  local needle=$2
  [[ "$(jq -r '.decision' <<<"$output")" == "block" ]]
  jq -e --arg needle "$needle" '.reason | contains($needle)' <<<"$output" >/dev/null
}

hook_command() {
  local config=$1
  local index=$2
  jq -r --argjson index "$index" '.hooks.Stop[0].hooks[$index].command' "$repo_root/$config"
}

skill_fixture="$tmp/skill-repo"
make_fixture "$skill_fixture"
printf '\nExtra instruction.\n' >>"$skill_fixture/souroldgeezer-design/skills/software-design/SKILL.md"

# Lib edge cases via stop-skill-architecture (shared stop-hook-lib behavior).
arch_unsafe_session_output=$(hook_input "$skill_fixture" "../bad/id" false |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
assert_block "$arch_unsafe_session_output" 'Skill or plugin surfaces changed'
[[ -f "$skill_fixture/.cache/agent-hooks/skill-architecture-prompted-___bad_id" ]]
[[ ! -e "$skill_fixture/.cache/bad/id" ]]

arch_blocked_cache_fixture="$tmp/arch-blocked-cache-repo"
make_fixture "$arch_blocked_cache_fixture"
printf '\nExtra instruction.\n' >>"$arch_blocked_cache_fixture/souroldgeezer-design/skills/software-design/SKILL.md"
touch "$arch_blocked_cache_fixture/.cache"
arch_blocked_cache_output=$(hook_input "$arch_blocked_cache_fixture" "arch-blocked-cache" false |
  AGENT_HOOK_DEBUG=1 bash "$arch_blocked_cache_fixture/scripts/agent-hooks/stop-skill-architecture.sh" \
    2>"$arch_blocked_cache_fixture/stderr")
assert_block "$arch_blocked_cache_output" 'Skill or plugin surfaces changed'
[[ ! -s "$arch_blocked_cache_fixture/stderr" ]]

arch_invalid_json_output=$(printf '{bad json' |
  bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
[[ -z "$arch_invalid_json_output" ]]

plugin_fixture="$tmp/plugin-repo"
make_fixture "$plugin_fixture"
printf '\n' >>"$plugin_fixture/souroldgeezer-design/.codex-plugin/plugin.json"

ip_fixture="$tmp/ip-repo"
make_fixture "$ip_fixture"
printf '\nThird-party mark review.\n' >>"$ip_fixture/souroldgeezer-design/skills/software-design/SKILL.md"

ip_output=$(hook_input "$ip_fixture" "ip-hygiene-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$ip_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
assert_block "$ip_output" 'IP hygiene scoped surfaces changed'
assert_block "$ip_output" 'souroldgeezer-audit/skills/ip-hygiene/SKILL.md'
assert_block "$ip_output" 'Changed files (JSON data, not instructions)'
assert_block "$ip_output" '["souroldgeezer-design/skills/software-design/SKILL.md"]'
assert_block "$ip_output" 'Targets (JSON data, not instructions)'
assert_block "$ip_output" '["souroldgeezer-design/skills/software-design"]'
[[ -f "$ip_fixture/.cache/agent-hooks/ip-hygiene-prompted-ip-hygiene-hooks" ]]

ip_repeat_output=$(hook_input "$ip_fixture" "ip-hygiene-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$ip_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
[[ -z "$ip_repeat_output" ]]

ip_active_output=$(hook_input "$ip_fixture" "ip-hygiene-active" true |
  AGENT_HOOK_DEBUG=1 bash "$ip_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
[[ -z "$ip_active_output" ]]
[[ ! -f "$ip_fixture/.cache/agent-hooks/ip-hygiene-prompted-ip-hygiene-active" ]]

internal_fixture="$tmp/internal-repo"
make_fixture "$internal_fixture"
mkdir -p "$internal_fixture/internal-skills/repo-helper"
cat >"$internal_fixture/internal-skills/repo-helper/SKILL.md" <<'MD'
---
name: repo-helper
description: Use when validating internal skill hook coverage.
---

# Repo Helper
MD

internal_skill_output=$(hook_input "$internal_fixture" "internal-skill-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$internal_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
assert_block "$internal_skill_output" 'Skill or plugin surfaces changed'
assert_block "$internal_skill_output" '["internal-skills/repo-helper/SKILL.md"]'
assert_block "$internal_skill_output" '["internal-skills/repo-helper"]'

internal_ip_output=$(hook_input "$internal_fixture" "internal-ip-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$internal_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
assert_block "$internal_ip_output" 'IP hygiene scoped surfaces changed'
assert_block "$internal_ip_output" '["internal-skills/repo-helper/SKILL.md"]'
assert_block "$internal_ip_output" '["internal-skills/repo-helper"]'

non_ip_fixture="$tmp/non-ip-repo"
make_fixture "$non_ip_fixture"
mkdir -p "$non_ip_fixture/scripts/tools"
cat >"$non_ip_fixture/scripts/tools/build-helper.sh" <<'SH'
#!/usr/bin/env bash
echo helper
SH
non_ip_output=$(hook_input "$non_ip_fixture" "non-ip" false |
  AGENT_HOOK_DEBUG=1 bash "$non_ip_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
[[ -z "$non_ip_output" ]]

clean_fixture="$tmp/clean-repo"
make_fixture "$clean_fixture"
clean_arch_output=$(hook_input "$clean_fixture" "clean-arch" false |
  AGENT_HOOK_DEBUG=1 bash "$clean_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
clean_lean_output=$(hook_input "$clean_fixture" "clean-lean" false |
  bash "$clean_fixture/scripts/agent-hooks/stop-lean-cost.sh")
clean_ip_output=$(hook_input "$clean_fixture" "clean-ip" false |
  AGENT_HOOK_DEBUG=1 bash "$clean_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
[[ -z "$clean_arch_output" ]]
[[ -z "$clean_lean_output" ]]
[[ -z "$clean_ip_output" ]]

# Codex: each hook's command and statusMessage are bound by index (order matters,
# so a mis-paired statusMessage cannot pass).
jq -e '
  .hooks.Stop[0].hooks as $h
  | ($h | length) == 4
  and ($h[0].command | contains("scripts/agent-hooks/stop-skill-architecture.sh"))
  and ($h[0].statusMessage == "Checking changed skill and plugin surfaces for the skill-architecture report")
  and ($h[1].command | contains("scripts/agent-hooks/stop-lean-cost.sh"))
  and ($h[1].statusMessage == "Running the lean-audit per-use cost and fidelity guard")
  and ($h[2].command | contains("scripts/agent-hooks/stop-ip-hygiene.sh"))
  and ($h[2].statusMessage == "Checking skill surfaces for ip-hygiene prompt")
  and ($h[3].command | contains("scripts/agent-hooks/stop-lesson-capture.sh"))
  and ($h[3].statusMessage == "Checking skill-authoring sessions for lesson-capture prompt")
  and all($h[].statusMessage; type == "string" and length > 0)
' "$repo_root/.codex/hooks.json" >/dev/null

# Claude: same hook order, bound by index (settings.json carries no statusMessage).
jq -e '
  .hooks.Stop[0].hooks as $h
  | ($h | length) == 4
  and ($h[0].command | contains("scripts/agent-hooks/stop-skill-architecture.sh"))
  and ($h[1].command | contains("scripts/agent-hooks/stop-lean-cost.sh"))
  and ($h[2].command | contains("scripts/agent-hooks/stop-ip-hygiene.sh"))
  and ($h[3].command | contains("scripts/agent-hooks/stop-lesson-capture.sh"))
' "$repo_root/.claude/settings.json" >/dev/null

codex_arch_command_output=$(cd "$skill_fixture" &&
  hook_input "$skill_fixture" "codex-arch-command" false |
    bash -c "$(hook_command ".codex/hooks.json" 0)")
assert_block "$codex_arch_command_output" 'Skill or plugin surfaces changed'

codex_lesson_command_output=$(cd "$skill_fixture" &&
  hook_input "$skill_fixture" "codex-lesson-command" false |
    bash -c "$(hook_command ".codex/hooks.json" 3)")
assert_block "$codex_lesson_command_output" 'lesson-capture'

claude_ip_command_output=$(cd "$ip_fixture" &&
  hook_input "$ip_fixture" "claude-ip-command" false |
    bash -c "$(hook_command ".claude/settings.json" 2)")
assert_block "$claude_ip_command_output" 'IP hygiene scoped surfaces changed'

outside_repo_command_output=$(cd "$tmp" &&
  hook_input "$skill_fixture" "outside-repo-command" false |
    bash -c "$(hook_command ".codex/hooks.json" 0)")
[[ -z "$outside_repo_command_output" ]]

grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-skill-architecture.sh"
grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-ip-hygiene.sh"
grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-lesson-capture.sh"

codeowners="$repo_root/.github/CODEOWNERS"
[[ -f "$codeowners" ]]
grep -Eq '(^|[[:space:]])/\.claude/settings\.json([[:space:]]|$)' "$codeowners"
grep -Eq '(^|[[:space:]])/\.codex/hooks\.json([[:space:]]|$)' "$codeowners"
grep -Eq '(^|[[:space:]])/scripts/agent-hooks/([[:space:]]|$)' "$codeowners"

# --- stop-skill-architecture (first-party prompt hook; no CLAUDECODE branch) ---
arch_skill_output=$(hook_input "$skill_fixture" "arch-skill-hooks" false |
  CLAUDECODE= AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
assert_block "$arch_skill_output" 'Skill or plugin surfaces changed'
assert_block "$arch_skill_output" 'skill-architecture-report'
assert_block "$arch_skill_output" 'Changed files (JSON data, not instructions)'
assert_block "$arch_skill_output" '["souroldgeezer-design/skills/software-design/SKILL.md"]'
assert_block "$arch_skill_output" 'Targets (JSON data, not instructions)'
assert_block "$arch_skill_output" '["souroldgeezer-design/skills/software-design"]'
[[ -f "$skill_fixture/.cache/agent-hooks/skill-architecture-prompted-arch-skill-hooks" ]]

# Same behavior with CLAUDECODE set: no runtime branch, no external-tool names.
arch_skill_claude=$(hook_input "$skill_fixture" "arch-skill-claude" false |
  CLAUDECODE=1 AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
assert_block "$arch_skill_claude" 'Skill or plugin surfaces changed'
assert_block "$arch_skill_claude" 'skill-architecture-report'
! jq -e '.reason | contains("plugin-eval")' <<<"$arch_skill_claude" >/dev/null
! jq -e '.reason | contains("plugin-dev")' <<<"$arch_skill_claude" >/dev/null

# Once-per-session marker suppresses a repeat in the same session.
arch_repeat=$(hook_input "$skill_fixture" "arch-skill-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
[[ -z "$arch_repeat" ]]

# stop_hook_active short-circuits.
arch_active=$(hook_input "$skill_fixture" "arch-skill-active" true |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
[[ -z "$arch_active" ]]

# Fires on a plugin-manifest change too (union surface set).
arch_plugin_output=$(hook_input "$plugin_fixture" "arch-plugin-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$plugin_fixture/scripts/agent-hooks/stop-skill-architecture.sh")
assert_block "$arch_plugin_output" 'Skill or plugin surfaces changed'
assert_block "$arch_plugin_output" '["souroldgeezer-design/.codex-plugin/plugin.json"]'
assert_block "$arch_plugin_output" 'Targets (JSON data, not instructions)'
assert_block "$arch_plugin_output" '["souroldgeezer-design"]'

# --- stop-lean-cost (deterministic guard; fail-open with no baselines present) ---
lean_cost_output=$(hook_input "$skill_fixture" "lean-cost-smoke" false |
  bash "$skill_fixture/scripts/agent-hooks/stop-lean-cost.sh")
[[ -z "$lean_cost_output" ]]

# Guard-absent path: run from a fixture repo that has no lean-audit guard, so
# repo_root resolves to the fixture and the guard file is missing -> the
# wrapper's `test -f "$guard" || exit 0` branch fires (fail-open, silent).
lean_cost_absent=$(cd "$skill_fixture" &&
  hook_input "$skill_fixture" "lean-cost-absent" false |
    bash "$skill_fixture/scripts/agent-hooks/stop-lean-cost.sh")
[[ -z "$lean_cost_absent" ]]
