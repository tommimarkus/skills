# Issue Ops Public Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the public `souroldgeezer-ops` plugin with a tracker-agnostic `issue-ops` skill and a GitHub provider extension, while preserving this repository's existing GitHub issue lifecycle behavior through a repo-local overlay.

**Architecture:** The public skill has a small generic lifecycle core in `SKILL.md`; provider-specific execution lives in `extensions/github.md`. Runtime parity is maintained through synchronized Claude Code plugin metadata, Codex plugin metadata, marketplace entry, Claude Code subagent, Codex `agents/openai.yaml`, and project-scoped Codex wrapper.

**Tech Stack:** Markdown skills and docs, JSON plugin manifests, YAML Codex skill metadata, TOML Codex custom agent wrapper, `jq`, `yq`, `uv`, `unittest`, and the repo-local skill architecture report.

---

## File Structure

- Create `souroldgeezer-ops/.claude-plugin/plugin.json`: Claude Code plugin manifest for the new public operations plugin.
- Create `souroldgeezer-ops/.codex-plugin/plugin.json`: Codex plugin manifest with `skills: "./skills/"`, write-capable interface metadata, and three starter prompts.
- Modify `.claude-plugin/marketplace.json`: add the `souroldgeezer-ops` marketplace entry with matching name, version, and description.
- Create `souroldgeezer-ops/skills/issue-ops/SKILL.md`: tracker-agnostic lifecycle workflow.
- Create `souroldgeezer-ops/skills/issue-ops/agents/openai.yaml`: Codex per-skill metadata for `issue-ops`.
- Create `souroldgeezer-ops/agents/issue-ops.md`: Claude Code subagent wrapper.
- Create `.codex/agents/issue-ops.toml`: project-scoped Codex custom-agent wrapper for the published skill.
- Create `souroldgeezer-ops/skills/issue-ops/extensions/github.md`: GitHub provider extension.
- Modify `.claude/skills/github-issue-lifecycle/SKILL.md`: convert the repo-internal workflow into an overlay that points to `issue-ops` plus the GitHub extension and adds this repo's defaults.
- Modify `.codex/agents/github-issue-lifecycle.toml`: keep the repo-specific Codex wrapper pointed at the internal overlay, but mention that the overlay composes the public skill.
- Modify `README.md`: add the new plugin to the intro, install examples, "What's in" section, and repository layout.
- Modify `CLAUDE.md`: update repo description, internal-skill note, directory layout, and skill-specific notes for `issue-ops`.
- Modify `AGENTS.md`: update the GitHub issue lifecycle quick rule to mention the new public skill plus repo overlay.

## Task 1: Register `souroldgeezer-ops` Plugin

