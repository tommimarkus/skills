---
name: git-workflow-policy
description: "Use when loaded repo guidance initializes git-workflow-policy, or when asked to inspect, adopt, or enforce developer git policy for branches, staging, commits, worktree hygiene, destructive git actions, PR/MR handoff, or version-policy placement. Not for PR/MR execution or releases."
---

# Git Workflow Policy

Own standing developer git rules for repositories that explicitly initialize
this policy. The shared enforcement posture — passive install, opt-in through
the consumer's own guidance, the standing line as enforcement authority — is
canonical in
[`../../docs/policy-reference/policy-posture-core.md`](../../docs/policy-reference/policy-posture-core.md);
once initialized, that guidance is authority for matching git workflow actions.

Inputs: request, repo identity/remotes, repo guidance, branch/worktree/upstream
state, base/default branch, provider evidence when available, version-policy
files when relevant.
Evidence: cite the initialization source or explicit request, git state, policy
options, exceptions, delegation, and verification or blocker.

Read [references/core-workflow.md](references/core-workflow.md) before real
workflow decisions, guidance edits, or enforcement. When editing triggers,
behavior, source grounding, or evals, also read `references/evals` and
[references/source-grounding.md](references/source-grounding.md).
For a planning-policy delegated integration/cleanup or approved historical
equivalence retirement, also read
[planning-worktree closeout](references/planning-worktree-closeout.md), then
drive its deterministic
[`planning_worktree.py`](references/scripts/planning_worktree.py) helper. Verify
the packaged command with `uv run python
"${CLAUDE_SKILL_DIR}/references/scripts/planning_worktree.py" --help` (Codex:
replace `${CLAUDE_SKILL_DIR}` with the loaded absolute `<skill-dir>`).

Modes: default `enforce-initialized` when loaded repo guidance initializes this
policy and the requested action touches developer git workflow; otherwise
default `lookup`. Narrower modes are `inspect`, `adopt-guidance`, and
`preflight`. Modes scope work; live git state and repo guidance remain
authoritative.

Rules: do not enforce just because the plugin is installed. Enforce only when
loaded repo guidance initializes `git-workflow-policy` or the user explicitly
asks. Treat a repo guidance initialization line as current-task policy authority
before matching branch, staging, commit, merge, rebase, force-push, destructive
git, or PR/MR handoff actions; do not wait for the user to name the skill in the
task. Initialization may include options, for example
`git-workflow-policy: feature branches, clean worktree, no direct main`.
If initialization names no options, apply the default profile in
`references/core-workflow.md`.
In `adopt-guidance`, absorb existing related guidance into initialization
options or adjacent local exceptions, then remove or replace competing workflow
prose; do not leave a pointer beside duplicate branch/staging/commit rules.
Delegate PR/MR lifecycle writes to `pr-ops`, issues to `issue-ops`, releases to
`release-policy`, security to `devsecops-audit`, and test adequacy to
`test-quality-audit`.

Ask vs continue: continue only when repository, target branch, policy,
exceptions, work area, and verification are clear. If repository identity, base
branch, integration authority, destructive git action, or policy precedence is
ambiguous, stop and ask instead of guessing.

Stop before history rewrites, branch deletion, force push, tags, publishing, or
merge/close actions unless a sibling skill has authority. Stop if required
verification cannot run and no documented substitute exists.

After guidance edits, rerun structured-file checks, `git diff --check`, and the
repo's documented skill-architecture or docs validation. End with the output
footer from `references/core-workflow.md`.
