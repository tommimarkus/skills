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
     and use the explicit-approval fallback in step 6; never claim the mode changed.
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
5. **Groom the steps.** A first decomposition is a draft, not the plan — a step
   can only be sized once the approach is settled, so grooming follows Converge.
   Test each step and re-cut what fails. The enumeration here is scoped by that
   settled approach, not a repo survey: step 2 skims only enough to ask good
   questions; this step lists only what the now-decided steps need to read and
   write.

   A step is ready when:
   - **Its read-set is named.** You can list the files it reads and writes. If
     the step's first act would be searching for them, that search is the
     parent's work: do it now, while already oriented, and hand the list. One
     enumeration in the parent replaces the same enumeration repeated in every
     subagent.
   - **It has one acceptance check.** Two independent checks means two steps.
     The check is the narrowest one that would actually fail if the step were
     wrong, not the whole suite.
   - **A fresh agent could finish it from the handoff alone.**

   Re-cut what fails: split a step that carries more than one concern or hides
   discovery inside execution; merge steps that share a read-set and an
   acceptance check.

   For an executable plan, load
   [plan-contract.md](plan-contract.md). It makes these readiness tests
   machine-checkable: every leaf has the complete handoff contract, a stable
   top-level work unit prevents artificial splitting, and the weighted
   medium-ready gate is calculated before approval. Use one of its documented
   Claude `${CLAUDE_SKILL_DIR}` or Codex absolute `<skill-dir>` commands. A
   missing settled decision, unknown read/write boundary, failed command, or
   other load-bearing gap is stop-and-return in every tier; every leaf carries
   the exact `missing_load_bearing_information` stop marker. Do not improvise.
6. **Present for approval.** In the Claude Code lane, put the agreed approach into
   the plan and call `ExitPlanMode` for approval. In the Codex lane, use the
   native plan approval control when exposed; otherwise present the proposed
   plan, ask for explicit approval, and end the turn. The active lane owns the
   plan: write no spec file, commit nothing, and do not hand to a separate
   planning skill.

Implementation is a fresh action the user drives after approval. Hand domain
design and coding to the sibling skill that owns it (see Delegation).

Non-interactive surfaces (a one-shot subagent, a headless run) cannot take the
user through plan-mode approval. There, produce the proposed approach —
execution shape included, its steps groomed and carrying the same size bands an
approved plan would — and the open questions that remain. The proposal names
the delegation it recommends; it does not spawn it. For Claude Code, state that
plan mode was not entered; for Codex, state that approval was not obtained.
Recommend running the cycle interactively.

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
- **Inputs** — the named read-set of files it reads and writes, plus the
  commands and prior decisions it cannot infer.
- **Acceptance** — how it knows it is done, and what it must not claim.
- **Return** — the shape the parent needs back in order to integrate.
- **Size** — one of three bands, derived from Inputs and Acceptance rather than
  estimated on its own, so it cannot drift from what those two already say:

| Band | The step… |
|---|---|
| `small` | touches a handful of named files under one narrow acceptance check, with no discovery |
| `medium` | spans a named read-set across a subsystem under one scoped acceptance check |
| `large` | must reason over a bounded read-set before it can edit |

`large` is the exception: name in the plan why the step cannot be cut smaller —
the same stated-case idiom the delegation departures above already use.
Unbounded discovery is never a legitimate `large`; that is an ungroomed step.

The band travels to the subagent, not only the plan, because it is what the
subagent checks reality against: a step told `small` that finds itself reading
forty files has a concrete mismatch to report back, and the parent re-cuts.
That pairing is what makes the band load-bearing rather than decorative.

Under-specified handoffs, not mis-tuned runtimes, are how delegation fails. Name
a specialized agent type when one fits the step, select its portable tier, and
let the matching host adapter map that tier to its supported execution settings.
Do not hand-tune model or reasoning effort per leaf outside that mapping. If the
adapter cannot map the selected tier or the host exposes no delegation
capability, stop and return the blocker to the parent. Where delegated steps
write the same files concurrently, the plan says so and isolates them.

Groom before selecting tiers: splitting usually confines the expensive tier to
the part that needs it — one large analytical step re-cuts into one small
analytical step plus several mechanical ones — which is a direct cost lever.

The portable leaf fields and the `mechanical`/`standard`/`analytical`/`deep`
judgment are shared across hosts; host overlays map them to host agent names.
Analytical and deep work names the irreducible unknown or risk. The plan groups
leaves by stable top-level work unit; each unit is weighted once from its
declared original size (`small=1`, `medium=2`, `large=3`) and is medium-ready
only when every leaf is mechanical or standard. Require weighted readiness of
at least 0.60, unless the user explicitly approves and the plan records an
analytical-heavy exception. This prevents gaming the threshold by splitting a
large concern into many small leaves.

### Selective audit routing

Initial inspection may route to exactly one owning audit only if the domain
matches, the audit could materially change the approach or acceptance command,
targeted inspection or focused tests cannot answer it, and the plan names both a
bounded question and its evidence surface. Otherwise send ordinary domain
design to the owning design skill. A vague request to “review risks” is not an
audit route.

This plugin ships an execution-tier roster so a plan names a tier instead of
tuning knobs per call — each definition already carries its model, effort, and
tool set:

| Tier | Use it when the step… |
|---|---|
| `plan-step-mechanical` | is already decided and only needs executing exactly |
| `plan-step-standard` | has a settled approach but needs ordinary implementation judgment (the default) |
| `plan-step-analytical` | holds a real unknown that must be resolved before editing |
| `plan-step-deep` | is one where a confident wrong answer is the failure mode |

Name the cheapest tier the step actually needs. Each tier stops and escalates
rather than improvising when the step turns out to sit above it, so guessing low
costs a handoff, while defaulting high costs on every step. Hosts and agent sets
differ: the tier judgment is the portable part, not these names. Sizing applies
under `delegation: inline` too: an oversized step blows the parent's own
context, a context problem rather than a delegation-only one.

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
Execution shape: <subagents: N steps (bands) | inline (case) | delegation unavailable (reason)>
Opt-outs: <none | phrase logged>
```