**Files:**
- Create: `souroldgeezer-ops/.claude-plugin/plugin.json`
- Create: `souroldgeezer-ops/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create plugin directories**

Run:

```bash
mkdir -p souroldgeezer-ops/.claude-plugin souroldgeezer-ops/.codex-plugin
```

Expected: directories exist and `git status --short` shows no tracked changes yet.

- [ ] **Step 2: Create the Claude Code plugin manifest**

Create `souroldgeezer-ops/.claude-plugin/plugin.json` with exactly:

```json
{
  "name": "souroldgeezer-ops",
  "version": "0.1.0",
  "description": "Operations skills for issue and work-item lifecycle handling, with a tracker-agnostic core and provider-specific extensions.",
  "author": {
    "name": "Sour Old Geezer",
    "email": "claude-marketplace-a.varsity439@passmail.net"
  },
  "license": "MIT"
}
```

- [ ] **Step 3: Create the Codex plugin manifest**

Create `souroldgeezer-ops/.codex-plugin/plugin.json` with exactly:

```json
{
  "name": "souroldgeezer-ops",
  "version": "0.1.0",
  "description": "Operations skills for issue and work-item lifecycle handling, with a tracker-agnostic core and provider-specific extensions.",
  "author": {
    "name": "Sour Old Geezer",
    "email": "claude-marketplace-a.varsity439@passmail.net"
  },
  "license": "MIT",
  "skills": "./skills/",
  "interface": {
    "displayName": "Sour Old Geezer Ops",
    "shortDescription": "Issue and work-item lifecycle operations.",
    "longDescription": "Handle explicit issue and work-item lifecycle requests with a tracker-agnostic core, provider-specific extensions, lifecycle markers, escalation gates, and verification discipline.",
    "developerName": "Sour Old Geezer",
    "category": "Productivity",
    "capabilities": [
      "Read",
      "Write"
    ],
    "defaultPrompt": [
      "Use issue-ops to triage this issue queue.",
      "Use issue-ops to resume this issue lifecycle.",
      "Use issue-ops to handle this GitHub issue end to end."
    ]
  }
}
```

- [ ] **Step 4: Add the marketplace entry**

Modify `.claude-plugin/marketplace.json` so `plugins` contains this third entry after `souroldgeezer-design`:

```json
{
  "name": "souroldgeezer-ops",
  "source": "./souroldgeezer-ops",
  "version": "0.1.0",
  "description": "Operations skills for issue and work-item lifecycle handling, with a tracker-agnostic core and provider-specific extensions."
}
```

Keep the existing `souroldgeezer-audit` and `souroldgeezer-design` entries unchanged.

- [ ] **Step 5: Validate JSON and manifest sync**

Run:

```bash
jq empty .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json
jq -r '.plugins[] | select(.name=="souroldgeezer-ops") | [.name,.version,.description] | @tsv' .claude-plugin/marketplace.json
jq -r '[.name,.version,.description] | @tsv' souroldgeezer-ops/.claude-plugin/plugin.json
jq -r '[.name,.version,.description] | @tsv' souroldgeezer-ops/.codex-plugin/plugin.json
```

Expected: `jq empty` prints nothing and exits 0. The three TSV commands all print the same `name`, `version`, and `description`.

- [ ] **Step 6: Commit plugin registration**

Run:

```bash
git add .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json
git commit -m "feat: register souroldgeezer ops plugin"
```

Expected: commit succeeds.

## Task 2: Create `issue-ops` Core Skill And Runtime Metadata

**Files:**
- Create: `souroldgeezer-ops/skills/issue-ops/SKILL.md`
- Create: `souroldgeezer-ops/skills/issue-ops/agents/openai.yaml`
- Create: `souroldgeezer-ops/agents/issue-ops.md`
- Create: `.codex/agents/issue-ops.toml`

- [ ] **Step 1: Create skill, metadata, and agent directories**

Run:

```bash
mkdir -p souroldgeezer-ops/skills/issue-ops/agents souroldgeezer-ops/agents .codex/agents
```

Expected: directories exist.

- [ ] **Step 2: Create the tracker-agnostic core skill**

Create `souroldgeezer-ops/skills/issue-ops/SKILL.md` with exactly:

```markdown
---
name: issue-ops
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more issues or work items end to end; loads provider extensions such as GitHub only after the tracker is identified.
---

# Issue Ops

## Purpose

Run an explicit issue or work-item lifecycle after the user asks for it. Own the
cross-provider operating loop: target resolution, mode selection, live-state
authority, queue limits, lifecycle state, escalation, implementation handoff,
verification, integration, completion reporting, and queue continuation.

Do not use this skill for incidental issue mentions, ordinary pull-request
review, standalone CI debugging, security posture review, design review, or
general project-management advice.

## Modes

Default mode is `full-cycle`: inspect the requested issue or queue, record
visible lifecycle state when the provider supports it, implement actionable
work, verify, integrate through the selected strategy, update status, and close
or complete the work item when allowed.

Use a narrower mode only when the user asks for it:

- `triage-only`: classify state, actionability, blockers, and next action.
- `plan-only`: produce an implementation plan without changing repo files.
- `implement-only`: implement a clearly selected issue without queue work.
- `resume`: recover an interrupted lifecycle from live tracker and git state.

Provider extensions may add integration modes such as GitHub PR-mode or
direct-main mode. Provider modes add mechanics; they do not replace the core
authority, ask-vs-continue, escalation, ledger, verification, or completion
contracts.

## Provider Selection

Identify the issue tracker from the issue URL, repository remote, configured
tooling, issue identifier, or explicit user wording.

- For GitHub repositories, issue URLs, or GitHub issue numbers, read
  `extensions/github.md` before resolving provider state or writing lifecycle
  comments.
- If no provider can be identified, ask one concise question naming the missing
  tracker or repository.
