# Planning Policy Core Workflow

The standing line, once initialized, is authority before new feature/build
work. Its invariant is a brief host-plan-lane brainstorm, an agreed approach,
and user approval before implementation.

## Enforcement

1. Select the lane: the **Claude Code lane** calls `EnterPlanMode` unless already
   there; the **Codex lane** uses native Plan mode when exposed, otherwise stays
   read-only for explicit approval. Never claim a mode change.
2. Orient only enough to ask good questions. Ask focused questions about goal,
   constraints, and success; stop when an approach is clear.
3. State the approach in one or two sentences and name a real tradeoff/pick.
   State execution shape: decomposable implementation steps delegate by default;
   the parent retains decomposition, integration, and final verification.
   Before approval, invoke the owning design skill if an unresolved domain-design
   choice materially affects implementation; bring its settled choice back here.
4. Groom after convergence. Name each step’s reads/writes and settled decisions;
   split multiple concerns/checks, merge identical boundaries/checks. A fresh
   agent must finish from the handoff. Load [plan contract](plan-contract.md),
   validate it using its Claude `${CLAUDE_SKILL_DIR}` or Codex absolute
   `<skill-dir>` form, and re-cut any missing boundary, decision, or failed
   command. Every leaf includes `missing_load_bearing_information`.

Delegate unless the plan records one case: indivisible/trivial, needs user
mid-flight, context cannot travel, or each result redefines the next. Overlap
is a sequencing/isolation issue, not an inline exception. Select an owning
audit only for one bounded initial-inspection question whose evidence cannot be
resolved by targeted inspection/tests and can change approach or acceptance;
otherwise use the owning design skill.

Portable tier is selected once per leaf: `mechanical`, `standard`,
`analytical`, or `deep`; no per-leaf runtime tuning. Analytical/deep names its
irreducible risk. Stable work units are weighted once (`small=1`, `medium=2`,
`large=3`); medium-ready units contain only mechanical/standard leaves and
need ratio `>=0.60`, unless the recorded user-approved analytical-heavy
exception applies. The adapter maps tiers or returns its blocker.

## Approval and output

Present the groomed plan and stop: Claude uses `ExitPlanMode`; Codex uses native
approval or asks explicitly and ends the turn. Non-interactive surfaces only
return a proposal/open questions and say approval was not obtained. No spec,
commit, implementation, or delegation happens before approval.

For two or more delegated steps, only the parent creates
`<git-common-dir>/planning-policy/ledgers/<plan-id>/`. Keep bounded checkpoints,
evidence paths, and returns, never raw logs. Successful leaves close
`completed` → `integrated` → `cleaned`; only then create dependent worktrees
from the current parent tip. Use the ledger's Git-policy helper, not a routine
cherry-pick, then validate `--closeout`.

Use this standing template for adoption (Codex substitutes its available native
approval/delegation wording):

> `planning-policy: <profile> — before new feature or build work, brainstorm the
> approach in plan mode and get it approved before implementing. The approved
> plan says who runs each step; delegate decomposable work unless it states why
> not, and keep integration and verification in the parent. Scope <globs>. Opt
> out per task by saying "skip planning" (logged). Enforcement <model>.`

Bare initialization governs new feature/build/creative work; trivial edits,
hotfixes, spikes, and end-to-end domain-owned work are logged exceptions.
`delegation` is `subagents-by-default` or `inline`; `enforcement` is behavioral
`model`, not a claimed mechanical backstop. Opt out by removing/off, a logged
per-task phrase, or scope/exception globs.

Footer:

```text
Planning policy: <enforced-initialized | on-demand | opt-out applied | not initialized>
Source: <initialization line | explicit request>
Scope/exceptions: <in force>
Plan mode: <entered | already active | fallback used (reason) | not available (reason)>
Execution shape: <subagents: N steps (bands) | inline (case) | delegation unavailable (reason)>
Opt-outs: <none | phrase logged>
```
