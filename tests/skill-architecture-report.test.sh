#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
report_script="$repo_root/scripts/skill-architecture-report.sh"

fail() {
  printf 'not ok - %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local file="$1"
  local expected="$2"
  if ! grep -Fq -- "$expected" "$file"; then
    printf 'Expected to find: %s\n' "$expected" >&2
    printf 'Actual output:\n' >&2
    sed -n '1,220p' "$file" >&2
    fail "missing expected output"
  fi
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

fixture="$tmpdir/repo"
mkdir -p \
  "$fixture/example-plugin/.codex-plugin" \
  "$fixture/example-plugin/skills/noisy-skill/references" \
  "$fixture/example-plugin/skills/noisy-skill/scripts" \
  "$fixture/example-plugin/skills/quiet-skill/agents" \
  "$fixture/.claude/skills/internal-helper/references"

cat > "$fixture/example-plugin/.codex-plugin/plugin.json" <<'JSON'
{
  "name": "example-plugin",
  "version": "1.0.0",
  "description": "Fixture plugin",
  "skills": "./skills/",
  "interface": {
    "defaultPrompt": ["one", "two", "three", "four"]
  }
}
JSON

cat > "$fixture/example-plugin/skills/noisy-skill/SKILL.md" <<'MD'
---
name: noisy-skill
description: Always use this for anything with architecture. This metadata intentionally stays vague.
---

# Noisy Skill

This skill contains a long reference-like explanation of every possible option.
Agents should consider results and maybe write an answer.

See [missing procedure](references/missing.md).
See [known procedure](references/known.md).
MD

cat > "$fixture/example-plugin/skills/noisy-skill/references/known.md" <<'MD'
# Known Procedure
MD

cat > "$fixture/example-plugin/skills/noisy-skill/references/extra.md" <<'MD'
# Extra Procedure
MD

cat > "$fixture/example-plugin/skills/noisy-skill/scripts/helper.sh" <<'SH'
#!/usr/bin/env bash
echo helper
SH

cat > "$fixture/example-plugin/skills/quiet-skill/SKILL.md" <<'MD'
---
name: quiet-skill
description: >-
  Use when producing quiet fixture output with explicit inputs, outputs,
  stop conditions, rerun guidance, and boundaries.
---

# Quiet Skill

Use this when fixture tests need a mostly clean skill.

Inputs: fixture files.
Output: a short report.
Stop when the report is complete.
Rerun the validation command after edits.
MD

cat > "$fixture/example-plugin/skills/quiet-skill/agents/openai.yaml" <<'YAML'
name: quiet-skill
description: Fixture metadata.
YAML

cat > "$fixture/.claude/skills/internal-helper/SKILL.md" <<'MD'
---
name: internal-helper
description: Use when checking internal fixture guidance with clear boundaries and rerun guidance.
---

# Internal Helper

Input: fixture.
Output: advice.
Stop when evidence is gathered.
Rerun the report after changing guidance.
MD

output="$tmpdir/report.md"
"$report_script" "$fixture" > "$output"
status=$?
if [[ "$status" -ne 0 ]]; then
  fail "advisory findings should exit 0, got $status"
fi

assert_contains "$output" "# Skill Architecture Craft Report"
assert_contains "$output" "## Summary"
assert_contains "$output" "blocker"
assert_contains "$output" "high"
assert_contains "$output" "medium"
assert_contains "$output" "low"
assert_contains "$output" "## Trigger Metadata"
assert_contains "$output" "## Workflow Body"
assert_contains "$output" "## On-Demand Knowledge"
assert_contains "$output" "## Deterministic Machinery"
assert_contains "$output" "## Runtime Parity"
assert_contains "$output" "## Repo Guidance Drift"
assert_contains "$output" "## Grouped Targets"
assert_contains "$output" "## Next Iteration"
assert_contains "$output" "SAC-TRIGGER-AGGRESSIVE (medium)"
assert_contains "$output" "SAC-TRIGGER-MISSING-CONTEXT (high)"
assert_contains "$output" "SAC-WORKFLOW-OUTPUT (high)"
assert_contains "$output" "SAC-REF-BROKEN-LINK (high)"
assert_contains "$output" "SAC-REF-UNADVERTISED-SUPPORT"
assert_contains "$output" "SAC-RUNTIME-DEFAULT-PROMPTS (medium)"
assert_contains "$output" "SAC-RUNTIME-MISSING-OPENAI (high)"
assert_contains "$output" "SAC-DOC-MISSING-ENTRYPOINT (low)"
assert_contains "$output" "Path: \`example-plugin/skills/noisy-skill/SKILL.md\`"
assert_contains "$output" "Path: \`example-plugin/skills/noisy-skill/references/extra.md\`"
assert_contains "$output" "Claude impact:"
assert_contains "$output" "Codex impact:"
assert_contains "$output" "Next action:"
assert_contains "$output" "Verify/rerun:"
assert_contains "$output" "scripts/skill-architecture-report.sh ."

help_out="$tmpdir/help.txt"
"$report_script" --help > "$help_out"
assert_contains "$help_out" "Usage: scripts/skill-architecture-report.sh [repo-root]"

if "$report_script" "$fixture/does-not-exist" > "$tmpdir/bad.out" 2> "$tmpdir/bad.err"; then
  fail "missing repo root should be a usage error"
fi
assert_contains "$tmpdir/bad.err" "Error:"

clean_fixture="$tmpdir/clean-repo"
mkdir -p "$clean_fixture/example-plugin/skills/clean-skill/agents"
touch "$clean_fixture/AGENTS.md" "$clean_fixture/CLAUDE.md"

cat > "$clean_fixture/example-plugin/skills/clean-skill/SKILL.md" <<'MD'
---
name: clean-skill
description: Use when validating a clean fixture skill with explicit boundaries, outputs, stop conditions, and rerun guidance.
---

# Clean Skill

Use this when fixture tests need a no-finding skill.

Inputs: fixture files.
Output: a short report.
Stop when validation is complete.
Rerun the report after changing this skill.
MD

cat > "$clean_fixture/example-plugin/skills/clean-skill/agents/openai.yaml" <<'YAML'
name: clean-skill
description: Use when validating a clean fixture skill.
YAML

clean_out="$tmpdir/clean-report.md"
"$report_script" "$clean_fixture" > "$clean_out"
assert_contains "$clean_out" "Findings: 0 total"
assert_contains "$clean_out" "No target groups."
assert_contains "$clean_out" "No current advisory findings."

printf 'ok - skill architecture report fixture behavior\n'