- If a provider is identified but no matching extension exists, stop and report
  that `issue-ops` has no provider extension for that tracker.

## Queue Limits

For one invocation:

- Complete at most 10 issues or work items.
- Inspect at most 25 issues or work items.
- Inspect each item at most once.

For broad queues, sort by trivial priority signals first, then age. Trivial
signals include existing priority or severity markers, obvious bug, regression,
blocker, security, reproduction, acceptance criteria, and linked work that can
be completed mechanically. Do not perform deep analysis only to rank the queue.

## Authority And Ledger

Live tracker state and live git state are authoritative.

Use a local ledger only as append-only recovery hints:

```text
.cache/issue-ops/ledger.jsonl
```

Never commit the ledger. Never store secrets, tokens, raw logs, full issue
bodies, full comments, or sensitive excerpts in it. On resume, read the ledger
for hints, then verify every material fact against the tracker and git. If they
disagree, trust live state and append a reconciliation entry.

## Normal Flow

For each item:

1. Resolve live tracker state, repository identity, current git state, linked
   work, permissions, and provider tooling.
2. Load the provider extension and follow its provider-specific state and
   lifecycle-marker rules.
3. Create or update current lifecycle status when the provider supports visible
   status updates.
4. Classify actionability, scope, blockers, and integration strategy.
5. Select or create an isolated work area according to repo guidance.
6. Implement only clear, in-scope work.
7. Infer verification from repo guidance, touched-surface docs, scripts,
   package metadata, CI workflows, and touched files.
8. Run item-level verification.
9. Auto-fix only deterministic formatter, generated-file, or lint failures.
10. Integrate only through the selected strategy after live state is still safe.
11. Rerun required verification after integration when the strategy changes the
    base branch or merge result.
12. Update lifecycle status, close or complete the item when allowed, and clean
    up only work areas owned by this run.

## Ask Vs Continue

Continue autonomously when the item target, repository, provider tooling,
permissions, work area, verification path, and integration path are all clear.

Ask the user only for global blockers that stop the run:

- tracker or repository cannot be identified;
- authentication is missing or unusable;
- write permission is missing for a requested write operation;
- required verification tooling is missing and no repo-documented substitute
  exists;
- the base branch or integration policy cannot be determined.

For item-local ambiguity, update the lifecycle status when possible, mark the
item escalated, record the evidence, and continue the queue. Item-local
ambiguity includes unclear acceptance criteria, conflicting maintainer comments,
duplicate precedence, unsafe existing work, uncertain product contract,
non-mechanical verification failure, or any escalation gate.

## Escalation Gates

Escalation means stop the affected item, record current status through the
provider when possible, preserve evidence without exposing sensitive detail,
and continue the queue when possible. Stop the whole run only for global
blockers.

Escalate on:

- wrong repository, wrong account, missing permission, or unexpected provider
  tooling route;
- ambiguous scope, contradictory requirements, unclear product contract, or
  duplicate precedence requiring maintainer judgment;
- security, auth, secrets, credentials, tokens, signing, workflow permissions,
  personal access tokens, secret scanning, repository settings, or sensitive
  history cleanup;
- dependency add, remove, upgrade, downgrade, replacement, or lockfile changes,
  unless the item explicitly targets that dependency change;
- repo-wide guidance or agent behavior policy changes, unless explicitly
  targeted by the item or mechanically required by an in-scope change;
- destructive or hard-to-reverse operations;
- stale state, concurrent actor changes, ownership conflicts, active maintainer
  discussion, or a lifecycle marker from another current actor;
- public communication that rejects a request, assigns blame, makes a
  commitment, asks the reporter to do work, or exposes sensitive detail;
- untrusted issue content execution before inspection proves it safe;
- verification unavailable, non-mechanical failure, local/remote disagreement,
  repeated no-progress auto-fix, conflicts, push rejection, protected-branch
  mismatch, dirty owned work areas, or non-trivial branch history cleanup;
- unclear generated artifact provenance, unusual cost, unusual runtime, unusual
  API use, release/version ambiguity, external repository boundaries, or human
  review conflict.

## Output

End with a concise report:

