# Planning Policy Core Workflow

Standing plan-first discipline for repositories or users that initialize this
policy, and the on-demand "plan this first" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before new feature or build
work.

## Invariant

New feature or build work is preceded by a brief brainstorm in plan mode that
converges on an approach the user approves (through `ExitPlanMode`) before any
implementation begins. Shipped work traces back to an approach the user agreed
to, not one assumed mid-edit.

## Enforcement cycle

1. **Enter plan mode.** If the session is not already in plan mode, call
   `EnterPlanMode` before asking anything. If already in plan mode, skip.
2. **Orient briefly.** Skim only what is needed to ask good questions — named
   files, recent commits, obvious structure. Do not deep-dive or start a review.
3. **Clarify in single, focused questions.** Surface the goal, its constraints,
   and what a good result looks like. Prefer one question per message;
   multiple-choice when it helps. Stop asking once the approach is clear — do not
   pad.
4. **Converge.** State the approach in one or two sentences, sized to how
   involved the work is. When real alternatives exist, name the tradeoff and your
   pick in one line — do not force a menu.
5. **Present with `ExitPlanMode`.** Put the agreed approach into the plan and call
   `ExitPlanMode` for approval. Native plan mode owns the plan: write no spec
   file, commit nothing, and do not hand to a separate planning skill.

Implementation is a fresh action the user drives after approval. Hand domain
design and coding to the sibling skill that owns it (see Delegation).

Non-interactive surfaces (a one-shot subagent, a headless run) cannot take the
user through plan-mode approval. There, produce the proposed approach and the
open questions that remain, state that plan mode was not entered, and recommend
running the cycle interactively.

## Standing block template

`adopt-guidance` and the default init block follow the posture core's
standing-line rule — the invariant inline, never a bare pointer. Template:

> `planning-policy: <profile> — before new feature or build work, brainstorm the
> approach in plan mode and get it approved (ExitPlanMode) before implementing.
> Scope <task-types/globs>. Opt out per task by saying "skip planning" (logged).
> Enforcement <model>.`

## Default profile

Bare `planning-policy` (no options) resolves to: scope = new feature, build, or
creative work; exceptions = trivial edits, hotfixes, spikes/throwaway, and work a
domain skill owns end to end (logged); enforcement `model`.

## Config options

- `scope` — task types or globs the policy governs (default: new feature/build work).
- `exceptions` — categories exempt from the plan-first gate, always logged.
- `enforcement` — `model` (behavioral default). A PreToolUse backstop that blocks
  implementation edits until an approved plan exists is a possible phase-2 and is
  deferred; do not claim it is active.

## Opt-out ladder

- **Disable:** negate/remove the init line, or `planning-policy: off`.
- **Per-task:** a single phrase ("skip planning" / "just do it") → applied and
  logged in the footer, never silent.
- **Per-scope:** `exceptions` / `scope` globs.

## Delegation

planning-policy is the front-door thinking step; it does not do domain design or
write code. After the plan is approved, hand off:

- code/module boundaries → `software-design`
- frontend app → `app-design`; HTTP API → `api-design`; IaC → `infra-design`
- ArchiMate®/UML® model → `architecture-design`
- security posture → `devsecops-audit`; test quality → `test-quality-audit`
- test-first ordering while implementing → `tdd-policy` (they compose: plan
  first, then test-first)
- commit/branch preflight → `git-workflow-policy`; PR/MR → `pr-ops`; issues →
  `issue-ops`

## Output footer

End the enforcing turn (the message before `ExitPlanMode`, or the summary on a
non-interactive run) with:

```
Planning policy: <enforced-initialized | on-demand | opt-out applied | not initialized>
Source: <initialization line | explicit request>
Scope/exceptions: <in force>
Plan mode: <entered | already active | not available (reason)>
Opt-outs: <none | phrase logged>
```
