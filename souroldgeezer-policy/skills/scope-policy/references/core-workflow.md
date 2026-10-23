# Scope Policy Core Workflow

Standing scope-boundary discipline for repositories that initialize this
policy, and the on-demand "keep this scoped" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before a change is made.

## Invariant

A change uses its declared scope level as the working footprint. A necessary
bounded extension uses the declared escalation mode, with its reason visible;
explicit exclusions and immutable managed boundaries remain authoritative.

## Enforcement

Select `enforce-initialized` for initialized guidance, or an explicit request;
otherwise `lookup`. `inspect` reports the level and escalation mode in force
without judging a specific diff. `adopt-guidance` writes the standing block —
MUST embed the invariant and a level, so the line never leans on the default.
`preflight`
diffs the working change against the declared level's footprint and lists the
hunks that fall outside it, before they land.

Applying a level to a change: identify the footprint the level permits (see
Levels), then classify each planned edit as inside or outside it. Inside edits
proceed. For a necessary adjacent edit, apply Escalation before proceeding.
Record unrelated wider findings with their reason; route to `issue-ops` only
when issue handling is requested or otherwise authorized.

## Levels

- **`targeted`** — the minimum edit that satisfies the task, inside the named
  target files/symbols. Out: opportunistic refactor, restructure, new
  abstraction, drive-by rename or reformat, dependency add/upgrade, unrelated
  test churn, adjacent bug fixes.
- **`balanced`** — `targeted`, plus refactoring confined to the code the
  change already enters (the touched functions/files): local extraction,
  renaming within that footprint, removing duplication the change would
  otherwise extend, tightening the pattern being extended, tests for the
  touched behaviour. Out: anything rippling beyond the footprint — signature
  changes with external callers, cross-cutting sweeps, module boundary moves,
  dependency swaps, new architecture.
- **`open`** — the agent derives the footprint from the goal. Delegated
  boundary, mandatory disclosure: it declares the chosen footprint and why
  before exceeding `balanced`, and discloses material changes with the result. Not "anything
  goes" — the request's own exclusions still bind.

## Escalation

Use the smallest justified extension when the current footprint prevents the
authorized outcome or would create a material correctness, maintainability, or
verification problem. Explain the concrete need and the bounded footprint at
N+1; do not perform a doomed attempt just to prove the current level impossible.
Preference for elegance or unrelated cleanup alone does not justify escalation.

- `escalation: stop` (explicit constraint) — stop, report the evidence, wait. Nothing
  widens.
- `escalation: auto` — move to N+1 only (never skip a rung), announce the rung
  change with its evidence, continue within existing authority. Record the
  material rung change once with the result.
- `open` is terminal: at level 3 an insurmountable problem is not a scope
  problem — stop as task-exceeds-request.

Escalation is per-task, monotonic within it, and never inherited by the next
task.

Under a standard `planning-policy` plan, the parent may apply `auto` to necessary
adjacent work and update the assignment without another approval turn when the
authorized outcome, material decisions, constraints, and acceptance stay intact.
A worker reports the need to the parent when its assigned boundary requires it;
it does not silently widen an explicit write restriction. Explicit `stop`,
plan-first constraints, new material risk, or changed authority still require
approval. A standard assignment is not an immutable managed leaf.

Under a strict or existing immutable managed plan, a leaf that cannot proceed within its
level returns bounded `oversized` evidence naming the blocking constraint and
the smallest wider footprint that resolves it. This is terminal for the
approved leaf. The parent preserves the original run and its evidence, then
prepares a replacement plan with the revised scope and obtains approval before
dispatching that work. The configured `auto` mode never edits or redispatches
an approved leaf in place; a leaf never widens its own boundary. Level is
orthogonal to that plan's portable tier — level bounds footprint, tier bounds
reasoning depth; neither substitutes for the other.

## Adoption and output

`adopt-guidance` follows the posture core's standing-line rule — the
invariant and a level inline, never a bare pointer. Template:

> `scope-policy: <targeted|balanced|open> — change only within that level's
> footprint; record unrelated wider findings. Escalate one justified rung
> for the authorized outcome; escalation <stop|auto>. Scope
> <globs>. Exceptions <globs>. Opt out per task by saying "<phrase>" (logged).`

Default profile: bare initialization is level `balanced`, escalation `auto`.
It covers a hand-written bare line; an ambiguous or contradictory level (two
named levels, or a level outside the three) is `blocked:missing_input`, never
a silent pick.

Opt-out ladder mirrors the posture core: disable the line, a single logged
per-task phrase, or scope/exception globs — every path stays one line or one
phrase.

## Output

Report the result and any material footprint extension, its reason, explicit
constraint, or wider finding. Combine this with the task's normal check summary;
routine compliance requires no standalone policy footer or empty fields.
