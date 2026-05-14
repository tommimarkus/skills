---
name: pr-ops
description: Use when the user explicitly asks to create, review, update, fix, merge, close, resume, or process one or more pull requests, merge requests, or prepared PR/MR branches end to end; loads provider extensions such as GitHub™ or GitLab™ only after the provider is identified.
---

# PR Ops

Run explicit pull-request or merge-request lifecycle work after the user asks
for it or a sibling skill hands off a prepared branch. Own target resolution,
PR/MR creation or reuse, live-state authority, reviews/comments/checks, safe
branch update, verification, merge/close authority, cleanup, and completion
reporting.

Inputs: user request, PR/MR identifiers or URLs, prepared branch targets,
repository remotes, current git branch/status/worktrees, provider auth/tooling,
base/head refs, reviews, comments, checks, linked work, and lifecycle markers.
Evidence: cite the provider state, git refs/status, checks, review state, and
verification commands inspected before writing, merging, closing, or reporting.

Do not use this skill for incidental PR/MR mentions, issue lifecycle work
without an explicit prepared-branch handoff, standalone deep CI debugging,
security posture review, design review, test-quality audit, or general
project-management advice.

Before acting on a real lifecycle, read
[references/core-workflow.md](references/core-workflow.md). When changing
trigger metadata, workflow behavior, provider handoff rules, source grounding,
or evaluation coverage, read `references/evals` and
`references/source-grounding.md`; keep evals synthetic or originally
paraphrased.

## Modes

Default mode is `full-cycle`: inspect the requested PR/MR, prepared branch, or
queue; create or reuse a PR/MR when the target is a prepared branch; classify
reviews, comments, checks, branch state, and merge safety; address clear
actionable work; verify; update the branch when safe; request review when
appropriate; monitor pending required checks to terminal state or escalation;
merge or close only when authorized; and clean up owned work areas.

Use narrower modes only when requested: `review-only`, `create-or-update`,
`checks-only`, `address-feedback`, `merge-only`, or `resume`. Provider modes add
mechanics; they do not replace the core authority, escalation, ledger,
verification, monitoring, cleanup, or completion contract.

## Provider Selection

Identify the provider from the PR/MR URL, repository remote, configured tooling,
identifier shape, prepared branch repository, sibling-skill handoff, or explicit
user wording.

- GitHub: read [extensions/github.md](extensions/github.md) before resolving or
  writing provider state, review threads, branches, checks, merge, close, or
  cleanup.
- GitLab: read [extensions/gitlab.md](extensions/gitlab.md) before resolving or
  writing provider state, discussions, branches, pipelines, merge, close, or
  cleanup.
- New providers follow [extensions/README.md](extensions/README.md).
- If no provider can be identified, ask one concise provider/repository
  question.
- If a provider is identified but unsupported, stop and report the missing
  extension.

## Core Rules

- Live provider state and live git state are authoritative.
- Pending required checks in `full-cycle` are active work, not a final state.
- Continue autonomously only when target, repo, tooling, permissions, work area,
  verification, branch update, and merge/close authority are clear.
- Ask only for global blockers; escalate item-local ambiguity through the
  provider when possible and continue the queue.
- Implement only clear in-scope feedback or check-failure remediation.
- Auto-fix only deterministic formatter, generated-file, or lint failures.
- Re-read live state before PR/MR creation, push, branch update, review request,
  thread resolution, merge, close, branch deletion, or final lifecycle writes.

End with the output footer from `references/core-workflow.md`.
