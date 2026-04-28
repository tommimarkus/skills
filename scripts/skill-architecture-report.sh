#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/skill-architecture-report.sh [repo-root]

Produces an advisory Markdown report for Skill Architecture Craft Standard
improvement targets. Findings exit 0; usage and unreadable-path errors exit
nonzero.
EOF
}

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 2
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "$#" -gt 1 ]]; then
  usage >&2
  die "expected zero or one repo root argument"
fi

repo_root="${1:-.}"
[[ -d "$repo_root" ]] || die "repo root is not a readable directory: $repo_root"
[[ -r "$repo_root" ]] || die "repo root is not readable: $repo_root"

repo_root="$(cd "$repo_root" && pwd)"
rerun_command='scripts/skill-architecture-report.sh .'
tmp_dir="$(mktemp -d)"
report_tmp="$tmp_dir/findings.tsv"
trap 'rm -rf "$tmp_dir"' EXIT
: > "$report_tmp"

relpath() {
  local path="$1"
  printf '%s\n' "${path#"$repo_root"/}"
}

frontmatter_value() {
  local file="$1"
  local key="$2"

  if command -v yq >/dev/null 2>&1; then
    local value
    if value="$(yq --front-matter=extract -r ".$key // \"\"" "$file" 2>/dev/null)"; then
      printf '%s\n' "$value" | sed ':again;N;$!bagain;s/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//'
      return
    fi
  fi

  awk -v key="$key" '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm {
      prefix = key ":"
      if (index($0, prefix) == 1) {
        value = substr($0, length(prefix) + 1)
        sub(/^[[:space:]]+/, "", value)
        sub(/^"/, "", value)
        sub(/"$/, "", value)
        print value
        exit
      }
    }
  ' "$file"
}

frontmatter_body() {
  local file="$1"
  awk '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { in_fm = 0; next }
    !in_fm { print }
  ' "$file"
}

field_safe() {
  printf '%s' "$1" | tr '\n' ' ' | sed 's/|/\//g; s/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//'
}

add_finding() {
  local group="$1"
  local severity="$2"
  local code="$3"
  local path="$4"
  local evidence="$5"
  local rule="$6"
  local impact="$7"
  local claude_impact="$impact"
  local codex_impact="$impact"
  local action="$8"
  local verify="${9:-$rerun_command}"

  case "$code" in
    SAC-TRIGGER-DESC-LENGTH)
      claude_impact="Overlong descriptions make Claude trigger matching noisier."
      codex_impact="Codex may reject or truncate overlong skill metadata."
      ;;
    *)
      claude_impact="${claude_impact//Claude\/Codex/Claude}"
      codex_impact="${codex_impact//Claude\/Codex/Codex}"
      ;;
  esac

  if [[ "$verify" == *'$repo_root'* ]]; then
    verify="$rerun_command"
  fi

  printf '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n' \
    "$group" \
    "$severity" \
    "$code" \
    "$(field_safe "$path")" \
    "$(field_safe "$evidence")" \
    "$(field_safe "$rule")" \
    "$(field_safe "$claude_impact")" \
    "$(field_safe "$codex_impact")" \
    "$(field_safe "$action")" \
    "$(field_safe "$verify")" >> "$report_tmp"
}

support_is_advertised() {
  local file="$1"
  local target="$2"

  if grep -Fq "($target)" "$file" ||
      grep -Fq "($target#" "$file" ||
      grep -Fq "($target/)" "$file" ||
      grep -Fq "($target/#" "$file"; then
    return 0
  fi

  awk -v target="$target" '
    function path_char(ch) {
      return ch ~ /[[:alnum:]_.\/-]/
    }
    function target_on_line(line, target,    pos, rest, offset, before, after, after2) {
      offset = 0
      rest = line
      while ((pos = index(rest, target)) > 0) {
        before = (offset + pos == 1) ? "" : substr(line, offset + pos - 1, 1)
        after = substr(line, offset + pos + length(target), 1)
        after2 = substr(line, offset + pos + length(target) + 1, 1)
        if (!path_char(before) && (!path_char(after) || (after == "/" && !path_char(after2)))) {
          return 1
        }
        offset += pos
        rest = substr(line, offset + 1)
      }
      return 0
    }
    {
      lower = tolower($0)
      has_cue = lower ~ /(read|load|use|consult|open|see|follow|run|verify|validate|inspect|cite|apply|emit|copy|rerun|re-run|scan)/
      has_negative = lower ~ /(do not|never|ignore|obsolete|deprecated|deleted|remove|historical)/
      if (!has_negative && target_on_line($0, target) && (has_cue || $0 ~ /^[[:space:]]*\|/)) {
        found = 1
      }
    }
    END { exit found ? 0 : 1 }
  ' "$file"
}

