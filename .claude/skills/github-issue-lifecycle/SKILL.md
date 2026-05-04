---
name: github-issue-lifecycle
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more GitHub™ issues end to end in this repository.
---

# GitHub Issue Lifecycle

## Purpose

Run this repository's opinionated GitHub issue lifecycle by composing the public
`issue-ops` skill with its GitHub extension, then applying repo-local defaults
and gates.

Use this internal skill only for explicit GitHub issue lifecycle requests in
this repository. Do not use it for incidental issue mentions, ordinary PR
review, standalone CI debugging, general GitHub questions, or published
marketplace/plugin distribution questions.

When changing trigger metadata, workflow behavior, repo-local gates, source
grounding, or evaluation coverage for this skill, read `references/evals` and
`references/source-grounding.md` first. Keep eval cases synthetic or originally
paraphrased; do not copy issue, review, or runbook text into this internal
skill.

## Source Of Truth Stack

Follow these layers in order:

1. Public `issue-ops` core at
   `souroldgeezer-ops/skills/issue-ops/SKILL.md`.
2. GitHub provider extension at
   `souroldgeezer-ops/skills/issue-ops/extensions/github.md`.
3. This repo-local overlay.

If this overlay conflicts with the public core on repo-specific behavior, this
overlay wins only inside this repository. If the public core or GitHub extension
changes a general lifecycle contract, update this overlay in the same change.

## Evidence Contract

Before acting, inspect these inputs and use them as the evidence basis for the
run: explicit issue scope from the user request, live GitHub issue state, latest
comments, linked PRs, lifecycle markers, repo identity and remotes, git branch
status and worktrees, repo guidance, and likely touched surfaces.

Evidence: the lifecycle marker and completion output must name the live issue
state, inspected repo or git state, verification commands, and repo-local gates
that materially shaped the disposition.

## Repo Defaults

Default mode remains `full-cycle` unless the user explicitly asks for
`triage-only`, `plan-only`, `implement-only`, `resume`, or `pr-mode`.

Use direct-main mode for clearly actionable repo-maintenance issues when live
GitHub state, git state, branch protection, permissions, and verification are
safe. Use PR-mode when the issue, branch policy, review state, or user request
requires review before merge.

For active issues, re-read live GitHub state, latest comments, lifecycle
markers, linked PRs, repo remotes, branch status, and worktrees before
direct-main integration, PR update or merge, issue closure, or final lifecycle
marker writes.

Use these dedicated worktrees unless they are dirty or occupied:

```text
.worktrees/github-issue-lifecycle-main
.worktrees/issue-<number>
```

Keep direct-main issue branches local. Prefer one clean commit named
`Fix #<number>: <title>` for defects or `Resolve #<number>: <title>`
otherwise.

Use the repo-local ledger as recovery hints only:

```text
.cache/github-issue-lifecycle/ledger.jsonl
```

Never commit the ledger. Never store secrets, tokens, raw logs, full issue
bodies, or sensitive excerpts in it.

## Ask Vs Continue

Continue when the public `issue-ops` core, GitHub extension, this overlay, live
GitHub state, and git state make the issue scope, integration path, and
verification path clear.

Ask the user only for global blockers that stop the run, such as unusable auth,
missing push permission, missing required verification tooling, or an unusable
base branch.

For issue-local ambiguity, do not guess and do not ask immediately during queue
processing. Escalate the issue with a lifecycle marker, record the evidence,
and continue the queue where possible. Issue-local ambiguity includes missing
acceptance criteria, conflicting comments, duplicate precedence, uncertain
skill contract, unsafe existing PR state, or stale lifecycle ownership.

## Repo-Specific Gates

Before implementing issue content, run `.claude/skills/ip-hygiene/SKILL.md`
triage when the issue body, comments, referenced material, or likely touched
files involve:

- `souroldgeezer-*/skills/**`;
- `souroldgeezer-*/agents/**`;
- `souroldgeezer-*/docs/*-reference/**`;
- `.claude/skills/**`;
- Claude Code or Codex plugin manifests;
- marketplace manifests;
- `README.md`, `CLAUDE.md`, or `AGENTS.md` sections that describe those
  artifacts.

Escalate the issue on any `ip-hygiene` concern that requires maintainer
judgment.

For published skill, plugin, agent, runtime metadata, bundled reference,
extension, manifest, marketplace, internal authoring skill, or repo-doc changes,
apply `docs/skill-architecture.md` and run `scripts/skill-architecture-report.sh`
when available.

Keep these surfaces synchronized when touched by an issue:

- public skill `SKILL.md`;
- provider extension files;
- matching Claude Code subagent;
- project-scoped Codex wrapper;
- `skills/<skill>/agents/openai.yaml`;
- both plugin manifests;
- `.claude-plugin/marketplace.json`;
- `README.md`;
- `CLAUDE.md`;
- `AGENTS.md` when Codex entry rules change.

## Completion Output

Use the public `issue-ops` completion output. Also name any repo-local gates
used, such as `ip-hygiene` or `skill-architecture-report`, in the verification
summary.

## Verification And Rerun

Run the public `issue-ops` and GitHub-extension verification selected for the
touched files. For this repository, run `scripts/skill-architecture-report.sh .`
when skill, plugin, agent, runtime metadata, marketplace, internal authoring
skill, or repo-guidance surfaces are touched.

Rerun validation after fixing validation findings before completion.
