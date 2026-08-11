# Scope Policy Core Workflow

Standing scope-boundary discipline for repositories that initialize this
policy, and the on-demand "keep this scoped" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before a change is made.

## Invariant

A change stays inside a declared scope level; work that cannot be done at that
level escalates one rung under a declared escalation mode, never silently
widens.

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
proceed. Outside edits are recorded, not made — capture what the edit would
have been and why it falls outside the level, and route it to `issue-ops` as a
follow-up item rather than doing it inline.

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
  before exceeding `balanced`, and discloses it in the footer. Not "anything
  goes" — the request's own exclusions still bind.

## Escalation

Trigger test: at level N the task cannot be completed correctly — not merely
more elegantly. Evidence required: what was attempted, the specific
constraint that blocks it, and the smallest footprint at N+1 that resolves it.

- `escalation: stop` (default) — stop, report the evidence, wait. Nothing
  widens.
- `escalation: auto` — move to N+1 only (never skip a rung), announce the rung
  change with its evidence, continue. Record the rung change in the footer.
- `open` is terminal: at level 3 an insurmountable problem is not a scope
  problem — stop as task-exceeds-request.

Escalation is per-task, monotonic within it, and never inherited by the next
task.

Under an approved `planning-policy` plan, a leaf that cannot proceed within its
level returns bounded `blocked` evidence naming the blocking constraint and the
smallest wider footprint that resolves it. The parent adjudicates: `stop` halts
and reports; `auto` re-cuts that leaf one rung wider and redispatches. A leaf
never widens its own boundary. Level is orthogonal to that plan's portable
tier — level bounds footprint, tier bounds reasoning depth; neither substitutes
for the other.

## Adoption and output

`adopt-guidance` follows the posture core's standing-line rule — the
invariant and a level inline, never a bare pointer. Template:

> `scope-policy: <targeted|balanced|open> — change only within that level's
> footprint; record wider findings instead of doing them. Escalate one rung
> only when the level is insurmountable; escalation <stop|auto>. Scope
> <globs>. Exceptions <globs>. Opt out per task by saying "<phrase>" (logged).`

Default profile: bare initialization is level `balanced`, escalation `stop`.
It covers a hand-written bare line; an ambiguous or contradictory level (two
named levels, or a level outside the three) is `blocked:missing_input`, never
a silent pick.

Opt-out ladder mirrors the posture core: disable the line, a single logged
per-task phrase, or scope/exception globs — every path stays one line or one
phrase.

## Output footer

End every run with:

```text
Scope policy: <enforced-initialized | on-demand | opt-out applied | not initialized>
Source: <initialization line | explicit request>
Level: <targeted | balanced | open> (<declared | defaulted | escalated from <level>>)
Escalation: <stop | auto> — <none | rung change + reason>
Recorded out-of-level: <none | N findings (routed)>
Opt-outs: <none | phrase logged>
```
