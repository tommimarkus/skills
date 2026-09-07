# Native Tool Evidence

Native Tool Evidence shows repeatable evidence from tools this project already uses. It does not require the project to adopt or configure a tool.

Load this procedure when a Build, Extract, or Review task has evidence from a
repository-configured native tool, detects a relevant tool without a
repository-owned invocation, or has a demonstrated evidence gap for which one
optional suggestion may be relevant.

## Evidence protocol

1. Detect repository-owned analyzers through manifests, configuration,
   documented scripts, and CI. Use only the project's invocation and settings.
   An installed tool without repository invocation is `detected-not-run`; never
   invent configuration.
2. Render `## Native Tool Evidence` only when there is configured evidence,
   `detected-not-run`, or an actually offered suggestion. Tool findings remain
   candidates, not facts by themselves; missing optional tooling never blocks
   and never makes the design concern `not-assessed`.
3. If no relevant tool is configured, offer at most one concise optional
   suggestion, and only for a demonstrated evidence gap. It is never a
   prerequisite. Equivalent tools share one capability key rather than creating
   multiple suggestions for the same gap.
4. Do not render the section when none of those cases applies. Do not repeat a
   suggestion while its active quiet decision applies.

## Clone-local quiet decisions

Persist only an explicit `no`, `not now`, or `defer`. At that moment say:

> I’ll remember only this optional tool suggestion in this clone until `<date>` so it is not repeatedly offered. Fragility findings remain active.

Before executing the write, replace the literal `<date>` in
`defer-until:<date>` with the UTC decision date plus 30 calendar days. The
record is active before that date. The suggestion is eligible again on its
stored UTC date. Reading never changes it; renewal requires a new explicit
decision and a newly rendered date.

Use Git's local configuration, which is clone-local and shared across linked
worktrees; do not use Git's worktree-specific configuration. Git documents the
local configuration scope in its [configuration manual](https://git-scm.com/docs/git-config/2.51.2.html)
and distinguishes it from per-worktree configuration in its
[worktree manual](https://git-scm.com/docs/git-worktree.html).

For the TypeScript unchecked-index evidence gap, the write template is:

```sh
git config --local softwaredesign.tool-decision-typescript-unchecked-index-evidence defer-until:<date>
```

For example, an explicit decision on 2026-08-09 renders the fixed command:

```sh
git config --local softwaredesign.tool-decision-typescript-unchecked-index-evidence defer-until:2026-09-08
```

Read that decision exactly with:

```sh
git config --local --get softwaredesign.tool-decision-typescript-unchecked-index-evidence
```

An active record means total silence: no suggestion and no suppression reminder.
Renew it only after a new explicit `no`, `not now`, or `defer`; do not slide a
stored deadline on read.

List and clear decisions exactly with:

```sh
git config --local --get-regexp '^softwaredesign\.tool-decision-'
git config --local --unset-all softwaredesign.tool-decision-typescript-unchecked-index-evidence
```

Reserve only the `softwaredesign.tool-decision-*` keys. Never use global or
worktree configuration, raw `.git` writes, helper scripts, hooks, plugin data,
tracked preferences, shell variables, or command substitutions. If the local
write is denied or would need escalation, do not escalate or retry merely to
save the preference: keep it conversation-local and disclose that once, with no
fallback persistence.
