# Planning Policy Core Workflow

Standing plan-first discipline for repositories or users that initialize this
policy, and the on-demand "plan this first" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before new feature or build
work.

## Invariant

New feature or build work is preceded by a brief brainstorm in the runtime's
plan-first lane that converges on an approach the user approves before any
implementation begins. Shipped work traces back to an approach the user agreed
to, not one assumed mid-edit.

## Enforcement cycle

1. **Select the runtime lane.**
   - **Claude Code lane:** If the session is not already in plan mode, call
     `EnterPlanMode` before asking anything. If already in plan mode, skip.
   - **Codex lane:** If Codex Plan mode is active or the surface exposes a native
     plan-mode control, use it before asking anything. Otherwise stay read-only
     and use the explicit-approval fallback in step 5; never claim the mode changed.
2. **Orient briefly.** Skim only what is needed to ask good questions — named
   files, recent commits, obvious structure. Do not deep-dive or start a review.
3. **Clarify in single, focused questions.** Surface the goal, its constraints,
   and what a good result looks like. Prefer one question per message;
   multiple-choice when it helps. Stop asking once the approach is clear — do not
   pad.
4. **Converge.** State the approach in one or two sentences, sized to how
   involved the work is. When real alternatives exist, name the tradeoff and your
   pick in one line — do not force a menu. State the execution shape with it:
   which steps go to subagents and what the parent keeps (see Execution shape).
5. **Present for approval.** In the Claude Code lane, put the agreed approach into
   the plan and call `ExitPlanMode` for approval. In the Codex lane, use the
   native plan approval control when exposed; otherwise present the proposed
   plan, ask for explicit approval, and end the turn. The active lane owns the
   plan: write no spec file, commit nothing, and do not hand to a separate
   planning skill.

Implementation is a fresh action the user drives after approval. Hand domain
design and coding to the sibling skill that owns it (see Delegation).

Non-interactive surfaces (a one-shot subagent, a headless run) cannot take the
user through plan-mode approval. There, produce the proposed approach — execution
shape included — and the open questions that remain. The proposal names the
delegation it recommends; it does not spawn it. For Claude Code, state that plan
mode was not entered; for Codex, state that approval was not obtained. Recommend
running the cycle interactively.

## Execution shape

The approved approach names how the work will be run, not only what will be
built. Default: decomposable implementation steps are delegated to subagents,
and independent steps are dispatched together so they run concurrently.

Delegate by default. Depart only on a case you can state in one line in the
plan, naming which:

- **Indivisible or trivial** — one step, or the handoff costs more than the work.
- **Needs the user mid-flight** — the step turns on a question a subagent cannot
  ask.
- **Context does not travel** — the step depends on in-flight findings that cost
  more to write down than to keep acting on.
- **Each step redefines the next** — exploratory work where the parent must
  re-decide after every result.

"Easier to just do it" is not one of these, and neither is the parent's own
familiarity with the code. Overlapping file writes are a sequencing or isolation
problem to solve in the plan, not a reason to keep the work inline.

The parent session keeps decomposition, integration, and the verification the
plan commits to. A subagent reporting "verified" has verified its own drafting,
not the integrated result — never let that stand in for the parent's check.

### What a delegated step carries

A subagent starts with no conversation history, so the plan states, per delegated
step:

- **Task and boundary** — what to do, and what to leave alone.
- **Inputs** — paths, commands, and prior decisions it cannot infer.
- **Acceptance** — how it knows it is done, and what it must not claim.
- **Return** — the shape the parent needs back in order to integrate.

Under-specified handoffs, not mis-tuned runtimes, are how delegation fails. So
name the agent type when a specialized one fits the step — its definition already
carries the model and tool set — and otherwise let the model and reasoning effort
inherit from the session rather than pinning them. Pin either only with a reason
stated in the plan. Where delegated steps write the same files concurrently, the
plan says so and isolates them.

- **Claude Code lane:** subagents through the `Agent` tool, one per decomposed
  step.
- **Codex lane:** the host's own delegation mechanism when exposed; otherwise
  keep the decomposition in the plan, run the steps in session, and say
  delegation was not available. Never claim a subagent ran.

## Standing block template

`adopt-guidance` and the default init block follow the posture core's
standing-line rule — the invariant inline, never a bare pointer. Template:

> `planning-policy: <profile> — before new feature or build work, brainstorm the
> approach in plan mode and get it approved (ExitPlanMode) before implementing.
> The approved plan says who runs each step: delegate decomposable steps to
> subagents unless the plan states why not, and keep integration and
> verification in the parent session. Scope <task-types/globs>. Opt out per task
> by saying "skip planning" (logged). Enforcement <model>.`

For Codex guidance (`AGENTS.md`), replace the parenthetical tool name with
"native Plan mode when available, otherwise explicit approval", and "subagents"
with "the host's delegation mechanism when available"; do not alter the Claude
Code template used in `CLAUDE.md`.

## Default profile

Bare `planning-policy` (no options) resolves to: scope = new feature, build, or
creative work; exceptions = trivial edits, hotfixes, spikes/throwaway, and work a
domain skill owns end to end (logged); delegation = `subagents-by-default`;
enforcement `model`.

## Config options

- `scope` — task types or globs the policy governs (default: new feature/build work).
- `exceptions` — categories exempt from the plan-first gate, always logged.
- `delegation` — `subagents-by-default` (default) or `inline`. `inline` drops the
  standing preference for consumers whose runtime or workflow cannot use
  subagents; a per-plan departure under the default still needs its one-line case.
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

End the enforcing turn (the message before `ExitPlanMode` or Codex native
approval, the explicit Codex fallback request, or the summary on a
non-interactive run) with:

```
Planning policy: <enforced-initialized | on-demand | opt-out applied | not initialized>
Source: <initialization line | explicit request>
Scope/exceptions: <in force>
Plan mode: <entered | already active | fallback used (reason) | not available (reason)>
Execution shape: <subagents: steps delegated | inline (case) | delegation unavailable (reason)>
Opt-outs: <none | phrase logged>
```