skill_scope() {
  local rel="$1"
  case "$rel" in
    .claude/skills/*/SKILL.md) printf 'internal' ;;
    */skills/*/SKILL.md) printf 'published' ;;
    *) printf 'unknown' ;;
  esac
}

skill_dir_from_rel() {
  local rel="$1"
  printf '%s\n' "${rel%/SKILL.md}"
}

scan_skill() {
  local rel="$1"
  local file="$repo_root/$rel"
  local skill_dir
  local description
  local name
  local body_lines
  local desc_len
  local scope

  skill_dir="$(skill_dir_from_rel "$rel")"
  description="$(frontmatter_value "$file" description || true)"
  name="$(frontmatter_value "$file" name || true)"
  body_lines="$(frontmatter_body "$file" | wc -l | awk '{print $1}')"
  desc_len="${#description}"
  scope="$(skill_scope "$rel")"

  if [[ "$desc_len" -gt 1024 ]]; then
    add_finding "Trigger Metadata" "high" "SAC-TRIGGER-DESC-LENGTH" "$rel" \
      "description length=$desc_len characters" \
      "Frontmatter description must stay at or below 1024 characters." \
      "Codex may reject or truncate overlong metadata; Claude trigger matching also gets noisier." \
      "Shorten the description and front-load the concrete trigger plus boundary context." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if ! printf '%s\n%s\n' "$description" "$(frontmatter_body "$file" | sed -n '1,40p')" |
      grep -Eiq '\b(use when|trigger when|invoke when|do not use when|boundary|scope|out of scope)\b'; then
    add_finding "Trigger Metadata" "high" "SAC-TRIGGER-MISSING-CONTEXT" "$rel" \
      "description/body opening lacks explicit trigger or boundary language" \
      "Skill metadata should name positive use context and near-miss boundaries." \
      "Agents may invoke the skill too late, too broadly, or miss it for terse user requests." \
      "Add a concise Use when trigger and at least one boundary or out-of-scope cue." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if printf '%s\n' "$description" | grep -Eiq '\b(always use|must use|for anything|for everything|any request|all tasks)\b'; then
    add_finding "Trigger Metadata" "medium" "SAC-TRIGGER-AGGRESSIVE" "$rel" \
      "description contains aggressive trigger wording: ${description:0:180}" \
      "Triggers should be specific enough to stay quiet for near-miss prompts." \
      "Claude/Codex may over-trigger this skill and consume context before the right workflow is selected." \
      "Replace broad imperative trigger wording with concrete task contexts and negative boundaries." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if [[ "$body_lines" -gt 500 ]]; then
    add_finding "Workflow Body" "medium" "SAC-WORKFLOW-BODY-SIZE" "$rel" \
      "body lines=$body_lines" \
      "SKILL.md should stay focused; detailed rubrics and examples belong in one-hop support files." \
      "Large bodies spend agent context every run and make iterative improvement slower." \
      "Move rarely needed procedure detail into referenced files with explicit load conditions." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if ! grep -Eiq '\b(stop when|stop if|do not proceed|halt|blocker|exit nonzero|exit 0|ask the user|escalate|unsupported|cannot proceed)\b' "$file"; then
    add_finding "Workflow Body" "medium" "SAC-WORKFLOW-STOP-CONDITIONS" "$rel" \
      "no clear stop or escalation condition matched" \
      "Agentic workflows should state when to stop, ask, or fail instead of guessing." \
      "Claude/Codex may continue past uncertainty, over-edit, or silently skip required evidence." \
      "Add explicit stop conditions for blockers, ambiguity, and verification failure." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if ! grep -Eiq '\b(output|deliverable|return|report|findings|summary|response must|produce)\b' "$file"; then
    add_finding "Workflow Body" "high" "SAC-WORKFLOW-OUTPUT" "$rel" \
      "no concrete output contract matched" \
      "Skills should define the shape of the agent's result, not just activities to perform." \
      "Claude/Codex may produce inconsistent responses that are hard to compare across iterations." \
      "Add a short output contract naming required sections or fields for the final response." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if ! grep -Eiq '\b(rerun|re-run|verify|validate|validation|test command|run .* again)\b' "$file"; then
    add_finding "Workflow Body" "medium" "SAC-WORKFLOW-RERUN-GUIDANCE" "$rel" \
      "no rerun or validation loop matched" \
      "Skills should tell agents how to verify and repeat after edits." \
      "Claude/Codex may stop after a plausible edit without proving the workflow still works." \
      "Add exact validation or rerun guidance near the workflow's completion criteria." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  if grep -Eiq '\b(reference-like|comprehensive catalog|full catalog|every possible|complete reference|long reference|all possible options)\b' "$file"; then
    add_finding "On-Demand Knowledge" "low" "SAC-REF-LIKELY-PROSE-DUMP" "$rel" \
      "body contains wording that looks like reference prose" \
      "Detailed reusable knowledge should live in one-hop references loaded only when needed." \
      "Agents pay the context cost on every invocation and may miss the core workflow." \
      "Move reference prose into references/ or extensions/ and leave explicit load instructions in SKILL.md." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi

  { grep -Eo '\[[^]]+\]\(([^)#]+)(#[^)]+)?\)' "$file" || true; } | sed -E 's/^.*\(([^)#]+).*/\1/' |
    while IFS= read -r link; do
      case "$link" in
        http:*|https:*|mailto:*|/*|"") continue ;;
      esac
      if [[ ! -e "$repo_root/$skill_dir/$link" && ! -e "$repo_root/$link" ]]; then
        add_finding "On-Demand Knowledge" "high" "SAC-REF-BROKEN-LINK" "$rel" \
          "broken one-hop link target=$link" \
          "Support-file links from SKILL.md must resolve deterministically in local repo use." \
          "Claude/Codex will fail or hallucinate missing procedure content during iterative improvement." \
          "Fix the link target or remove the stale reference from the skill body." \
          'scripts/skill-architecture-report.sh "$repo_root"'
      fi
    done

  local unadvertised_tmp
  unadvertised_tmp="$tmp_dir/unadvertised-support.tmp"
  find "$repo_root/$skill_dir" -mindepth 2 -type f \( -path '*/references/*' -o -path '*/extensions/*' -o -path '*/examples/*' -o -path '*/fixtures/*' \) |
    sort |
    while IFS= read -r support; do
      local support_rel_from_skill
      local support_rel_from_repo
      local support_bucket
      support_rel_from_repo="$(relpath "$support")"
      support_rel_from_skill="${support_rel_from_repo#"$skill_dir"/}"

      case "$support_rel_from_skill" in
        */README.md)
          support_bucket="${support_rel_from_skill%/README.md}"
          if support_is_advertised "$file" "$support_rel_from_skill" ||
              support_is_advertised "$file" "$support_bucket"; then
            continue
          fi
          printf '%s|%s\n' "$support_bucket" "$support_rel_from_skill" >> "$unadvertised_tmp"
          continue
          ;;
      esac

      support_bucket="$support_rel_from_skill"
      case "$support_rel_from_skill" in
        references/*/*|fixtures/*/*|examples/*/*)
          support_bucket="${support_rel_from_skill%/*}"
          ;;
      esac
      if support_is_advertised "$file" "$support_rel_from_skill" ||
          support_is_advertised "$file" "$support_bucket"; then
        continue
      fi
      printf '%s|%s\n' "$support_bucket" "$support_rel_from_skill" >> "$unadvertised_tmp"
    done

  if [[ -s "$unadvertised_tmp" ]]; then
    cut -d'|' -f1 "$unadvertised_tmp" | sort -u |
      while IFS= read -r support_bucket; do
        local support_count
        local support_examples
        support_count="$(awk -F'|' -v bucket="$support_bucket" '$1 == bucket { count++ } END { print count + 0 }' "$unadvertised_tmp")"
        support_examples="$(awk -F'|' -v bucket="$support_bucket" '$1 == bucket { print $2 }' "$unadvertised_tmp" | sed -n '1,3p' | paste -sd ',' - | sed 's/,/, /g')"
        add_finding "On-Demand Knowledge" "low" "SAC-REF-UNADVERTISED-SUPPORT" "$skill_dir/$support_bucket" \
          "$support_count support file(s) not mentioned from $rel; examples: $support_examples" \
          "One-hop knowledge should be advertised with load conditions from SKILL.md." \
          "Claude/Codex may never discover useful support material or may load it at the wrong time." \
          "Mention this support area from SKILL.md with a precise condition, or remove it if obsolete." \
          "$rerun_command"
      done
  fi
  rm -f "$unadvertised_tmp"

  find "$repo_root/$skill_dir" -mindepth 2 -type f -path '*/scripts/*' |
    sort |
    while IFS= read -r helper; do
      local helper_rel
      helper_rel="$(relpath "$helper")"
      local helper_from_skill="${helper_rel#"$skill_dir"/}"
      if ! grep -Fq "$helper_from_skill" "$file"; then
        add_finding "Deterministic Machinery" "medium" "SAC-SCRIPT-UNADVERTISED" "$helper_rel" \
          "script not advertised from $rel" \
          "Fragile or repeated work should be exposed through documented, discoverable commands." \
          "Agents may reimplement deterministic checks by hand instead of using the bundled script." \
          "Add usage and load conditions for this script in SKILL.md, including a verification command." \
          'scripts/skill-architecture-report.sh "$repo_root"'
      fi
    done

  if [[ "$scope" == "published" && ! -f "$repo_root/$skill_dir/agents/openai.yaml" ]]; then
    add_finding "Runtime Parity" "high" "SAC-RUNTIME-MISSING-OPENAI" "$rel" \
      "missing ${skill_dir}/agents/openai.yaml" \
      "Published plugin skills should include basic Codex metadata next to the shared skill." \
      "Claude may have usable subagent guidance while Codex lacks equivalent skill metadata." \
      "Add agents/openai.yaml that matches the skill purpose and trigger boundaries." \
      "$rerun_command"
  fi

  if [[ -n "$name" && "$rel" == */skills/*/SKILL.md ]]; then
    local expected_name
    expected_name="$(basename "$skill_dir")"
    if [[ "$name" != "$expected_name" ]]; then
      add_finding "Runtime Parity" "high" "SAC-RUNTIME-NAME-DRIFT" "$rel" \
        "frontmatter name=$name, directory=$expected_name" \
        "Skill name should match its directory for predictable runtime discovery." \
        "Claude/Codex may expose confusing names or fail parity checks." \
        "Rename the directory or update frontmatter so both match." \
        'scripts/skill-architecture-report.sh "$repo_root"'
    fi
  fi
}

scan_codex_plugin() {
  local rel="$1"
  local file="$repo_root/$rel"

  if ! command -v jq >/dev/null 2>&1; then
    add_finding "Runtime Parity" "medium" "SAC-RUNTIME-JQ-MISSING" "$rel" \
      "jq is not available" \
      "Codex plugin metadata checks require deterministic JSON parsing." \
      "Agents cannot reliably assess runtime parity without the repo-standard JSON tool." \
      "Install jq or run this report in an environment with jq available." \
      "$rerun_command"
    return
  fi

  if ! jq empty "$file" >/dev/null 2>&1; then
    add_finding "Runtime Parity" "blocker" "SAC-RUNTIME-PLUGIN-JSON" "$rel" \
      "jq could not parse plugin.json" \
      "Plugin metadata must be valid JSON for both packaging and advisory checks." \
      "Codex plugin discovery can fail before skills are visible." \
      "Fix JSON syntax, then rerun the report." \
      "$rerun_command"
    return
  fi

  local prompt_count
  prompt_count="$(jq '.interface.defaultPrompt // [] | length' "$file")"
  if [[ "$prompt_count" -gt 3 ]]; then
    add_finding "Runtime Parity" "medium" "SAC-RUNTIME-DEFAULT-PROMPTS" "$rel" \
      "interface.defaultPrompt count=$prompt_count" \
      "Codex defaultPrompt arrays should contain three or fewer entries." \
      "Extra Codex prompts are ignored or warned about, so advertised entrypoints drift from runtime truth." \
      "Reduce defaultPrompt to the highest-value three prompts and keep remaining examples in docs or references." \
      "$rerun_command"
  fi
}

scan_repo_guidance() {
  if [[ -e "$repo_root/.agents/plugins/marketplace.json" ]]; then
    add_finding "Repo Guidance Drift" "high" "SAC-DOC-SPLIT-MARKETPLACE" ".agents/plugins/marketplace.json" \
      "secondary Codex marketplace catalog exists" \
      "This repo uses .claude-plugin/marketplace.json as the shared marketplace unless a design explicitly splits catalogs." \
      "Claude/Codex package listings may drift and confuse local marketplace refreshes." \
      "Remove the split catalog or document the explicit split decision in canonical repo guidance." \
      "$rerun_command"
  fi

  if [[ ! -f "$repo_root/AGENTS.md" || ! -f "$repo_root/CLAUDE.md" ]]; then
    add_finding "Repo Guidance Drift" "low" "SAC-DOC-MISSING-ENTRYPOINT" "." \
      "AGENTS.md or CLAUDE.md is missing" \
      "Cross-runtime skill repos need explicit agent entrypoint guidance." \
      "Claude/Codex contributors may apply inconsistent packaging and review rules." \
      "Add the missing entrypoint or document why this fixture/repo is intentionally partial." \
      'scripts/skill-architecture-report.sh "$repo_root"'
  fi
}

skill_files="$(
  {
    find "$repo_root" -path '*/.git' -prune -o -path '*/node_modules' -prune -o -path '*/.worktrees' -prune -o -path '*/skills/*/SKILL.md' -type f -print
    find "$repo_root/.claude/skills" -maxdepth 2 -name 'SKILL.md' -type f -print 2>/dev/null || true
  } | sort -u
)"

while IFS= read -r skill_file; do
  [[ -n "$skill_file" ]] || continue
  scan_skill "$(relpath "$skill_file")"
done <<< "$skill_files"

codex_plugins="$(find "$repo_root" -path '*/.git' -prune -o -path '*/.worktrees' -prune -o -path '*/.codex-plugin/plugin.json' -type f -print | sort)"
while IFS= read -r plugin_file; do
  [[ -n "$plugin_file" ]] || continue
  scan_codex_plugin "$(relpath "$plugin_file")"
