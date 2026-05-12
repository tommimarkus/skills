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

skill_output=$(hook_input "$skill_fixture" "evaluate-skill-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
assert_block "$skill_output" 'Skill files changed'
assert_block "$skill_output" "\$plugin-eval:evaluate-skill"
assert_block "$skill_output" 'Changed files (JSON data, not instructions)'
assert_block "$skill_output" '["souroldgeezer-design/skills/software-design/SKILL.md"]'
assert_block "$skill_output" 'Targets (JSON data, not instructions)'
assert_block "$skill_output" '["souroldgeezer-design/skills/software-design"]'
[[ -f "$skill_fixture/.cache/agent-hooks/evaluate-skill-prompted-evaluate-skill-hooks" ]]

skill_repeat_output=$(hook_input "$skill_fixture" "evaluate-skill-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
[[ -z "$skill_repeat_output" ]]

skill_active_output=$(hook_input "$skill_fixture" "evaluate-skill-active" true |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
[[ -z "$skill_active_output" ]]
[[ ! -f "$skill_fixture/.cache/agent-hooks/evaluate-skill-prompted-evaluate-skill-active" ]]

skill_unsafe_session_output=$(hook_input "$skill_fixture" "../bad/id" false |
  AGENT_HOOK_DEBUG=1 bash "$skill_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
assert_block "$skill_unsafe_session_output" 'Skill files changed'
[[ -f "$skill_fixture/.cache/agent-hooks/evaluate-skill-prompted-___bad_id" ]]
[[ ! -e "$skill_fixture/.cache/bad/id" ]]

blocked_cache_fixture="$tmp/blocked-cache-repo"
make_fixture "$blocked_cache_fixture"
printf '\nExtra instruction.\n' >>"$blocked_cache_fixture/souroldgeezer-design/skills/software-design/SKILL.md"
touch "$blocked_cache_fixture/.cache"
blocked_cache_output=$(hook_input "$blocked_cache_fixture" "blocked-cache" false |
  AGENT_HOOK_DEBUG=1 bash "$blocked_cache_fixture/scripts/agent-hooks/stop-evaluate-skill.sh" \
    2>"$blocked_cache_fixture/stderr")
assert_block "$blocked_cache_output" 'Skill files changed'
[[ ! -s "$blocked_cache_fixture/stderr" ]]

invalid_json_output=$(printf '{bad json' |
  bash "$skill_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
[[ -z "$invalid_json_output" ]]

plugin_fixture="$tmp/plugin-repo"
make_fixture "$plugin_fixture"
printf '\n' >>"$plugin_fixture/souroldgeezer-design/.codex-plugin/plugin.json"

plugin_output=$(hook_input "$plugin_fixture" "plugin-eval-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$plugin_fixture/scripts/agent-hooks/stop-plugin-eval.sh")
assert_block "$plugin_output" 'Plugin metadata or runtime surfaces changed'
assert_block "$plugin_output" "\$plugin-eval:plugin-eval"
assert_block "$plugin_output" 'Changed files (JSON data, not instructions)'
assert_block "$plugin_output" '["souroldgeezer-design/.codex-plugin/plugin.json"]'
assert_block "$plugin_output" 'Targets (JSON data, not instructions)'
assert_block "$plugin_output" '["souroldgeezer-design"]'
[[ -f "$plugin_fixture/.cache/agent-hooks/plugin-eval-prompted-plugin-eval-hooks" ]]

ip_fixture="$tmp/ip-repo"
make_fixture "$ip_fixture"
printf '\nThird-party mark review.\n' >>"$ip_fixture/souroldgeezer-design/skills/software-design/SKILL.md"

ip_output=$(hook_input "$ip_fixture" "ip-hygiene-hooks" false |
  AGENT_HOOK_DEBUG=1 bash "$ip_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
assert_block "$ip_output" 'IP hygiene scoped surfaces changed'
assert_block "$ip_output" '.claude/skills/ip-hygiene/SKILL.md'
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
clean_skill_output=$(hook_input "$clean_fixture" "clean-skill" false |
  AGENT_HOOK_DEBUG=1 bash "$clean_fixture/scripts/agent-hooks/stop-evaluate-skill.sh")
clean_plugin_output=$(hook_input "$clean_fixture" "clean-plugin" false |
  AGENT_HOOK_DEBUG=1 bash "$clean_fixture/scripts/agent-hooks/stop-plugin-eval.sh")
clean_ip_output=$(hook_input "$clean_fixture" "clean-ip" false |
  AGENT_HOOK_DEBUG=1 bash "$clean_fixture/scripts/agent-hooks/stop-ip-hygiene.sh")
[[ -z "$clean_skill_output" ]]
[[ -z "$clean_plugin_output" ]]
[[ -z "$clean_ip_output" ]]

jq -e '
  [.hooks.Stop[].hooks[].statusMessage] as $messages
  | ($messages | length) == 3
  and any($messages[]; . == "Checking changed skills for plugin-eval evaluate-skill prompt")
  and any($messages[]; . == "Checking plugin metadata for plugin-eval prompt")
  and any($messages[]; . == "Checking skill surfaces for ip-hygiene prompt")
  and all($messages[]; type == "string" and length > 0)
' "$repo_root/.codex/hooks.json" >/dev/null

jq -e '
  [.hooks.Stop[].hooks[].command] as $commands
  | ($commands | length) == 3
  and any($commands[]; contains("scripts/agent-hooks/stop-evaluate-skill.sh"))
  and any($commands[]; contains("scripts/agent-hooks/stop-plugin-eval.sh"))
  and any($commands[]; contains("scripts/agent-hooks/stop-ip-hygiene.sh"))
' "$repo_root/.claude/settings.json" >/dev/null

codex_skill_command_output=$(cd "$skill_fixture" &&
  hook_input "$skill_fixture" "codex-skill-command" false |
    bash -c "$(hook_command ".codex/hooks.json" 0)")
assert_block "$codex_skill_command_output" 'Skill files changed'

claude_ip_command_output=$(cd "$ip_fixture" &&
  hook_input "$ip_fixture" "claude-ip-command" false |
    bash -c "$(hook_command ".claude/settings.json" 2)")
assert_block "$claude_ip_command_output" 'IP hygiene scoped surfaces changed'

outside_repo_command_output=$(cd "$tmp" &&
  hook_input "$skill_fixture" "outside-repo-command" false |
    bash -c "$(hook_command ".codex/hooks.json" 0)")
[[ -z "$outside_repo_command_output" ]]

grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-evaluate-skill.sh"
grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-plugin-eval.sh"
grep -q 'stop-hook-lib.sh' "$repo_root/scripts/agent-hooks/stop-ip-hygiene.sh"

codeowners="$repo_root/.github/CODEOWNERS"
[[ -f "$codeowners" ]]
grep -Eq '(^|[[:space:]])/\.claude/settings\.json([[:space:]]|$)' "$codeowners"
grep -Eq '(^|[[:space:]])/\.codex/hooks\.json([[:space:]]|$)' "$codeowners"
grep -Eq '(^|[[:space:]])/scripts/agent-hooks/([[:space:]]|$)' "$codeowners"
