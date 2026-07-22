#!/usr/bin/env bash
# PreToolUse commit guard (graduates lesson-candidate #93).
#
# Refuses `git commit` on the PRIMARY checkout's `main` branch while linked
# worktrees are active.
#
# Why: during worktree-based authoring, a shell — a dispatched subagent's, and
# sometimes the main agent's — starts at the pinned launch directory, which is
# the primary checkout. A bare `git commit` there lands authoring work on the
# primary checkout's `main` instead of the intended worktree branch. Prose
# "work in the worktree" instructions are not enough; this hook is the
# zero-token deterministic backstop.
#
# Fires on Bash tool calls (settings matcher "Bash"). Fail-open: any missing
# tool, parse failure, or non-repo context exits 0 (allow). It denies only when
# ALL of these hold:
#   * the command creates/amends a commit via `git commit`;
#   * no explicit override token `ALLOW_MAIN_COMMIT=1` is present;
#   * the effective git dir is the PRIMARY checkout (git-dir == git-common-dir);
#   * the current branch is `main`;
#   * at least one linked worktree exists;
#   * the repo is this marketplace (root has `.claude-plugin/marketplace.json`).
#
# Deliberate integration onto main (e.g. the update-ref fallback used when the
# primary checkout is writable) is allowed by prefixing the command with
# `ALLOW_MAIN_COMMIT=1`. Fast-forward merges (`git merge --ff-only`) create no
# commit and are unaffected.

set -euo pipefail

command -v jq >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

input=$(cat) || exit 0
jq -e 'type == "object"' >/dev/null 2>&1 <<<"$input" || exit 0

tool=$(jq -r 'if (.tool_name | type) == "string" then .tool_name else "" end' <<<"$input")
[[ "$tool" == "Bash" ]] || exit 0

cmd=$(jq -r 'if (.tool_input.command | type) == "string" then .tool_input.command else "" end' <<<"$input")
[[ -n "$cmd" ]] || exit 0

cwd=$(jq -r 'if (.cwd | type) == "string" then .cwd else "" end' <<<"$input")
[[ -n "$cwd" ]] || cwd="$PWD"

# 1) Does the command create/amend a commit via `git commit`? Match
#    `git commit` and `git -C <path> commit`, requiring `commit` at a word
#    boundary (so `git commit-graph` / `commit-tree` do not match). Exclude
#    dry-run and help.
grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-C[[:space:]]+[^[:space:];&|]+)?[[:space:]]+commit([[:space:]]|$)' <<<"$cmd" || exit 0
grep -Eq '(^|[[:space:]])--dry-run([[:space:]]|=|$)' <<<"$cmd" && exit 0
grep -Eq '(^|[[:space:]])(-h|--help)([[:space:]]|$)' <<<"$cmd" && exit 0

# 2) Explicit override for deliberate integration onto main.
grep -Eq '(^|[[:space:]])ALLOW_MAIN_COMMIT=1([[:space:]]|$)' <<<"$cmd" && exit 0

# 3) Resolve the effective directory the commit would run in: first a leading
#    `cd <path> &&|;` prefix (the recommended dispatch pattern), then a
#    `git -C <path>` override of the directory git operates on.
# resolve_against BASE TARGET: TARGET verbatim when absolute, else BASE/TARGET.
resolve_against() {
  case "$2" in
    /*) printf '%s\n' "$2" ;;
    *)  printf '%s\n' "$1/$2" ;;
  esac
}
dir="$cwd"
for pattern in '^[[:space:]]*cd[[:space:]]+([^[:space:];&|]+)' \
               'git[[:space:]]+-C[[:space:]]+([^[:space:];&|]+)'; do
  if [[ "$cmd" =~ $pattern ]]; then
    dir=$(resolve_against "$dir" "${BASH_REMATCH[1]}")
  fi
done

# 4) Must be inside a git work tree.
git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# abs_git_path DIR FLAG: absolute path from `git rev-parse` for FLAG in DIR.
abs_git_path() {
  git -C "$1" rev-parse --path-format=absolute "$2" 2>/dev/null
}

# 5) Scope to this marketplace repo only.
common_dir=$(abs_git_path "$dir" --git-common-dir) || exit 0
repo_root=$(dirname "$common_dir")
[[ -f "$repo_root/.claude-plugin/marketplace.json" ]] || exit 0

# 6) PRIMARY checkout? (git-dir == git-common-dir only in the primary work tree)
git_dir=$(abs_git_path "$dir" --git-dir) || exit 0
[[ "$git_dir" == "$common_dir" ]] || exit 0

# 7) On branch `main`?
branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD 2>/dev/null) || exit 0
[[ "$branch" == "main" ]] || exit 0

# 8) Are linked worktrees active? (worktree list always includes the primary)
wt_count=$(git -C "$dir" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)
[[ "${wt_count:-0}" -gt 1 ]] || exit 0

# All conditions met -> deny.
reason="Blocked: 'git commit' on the PRIMARY checkout's 'main' while $((wt_count - 1)) linked worktree(s) are active. During worktree-based authoring, shells start at the primary checkout, so a bare commit lands on primary 'main' instead of your worktree branch. Fix: cd into the intended worktree (see 'git worktree list') and commit there, or use 'git -C <worktree> commit'. If you are DELIBERATELY integrating onto main, prefix the command with 'ALLOW_MAIN_COMMIT=1'. Guard: scripts/agent-hooks/pretooluse-worktree-commit-guard.sh (graduated from issue #93)."

jq -n --arg r "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $r
  }
}'
exit 0
