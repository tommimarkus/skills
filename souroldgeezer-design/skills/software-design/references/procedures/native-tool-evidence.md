# Native Tool Evidence

Native Tool Evidence shows repeatable evidence from tools this project already uses. It does not require the project to adopt or configure a tool.

Load for configured evidence, `detected-not-run`, or a suggestion for a
demonstrated evidence gap.

## Evidence protocol

1. Detect through manifests, configuration, documented scripts, and CI; use the
   project's invocation and settings. An installed tool alone is
   `detected-not-run`; never invent configuration.
2. Render `## Native Tool Evidence` only when there is configured evidence,
   `detected-not-run`, or an actually offered suggestion. Tool findings remain
   candidates; missing optional tooling never blocks and never makes the design
   concern `not-assessed`.
3. If no relevant tool is configured, offer at most one concise optional
   suggestion for a demonstrated evidence gap; it is never a prerequisite.
   Equivalent tools share one capability key.
4. Do not render the section when none of those cases applies. Do not repeat an
   active quiet decision.

## Clone-local quiet decisions

Persist only an explicit `no`, `not now`, or `defer`. At that moment say:

> I’ll remember only this optional tool suggestion in this clone until `<date>` so it is not repeatedly offered. Fragility findings remain active.

Set `<date>` to 30 UTC calendar days after the explicit decision. Before
executing, replace the literal `<date>` in `defer-until:<date>`. The record is
active before its stored UTC date. The suggestion is eligible again on its
stored UTC date. Reading never slides the deadline. Renew it only after a new
explicit `no`, `not now`, or `defer`.

Use clone-local Git configuration, shared across linked worktrees, never
worktree configuration; see the [configuration manual](https://git-scm.com/docs/git-config/2.51.2.html)
and [worktree manual](https://git-scm.com/docs/git-worktree.html).

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

List and clear decisions exactly with:

```sh
git config --local --get-regexp '^softwaredesign\.tool-decision-'
git config --local --unset-all softwaredesign.tool-decision-typescript-unchecked-index-evidence
```

Reserve only `softwaredesign.tool-decision-*`. Never use global or worktree
configuration, raw `.git` writes, helpers, hooks, plugin data, tracked
preferences, shell variables, or substitutions. If a local write is denied or
would need escalation, do not escalate or retry merely to save the preference:
keep it conversation-local and disclose that once, with no fallback persistence.