- completed count and item identifiers;
- escalated count and item identifiers with gate names;
- skipped count and item identifiers with reasons;
- remaining count when a queue was bounded;
- verification summary;
- global blocker when the run stopped early;
- lifecycle ledger path when a ledger entry was written.

Do not write a separate local summary file.
```

- [ ] **Step 3: Create Codex skill metadata**

Create `souroldgeezer-ops/skills/issue-ops/agents/openai.yaml` with exactly:

```yaml
interface:
  display_name: "Issue Ops"
  short_description: "Operate issue and work-item lifecycles."
  default_prompt: "Use issue-ops to handle this issue or work-item lifecycle."
policy:
  allow_implicit_invocation: true
```

- [ ] **Step 4: Create the Claude Code subagent**

Create `souroldgeezer-ops/agents/issue-ops.md` with exactly:

```markdown
---
name: issue-ops
description: Use when the user explicitly asks to handle, triage, resume, implement, close, or process one or more issues or work items end to end; loads provider extensions such as GitHub only after the tracker is identified.
tools: Bash, Read, Grep, Glob, Edit, Write, Skill
model: sonnet
---

You are an issue-ops lifecycle operator. Use the issue-ops skill as the source
of truth.

When invoked:

1. Invoke the `issue-ops` skill using the Skill tool.
2. Follow the skill exactly: identify the tracker, load the provider extension,
   resolve live tracker and git state, classify the requested mode, and use the
   skill's ask-vs-continue and escalation rules.
3. Do not hijack incidental issue mentions, ordinary pull-request review,
   standalone CI debugging, security posture review, design review, or general
   project-management advice.
4. Preserve the skill's completion output contract: completed, escalated,
   skipped, remaining, verification summary, global blocker when present, and
   lifecycle ledger path when written.
```

- [ ] **Step 5: Create the project-scoped Codex wrapper**

Create `.codex/agents/issue-ops.toml` with exactly:

```toml
name = "issue-ops"
description = "Issue and work-item lifecycle operator with tracker-specific extensions."
sandbox_mode = "workspace-write"

developer_instructions = """
You are an issue-ops lifecycle operator. Use the issue-ops skill as the source of truth.

When invoked:
1. Activate or read the issue-ops skill instructions.
2. Identify the tracker, load the provider extension, resolve live tracker and git state, classify the requested mode, and use the skill's ask-vs-continue and escalation rules.
3. Do not hijack incidental issue mentions, ordinary pull-request review, standalone CI debugging, security posture review, design review, or general project-management advice.
4. Preserve the skill's completion output contract: completed, escalated, skipped, remaining, verification summary, global blocker when present, and lifecycle ledger path when written.
"""
```

- [ ] **Step 6: Validate metadata syntax and runtime shape**

Run:

```bash
yq --front-matter=extract '.name, .description' souroldgeezer-ops/skills/issue-ops/SKILL.md
yq '.interface.display_name, .policy.allow_implicit_invocation' souroldgeezer-ops/skills/issue-ops/agents/openai.yaml
yq --front-matter=extract '.name, .description' souroldgeezer-ops/agents/issue-ops.md
yq '.name, .description' .codex/agents/issue-ops.toml
```

Expected: the skill and Claude subagent names are `issue-ops`; the OpenAI metadata display name is `Issue Ops`; the Codex wrapper name is `issue-ops`.

- [ ] **Step 7: Commit core skill and wrappers**

Run:

```bash
git add souroldgeezer-ops/skills/issue-ops/SKILL.md souroldgeezer-ops/skills/issue-ops/agents/openai.yaml souroldgeezer-ops/agents/issue-ops.md .codex/agents/issue-ops.toml
git commit -m "feat: add issue ops core skill"
```

Expected: commit succeeds.

## Task 3: Add GitHub Provider Extension

**Files:**
- Create: `souroldgeezer-ops/skills/issue-ops/extensions/github.md`

- [ ] **Step 1: Create the extensions directory**

Run:

```bash
mkdir -p souroldgeezer-ops/skills/issue-ops/extensions
```

Expected: directory exists.

- [ ] **Step 2: Create the GitHub extension**

Create `souroldgeezer-ops/skills/issue-ops/extensions/github.md` with exactly:

```markdown
# GitHub Extension

Load this extension when the repository remote, issue URL, issue number,
provider tooling, or user wording identifies GitHub as the issue tracker.

