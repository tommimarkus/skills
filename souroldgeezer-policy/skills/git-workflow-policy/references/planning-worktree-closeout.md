# Planning worktree closeout

Load this procedure only when a planning-policy delegated step returned a
successful commit, or when retiring a specifically approved patch-equivalent
historical branch.

Resolve the Git-policy-owned helper with the active host form:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/planning_worktree.py" --help
uv run python "<skill-dir>/references/scripts/planning_worktree.py" --help
```

The parent passes the exact target, branch, registered worktree, and returned
commit to `integrate`. The helper requires clean parent and leaf worktrees, no
active Git operation or leaf upstream, rebases onto the current parent tip, and
fast-forward-only merges. A conflict is aborted with the source branch kept.
Routine integration never cherry-picks. Its bounded
`planning-worktree-result-v1` records source, rebased, and parent commit
identities plus the exact branch/worktree.

Pass the successful integrate result to `cleanup`. It proves the exact branch
is in `git branch --merged <target>`, removes the clean worktree, prunes
metadata, and uses `git branch -d`; it never force-deletes. If cleanup fails,
retain the branch and retry after fixing the stated condition.

Use `integrate --require-patch-equivalent` only for explicitly approved
historical retirement: every `git cherry` row must be `-`, and the rebased
branch must equal the parent tip, so the operation cannot introduce content.
