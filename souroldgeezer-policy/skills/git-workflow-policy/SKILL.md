---
name: git-workflow-policy
description: "Use when repo guidance initializes git-workflow-policy, or when asked to inspect, adopt, or enforce developer git policy for branches, staging, commits, worktree hygiene, destructive git actions, PR/MR handoff, or version-policy placement. Not for PR/MR execution or releases."
---

# Git Workflow Policy

Own standing developer git rules for repositories that explicitly initialize
this policy. Installing the plugin is passive; a consuming repo must opt in
through its own guidance, such as `AGENTS.md` or `CLAUDE.md`.

Inputs: request, repo identity/remotes, repo guidance, branch/worktree/upstream
state, base/default branch, provider evidence when available, version-policy
files when relevant.
Evidence: cite the initialization source or explicit request, git state, policy
options, exceptions, delegation, and verification or blocker.

Read [references/core-workflow.md](references/core-workflow.md) before real
workflow decisions, guidance edits, or enforcement. When editing triggers,
behavior, source grounding, or evals, also read `references/evals` and
[references/source-grounding.md](references/source-grounding.md).

Modes: default `enforce-initialized` when repo guidance initializes this policy;
otherwise default `lookup`. Narrower modes are `inspect`, `adopt-guidance`, and
`preflight`. Modes scope work; live git state and repo guidance remain
authoritative.

Rules: do not enforce just because the plugin is installed. Enforce only when
repo guidance initializes `git-workflow-policy` or the user explicitly asks.
Initialization may include options, for example
`git-workflow-policy: feature branches, clean worktree, no direct main`.
If initialization names no options, apply the default profile in
`references/core-workflow.md`.
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