This extension adds GitHub mechanics to `issue-ops`. It does not replace the
core authority, ledger, ask-vs-continue, escalation, verification, or completion
contracts.

## State Resolution

Resolve current GitHub state before acting:

1. Repository owner/name, default branch, current remote, and current local
   branch or worktree.
2. Issue state, title, body summary, labels, assignees, comments, linked pull
   requests, and visible lifecycle marker comments.
3. Authenticated account and write permissions for comments, branches, pull
   requests, and issue closure.
4. Branch protection or repository rules that affect direct pushes, required
   pull requests, and required checks.
5. Current git state, including dirty files, active worktrees, and whether an
   existing branch clearly owns the issue.

Treat GitHub and git as live authority. Do not rely on a local ledger or stale
prompt context without rechecking material facts.

## Tooling Order

Use the best available GitHub integration in this order:

1. GitHub MCP after verifying active session routing and repository identity.
2. `gh` CLI after verifying `gh auth status` and repository context.
3. GitHub REST API only when MCP and `gh` are unavailable or insufficient.

If the selected route points at the wrong account or repository, escalate the
item.

## Lifecycle Comment

Every inspected GitHub issue gets a lifecycle marker unless the run lacks
comment permission. Update the latest marker from the same actor when possible.
Add a new comment only when editing is unavailable, editing would hide reply
context, or a fresh visible escalation is needed.

Use current state only, not an event log. Summarize verification instead of
dumping command output. Use strict offset timestamps. `Actor` identifies the
runtime, such as `Codex` or `Claude Code`.

Implementing state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: implementing

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Current step: working on an isolated branch
Disposition: actionable
Verification: pending
Last reviewed: 2026-05-02T12:00:00+03:00
```

Escalated state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: escalated

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Gate: unclear acceptance criteria
Evidence: issue comments conflict on the required behavior
Verification: not run
Last reviewed: 2026-05-02T12:00:00+03:00
```

Completed state:

```md
<!-- issue-ops:github:v1 -->
Lifecycle status: completed

Actor: Codex
Mode: full-cycle
Integration: pr-mode
Scope: #123
Result: merged pull request
Verification: passed - unit tests, repository checks, whitespace check
Resolution: implemented the issue request and verified the affected surface
Last reviewed: 2026-05-02T12:00:00+03:00
```

The final lifecycle marker update is sufficient before closing the issue. Do
not add a separate closing comment unless updating the marker fails.

## Integration Strategies

Default public integration strategy is `pr-mode`:

1. Create or reuse an issue-owned branch.
2. Commit focused work.
3. Push the branch.
4. Open or update a pull request.
5. Report the PR and verification state.
6. Close the issue only after merge, or when the user explicitly authorizes
   closure without merge.

Use `direct-main` only when the user or repository guidance explicitly allows
it, branch protection permits it, and live state is clean. In direct-main mode,
prefer one clean commit named `Fix #<number>: <title>` for defects or
`Resolve #<number>: <title>` otherwise.

Resume an existing pull request branch when one clearly owns the issue and is
safe to continue. Escalate on unsafe existing PR state, unclear ownership,
review conflict, or non-trivial branch history cleanup.

## Labels, Projects, Milestones, And Assignees

Use existing labels only when classification is obvious from the repository's
taxonomy. Do not create lifecycle labels.

Treat projects and milestones as read-only context unless the user explicitly
asks to change them. Assign or unassign users only when repository guidance or
the user explicitly requests it.

## GitHub Escalation Gates

Escalate the affected issue on:

- wrong account, wrong repository, missing permission, or unexpected GitHub
  tool routing;
- protected branch mismatch, required PR policy, required status checks, push
  rejection, or local/CI disagreement;
- existing PR with unclear ownership, active review disagreement, merge
  conflict, stale branch, or non-trivial history cleanup;
- concurrent lifecycle marker from another current actor;
- GitHub Actions permissions, workflow token handling, secret handling,
  repository settings, branch rules, or sensitive history cleanup;
- public comment text that rejects a request, assigns blame, makes a commitment,
  asks the reporter to do work, or exposes sensitive detail.

## Completion