done <<< "$codex_plugins"

scan_repo_guidance

finding_count="$(wc -l < "$report_tmp" | awk '{print $1}')"
blocker_count="$(awk -F'|' '$2 == "blocker" { count++ } END { print count + 0 }' "$report_tmp")"
high_count="$(awk -F'|' '$2 == "high" { count++ } END { print count + 0 }' "$report_tmp")"
medium_count="$(awk -F'|' '$2 == "medium" { count++ } END { print count + 0 }' "$report_tmp")"
low_count="$(awk -F'|' '$2 == "low" { count++ } END { print count + 0 }' "$report_tmp")"

cat <<EOF
# Skill Architecture Craft Report

## Summary

- Repo: \`$repo_root\`
- Findings: $finding_count total ($blocker_count blocker, $high_count high, $medium_count medium, $low_count low)
- Exit policy: advisory findings exit 0; rerun after each improvement.

EOF

emit_group() {
  local group="$1"
  printf '## %s\n\n' "$group"
  local group_tmp
  group_tmp="$tmp_dir/group.tmp"
  awk -F'|' -v group="$group" '$1 == group { print }' "$report_tmp" > "$group_tmp"
  if [[ ! -s "$group_tmp" ]]; then
    printf 'No advisory findings.\n\n'
    return
  fi

  local i=1
  while IFS='|' read -r _group severity code path evidence rule claude_impact codex_impact action verify; do
    cat <<EOF
### $i. $code ($severity)

- Path: \`$path\`
- Evidence: $evidence
- Violated rule: $rule
- Claude impact: $claude_impact
- Codex impact: $codex_impact
- Next action: $action
- Verify/rerun: \`$verify\`

EOF
    i=$((i + 1))
  done < "$group_tmp"
}

emit_group "Trigger Metadata"
emit_group "Workflow Body"
emit_group "On-Demand Knowledge"
emit_group "Deterministic Machinery"
emit_group "Runtime Parity"
emit_group "Repo Guidance Drift"

cat <<'EOF'
## Grouped Targets

EOF

if [[ "$finding_count" -eq 0 ]]; then
  printf 'No target groups.\n\n'
else
  target_tmp="$tmp_dir/targets.tmp"
  awk -F'|' '
    function owner(path) {
      if (match(path, /^\.claude\/skills\/[^/]+/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/skills\/[^/]+/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/\.codex-plugin\/plugin\.json/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/\.claude-plugin\/plugin\.json/)) {
        return substr(path, RSTART, RLENGTH)
      }
      return path
    }
    {
      target = owner($4)
      count[target]++
      if (codes[target] == "") {
        codes[target] = $3
      } else if (index(codes[target], $3) == 0) {
        codes[target] = codes[target] ", " $3
      }
      if (actions[target] == "") {
        actions[target] = $9
      }
    }
    END {
      for (target in count) {
        print target "|" count[target] "|" codes[target] "|" actions[target]
      }
    }
  ' "$report_tmp" | sort > "$target_tmp"

  while IFS='|' read -r target count codes action; do
    printf -- '- `%s`: %s finding(s); codes: %s; first action: %s\n' "$target" "$count" "$codes" "$action"
  done < "$target_tmp"
  printf '\n'
fi

cat <<'EOF'
## Next Iteration

EOF

if [[ "$finding_count" -eq 0 ]]; then
  cat <<'EOF'
No current advisory findings. Re-run the report after skill, metadata, support-file,
or repo-guidance changes.

- Verify/rerun: `scripts/skill-architecture-report.sh .`
EOF
else
  next_tmp="$tmp_dir/next.tmp"
  awk -F'|' '
    function owner(path) {
      if (match(path, /^\.claude\/skills\/[^/]+/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/skills\/[^/]+/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/\.codex-plugin\/plugin\.json/)) {
        return substr(path, RSTART, RLENGTH)
      }
      if (match(path, /^souroldgeezer-[^/]+\/\.claude-plugin\/plugin\.json/)) {
        return substr(path, RSTART, RLENGTH)
      }
      return path
    }
    BEGIN {
      priority["SAC-RUNTIME-PLUGIN-JSON"] = 1
      priority["SAC-RUNTIME-DEFAULT-PROMPTS"] = 2
      priority["SAC-RUNTIME-MISSING-OPENAI"] = 3
      priority["SAC-TRIGGER-DESC-LENGTH"] = 4
      priority["SAC-TRIGGER-AGGRESSIVE"] = 5
      priority["SAC-TRIGGER-MISSING-CONTEXT"] = 6
      priority["SAC-REF-BROKEN-LINK"] = 7
      priority["SAC-SCRIPT-UNADVERTISED"] = 8
      priority["SAC-WORKFLOW-OUTPUT"] = 9
    }
    {
      rank = ($3 in priority) ? priority[$3] : 50
      printf "%03d|%s|%s|%s|%s|%s\n", rank, owner($4), $3, $4, $9, $10
    }
  ' "$report_tmp" | sort -t'|' -k1,1n -k2,2 -k3,3 | awk -F'|' '!seen[$2]++ { print }' | sed -n '1,5p' > "$next_tmp"

  n=1
  while IFS='|' read -r _rank _target code path action verify; do
    printf '%s. %s in `%s`: %s Verify with `%s`.\n' "$n" "$code" "$path" "$action" "$verify"
    n=$((n + 1))
  done < "$next_tmp"
  printf '\nExact rerun command: `scripts/skill-architecture-report.sh .`\n'
fi
