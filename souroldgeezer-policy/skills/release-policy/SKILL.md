---
name: release-policy
description: "Use when repo guidance initializes release-policy, or when asked to inspect, adopt, or enforce release policy for automatic version bumping, version strategy, notes, tags, provider releases, publication, rollback, post-release checks, or release exceptions. Not for git workflow or PR/MR execution."
---

# Release Policy

Own standing release and distribution rules for repositories that explicitly
initialize this policy. Installing the plugin is passive; a consuming repo must
opt in through its own guidance, such as `AGENTS.md` or `CLAUDE.md`.

Inputs: request, repo identity, branch/worktree state, release candidate,
version source, notes/changelog, tags, provider release state, publication
target, tooling/auth, release guidance, verification, rollback guidance.
Evidence: cite the initialization source or explicit request, git state,
candidate, policy options, version source, tags/provider state, target,
verification, delegation, and blocker.

Read [references/core-workflow.md](references/core-workflow.md) before real
release decisions or writes. Use
[references/scripts/version-bump](references/scripts/version-bump)
`--help` before automatic version bump calculation or version-source writes.
When editing triggers, behavior, source grounding, evals, or helper scripts,
also inspect [references/scripts/](references/scripts/) and
`references/scripts/version_bump/`, read `references/evals`, and read
[references/source-grounding.md](references/source-grounding.md).

Modes: default `enforce-initialized` when repo guidance initializes this policy;
otherwise default `lookup`. Narrower modes are `preflight`, `adopt-guidance`,
`prepare-release`, `cut-release`, `publish`, `post-release`, and `resume`.
Modes scope work; verification and publication gates remain mandatory.

Rules: do not enforce just because the plugin is installed. Enforce only when
repo guidance initializes `release-policy` or the user explicitly asks.
Initialization may include options, for example
`release-policy: calver YYYY.MM.build, git tagging`. Initialized options can
grant standing authority for routine version updates and git tag creation for
releasable changes after verification. Provider releases, publication, and
destructive corrections still require explicit authority unless the initialized
policy names the target and action. If initialization names no options, apply
the default profile in `references/core-workflow.md`. For SemVer, CalVer, and
PEP 440-style bumps, prefer the bundled `version-bump` helper over manual
version arithmetic; it is dry-run by default and requires `--write` for source
updates. Apply `git-workflow-policy` preflight before release writes. Delegate
PR/MR lifecycle actions to `pr-ops`, issues to `issue-ops`, security controls
to `devsecops-audit`, and test adequacy to `test-quality-audit`.

Ask vs continue: continue only for read-only preflight/lookup, local
verification, and clearly authorized release-prep edits. If release candidate,
version source, tag/provider release, publication target or authority,
credentials, rollback path, or destructive correction is ambiguous, stop and ask
instead of guessing.

Stop when required verification fails or cannot run without a documented
substitute, or when conflicting release state cannot be reconciled safely.

After release-prep edits, rerun structured-file checks, `git diff --check`, and
the repo's documented release, packaging, or skill-architecture validation. End
with the output footer from `references/core-workflow.md`.