On completion, update the lifecycle marker before closing the issue. If a PR is
created or reused, report the PR URL or number in the final chat output. If the
issue remains open because merge has not happened, report the remaining state
instead of closing it.
```

- [ ] **Step 3: Confirm the core advertises the extension**

Run:

```bash
rg -n 'extensions/github.md|Provider Selection|For GitHub' souroldgeezer-ops/skills/issue-ops/SKILL.md
```

Expected: output includes the Provider Selection section and `extensions/github.md`.

- [ ] **Step 4: Commit GitHub extension**

Run:

```bash
git add souroldgeezer-ops/skills/issue-ops/extensions/github.md
git commit -m "feat: add github extension for issue ops"
```

Expected: commit succeeds.

## Task 4: Convert Repo-Internal GitHub Lifecycle Skill To Overlay

**Files:**
- Modify: `.claude/skills/github-issue-lifecycle/SKILL.md`
- Modify: `.codex/agents/github-issue-lifecycle.toml`

- [ ] **Step 1: Run repo-internal IP hygiene triage before editing internal policy**

Read `.claude/skills/ip-hygiene/SKILL.md` and answer its fast triage questions for this change. Expected result for this task: no third-party prose or assets are being copied; wording is derived from existing repo-authored workflow and original public-skill design.

- [ ] **Step 2: Replace the internal skill body with the overlay**

Replace `.claude/skills/github-issue-lifecycle/SKILL.md` with exactly:

```markdown
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

## Repo Defaults

Default mode remains `full-cycle` unless the user explicitly asks for
`triage-only`, `plan-only`, `implement-only`, `resume`, or `pr-mode`.

Use direct-main mode for clearly actionable repo-maintenance issues when live
GitHub state, git state, branch protection, permissions, and verification are
safe. Use PR-mode when the issue, branch policy, review state, or user request
requires review before merge.

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
```

- [ ] **Step 3: Update the repo-specific Codex wrapper**

Replace `.codex/agents/github-issue-lifecycle.toml` with exactly:

```toml
name = "github-issue-lifecycle"
description = "GitHub™ issue lifecycle operator for explicit repo-internal issue handling."
sandbox_mode = "workspace-write"

developer_instructions = """
You are a GitHub issue lifecycle operator for this repository. Use the repo-internal `.claude/skills/github-issue-lifecycle/SKILL.md` overlay as the source of truth.

When invoked:
1. Read `.claude/skills/github-issue-lifecycle/SKILL.md`.
2. Follow its source-of-truth stack: public `issue-ops`, the GitHub extension, then this repository's overlay.
3. Proceed only for explicit GitHub issue lifecycle requests; do not hijack incidental issue mentions, ordinary PR review, standalone CI debugging, or general GitHub questions.
4. Default to full-cycle handling unless the user explicitly narrows the mode.
5. Resolve live GitHub and git state before acting.
6. Follow the overlay's repo-specific gates for `ip-hygiene`, skill architecture validation, isolated `.worktrees/` worktrees, direct-main handling, lifecycle state, and cleanup.
7. Preserve the public issue-ops completion output and include repo-local verification gates used.
"""
```

- [ ] **Step 4: Validate overlay references**

Run:

```bash
rg -n 'souroldgeezer-ops/skills/issue-ops/SKILL.md|extensions/github.md|ip-hygiene|skill-architecture-report' .claude/skills/github-issue-lifecycle/SKILL.md .codex/agents/github-issue-lifecycle.toml
```

Expected: output includes the public core path, GitHub extension path, `ip-hygiene`, and `skill-architecture-report`.

- [ ] **Step 5: Commit repo overlay**

Run:

```bash
git add .claude/skills/github-issue-lifecycle/SKILL.md .codex/agents/github-issue-lifecycle.toml
git commit -m "refactor: make github issue lifecycle a repo overlay"
```

Expected: commit succeeds.

## Task 5: Update README, CLAUDE, And AGENTS Guidance

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update README intro and install examples**

Modify `README.md` so the intro says the marketplace ships three plugins and includes this bullet after `souroldgeezer-design`:

```markdown
- **souroldgeezer-ops** — operations workflows for issue and work-item
  lifecycle handling, with a tracker-agnostic `issue-ops` core and a GitHub™
  provider extension for GitHub issue state, lifecycle comments, PR-mode,
  direct-main mode, and closure mechanics.
