---
name: release-policy
description: "Use when loaded repo guidance initializes release-policy, or when asked to inspect, adopt, or enforce release policy for version updates, version strategy, notes, tags, provider releases, publication, rollback, post-release checks, or release exceptions. Not for git workflow or PR/MR execution."
---

# Release Policy

Own standing release and distribution rules for repositories that explicitly
initialize this policy. Installing the plugin is passive; a consuming repo must
opt in through its own guidance, such as `AGENTS.md` or `CLAUDE.md`.
Once loaded repo guidance initializes this policy, that guidance is standing
enforcement authority for matching release actions.

Inputs/evidence: inspect request, repo guidance, git state, candidate, version
source/strategy, notes, tags/provider releases, targets/auth, verification, and
rollback guidance. Cite source, options, actions, delegation, and blockers.

Read [references/core-workflow.md](references/core-workflow.md) before real
release decisions or writes. When editing behavior or evals, inspect
`references/evals` and
[references/source-grounding.md](references/source-grounding.md).

Modes: default `enforce-initialized` when loaded guidance initializes this
policy and the request touches release/distribution; otherwise `lookup`. Other
modes: `preflight`, `adopt-guidance`, `prepare-release`, `cut-release`,
`publish`, `post-release`, `resume`.
Modes scope work; verification and publication gates remain mandatory.

Rules: plugin install alone never enforces. Enforce only when loaded guidance
initializes `release-policy` or the user asks. Treat initialization as
current-task authority before version, notes, tag, provider release,
publication, rollback, or exception actions; do not wait for the user to name
the skill. Bare initialization uses `references/core-workflow.md`. Initialized
options can authorize routine version updates and git tags after verification;
provider releases, publication, and destructive corrections still require named
target/action authority. Apply `git-workflow-policy` preflight before release
writes. Delegate PR/MR lifecycle to `pr-ops`, issues to `issue-ops`, security to
`devsecops-audit`, and test adequacy to `test-quality-audit`.

In `adopt-guidance`, absorb existing related guidance into initialization
options/exceptions, then remove or replace competing release prose; do not leave
a pointer beside duplicate version/tag/publication rules.

Ask vs continue: continue only for read-only preflight/lookup, local
verification, and authorized release-prep edits. If candidate, version source,
tag/provider release, publication target/authority, credentials, rollback, or
destructive correction is ambiguous, stop and ask.

Stop when required verification fails or cannot run without a documented
substitute, or when conflicting release state cannot be reconciled safely.

After release-prep edits, rerun structured-file checks, `git diff --check`, and
the repo's documented release, packaging, or skill-architecture validation. End
with the output footer from `references/core-workflow.md`.