```

In Claude Code install commands, add:

```text
/plugin install souroldgeezer-ops@souroldgeezer
```

In the local development `enabledPlugins` example, add:

```json
"souroldgeezer-ops@souroldgeezer": true
```

Ensure the JSON comma placement remains valid.

- [ ] **Step 2: Add README section for `souroldgeezer-ops`**

Add this section after the `souroldgeezer-design` section and before "How the audits work":

```markdown
## What's in `souroldgeezer-ops`

One operations skill with a matching one-shot Claude Code subagent:

| Skill | Operates | Provider extensions |
|---|---|---|
| [issue-ops](souroldgeezer-ops/skills/issue-ops/SKILL.md) | Explicit issue and work-item lifecycle requests — triage, plan, implement, resume, close, queue processing, lifecycle state, escalation, verification, and completion reporting | [github](souroldgeezer-ops/skills/issue-ops/extensions/github.md) for GitHub™ issue state, lifecycle comments, labels/projects/milestones context, GitHub MCP / `gh` / REST routing, PR-mode, direct-main mode, linked PRs, and issue closure |

The core skill is tracker-agnostic. Provider mechanics live in extensions and
load only after the tracker is identified.

Matching Claude Code subagent: [souroldgeezer-ops/agents/issue-ops.md](souroldgeezer-ops/agents/issue-ops.md).
Codex installs the bundled skill through the plugin manifest, reads per-skill
metadata from [souroldgeezer-ops/skills/issue-ops/agents/openai.yaml](souroldgeezer-ops/skills/issue-ops/agents/openai.yaml),
and has a matching project-scoped wrapper in [.codex/agents/issue-ops.toml](.codex/agents/issue-ops.toml).
```

- [ ] **Step 3: Update README repository layout**

In the repository layout block, add this plugin block after `souroldgeezer-design/`:

```text
souroldgeezer-ops/                  # operations plugin
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/*.md                       # Claude Code subagents (one per skill, same name)
  skills/<name>/
    SKILL.md                        # tracker-agnostic workflow
    agents/openai.yaml              # Codex per-skill UI metadata / invocation policy
    extensions/                     # provider-specific mechanics
```

- [ ] **Step 4: Update CLAUDE repo description and internal skill note**

In `CLAUDE.md`, update "What this repo is" so it still describes a marketplace with one or more plugin subdirectories and now acknowledges `souroldgeezer-ops` as a published plugin. Keep the existing runtime documentation cross-check rules unchanged.

Replace the `github-issue-lifecycle` internal skill bullet with:

```markdown
- **`github-issue-lifecycle`** at [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md) — repo-local overlay for explicit GitHub™ issue lifecycle requests in this repository. It composes the public `issue-ops` skill from `souroldgeezer-ops`, the GitHub provider extension, and this repository's defaults for `ip-hygiene`, `.worktrees/**`, direct-main handling, skill-architecture verification, published-surface synchronization, lifecycle status, and cleanup. Codex has a thin project-scoped wrapper at [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml) that points back to this overlay.
```

- [ ] **Step 5: Update CLAUDE directory layout and skill-specific notes**

In the `CLAUDE.md` directory layout block, add this plugin block after `souroldgeezer-design`:

```text
souroldgeezer-ops/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  agents/<skill-name>.md
  skills/<skill-name>/SKILL.md
                     /agents/openai.yaml
                     /extensions/      ← provider-specific mechanics
```

Add this skill-specific note before the `devsecops-audit` note:

```markdown
- **`issue-ops`** (plugin `souroldgeezer-ops`) exposes lifecycle modes **full-cycle**, **triage-only**, **plan-only**, **implement-only**, and **resume** for explicit issue or work-item operations. The core is tracker-agnostic: it owns mode selection, queue limits, live-state authority, local recovery ledger, ask-vs-continue rules, escalation gates, verification inference, integration handoff, and completion output. Provider mechanics live in extensions. The first extension is `extensions/github.md`, covering GitHub™ issue state, lifecycle marker comments, labels/projects/milestones context, GitHub MCP / `gh` / REST routing, PR-mode, direct-main mode, linked pull requests, and issue closure. The repo-internal `.claude/skills/github-issue-lifecycle` skill is an overlay on this public skill, not a separate published workflow.
```

- [ ] **Step 6: Update AGENTS quick rule**

Replace the GitHub issue lifecycle quick rule in `AGENTS.md` with:

```markdown
- When the user explicitly asks to handle, triage, resume, implement, close, or
  process GitHub™ issues end to end in this repository, use the repo-internal
  [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md)
  overlay. It composes the public `issue-ops` skill, the GitHub provider
  extension, and this repo's extra gates. Codex can invoke the thin
  [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml)
  wrapper for that overlay.
```

- [ ] **Step 7: Validate documentation references**

Run:

```bash
rg -n 'souroldgeezer-ops|issue-ops|github-issue-lifecycle' README.md CLAUDE.md AGENTS.md
```

Expected: all three files mention `souroldgeezer-ops` or `issue-ops`, and the repo-internal overlay still mentions `github-issue-lifecycle`.

- [ ] **Step 8: Commit docs and guidance**

Run:

```bash
git add README.md CLAUDE.md AGENTS.md
git commit -m "docs: document issue ops plugin"
```

Expected: commit succeeds.

## Task 6: Run Final Validation And Commit Any Fixes

**Files:**
- Modify only files with validation-driven fixes from earlier tasks.

- [ ] **Step 1: Run structural JSON validation**

Run:

```bash
jq empty .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json
```

Expected: no output and exit 0.

- [ ] **Step 2: Run YAML and TOML inspection**

Run:

```bash
yq '.interface.display_name, .policy.allow_implicit_invocation' souroldgeezer-ops/skills/issue-ops/agents/openai.yaml
yq '.name, .description' .codex/agents/issue-ops.toml
yq '.name, .description' .codex/agents/github-issue-lifecycle.toml
```

Expected: command exits 0 and prints the expected metadata values.

- [ ] **Step 3: Run unit tests**

Run:

```bash
env UV_CACHE_DIR=/tmp/codex-uv-cache uv run python -m unittest tests.skill_architecture_report_test
```

Expected: `Ran 12 tests` and `OK`.

- [ ] **Step 4: Run strict skill architecture report**

Run:

```bash
env UV_CACHE_DIR=/tmp/codex-uv-cache uv run python scripts/skill_architecture_report.py --format json --strict .
```

Expected: JSON summary reports `"finding_count": 0` and exits 0.

- [ ] **Step 5: Run Markdown skill architecture report**

Run:

```bash
env UV_CACHE_DIR=/tmp/codex-uv-cache bash scripts/skill-architecture-report.sh .
```

Expected: report summary says `Findings: 0 total`.

- [ ] **Step 6: Run whitespace validation**

Run:

```bash
git diff --check
```

Expected: no output and exit 0.

- [ ] **Step 7: Fix validation findings in focused commits**

If a command in Steps 1-6 fails, make the narrowest fix to the named file and rerun the failed command plus `git diff --check`. Commit each coherent fix:

```bash
git add .claude-plugin/marketplace.json .codex/agents/issue-ops.toml .codex/agents/github-issue-lifecycle.toml .claude/skills/github-issue-lifecycle/SKILL.md README.md CLAUDE.md AGENTS.md souroldgeezer-ops
git commit -m "fix: align issue ops validation"
```

Expected: all validation commands pass after the fix commit.

- [ ] **Step 8: Review final branch state**

Run:

```bash
git status --short --branch
git log --oneline --max-count=8
```

Expected: clean branch with the design commit plus implementation commits.

## Self-Review Checklist

- [ ] The new plugin is listed in `.claude-plugin/marketplace.json` and has both plugin manifests.
- [ ] Manifest `name`, `version`, and `description` are synchronized across Claude, Codex, and marketplace surfaces.
- [ ] `issue-ops` core does not include GitHub-specific mechanics beyond extension selection.
- [ ] `extensions/github.md` owns GitHub state, tooling, lifecycle comments, integration strategies, and closure mechanics.
- [ ] The internal `github-issue-lifecycle` skill is a repo overlay, not a second public workflow.
- [ ] README, CLAUDE, and AGENTS reflect the new plugin and overlay relationship.
- [ ] Codex `interface.defaultPrompt` has three entries.
- [ ] Final validation commands all pass.
