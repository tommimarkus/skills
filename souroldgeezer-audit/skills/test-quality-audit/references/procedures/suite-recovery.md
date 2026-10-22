# Suite recovery program

**When this runs:** after the prioritized remediation worklist of
[deep-mode-output-format.md](deep-mode-output-format.md), under the Deep-only
load condition stated in the Load Map of [../../SKILL.md](../../SKILL.md). When
all five Suite health dispositions are `supported-positive`, emit no program.

## Stance

Propose-only. The audit edits, deletes, quarantines, or reschedules nothing,
and runs nothing beyond the Deep evidence ladder's already-authorized runs. The
program is an output section that orders the work and states what evidence
closes each item; executing it is ordinary work, under `tdd-policy`'s in-cycle
rules when that policy is initialized in the target repository. This is the
read-only principle of
[../../../../docs/audit-reference/audit-craft.md](../../../../docs/audit-reference/audit-craft.md)
§2, in the same shape as lean-audit's propose-only minify lens.

## Inputs

Reuse the Deep evidence already in hand; never re-derive it here:

- the Suite health lane table, runtime distribution, and lifecycle table from
  [deep-mode-output-format.md](deep-mode-output-format.md);
- per-test durations, slow cases, and timing coverage from the JUnit snapshot
  helper when a report was available;
- the SUT risk-tier map from
  [../../../../docs/audit-reference/materiality.md](../../../../docs/audit-reference/materiality.md);
- any `structure-coupled` records found in accessible history, weighed as
  [deep-mode-output-format.md](deep-mode-output-format.md) states;
- the portfolio candidates with their dispositions and the `SH-*` codes they
  cite from [../smell-catalog.md](../smell-catalog.md).

## Program steps

Emit the steps in this fixed order. Every item carries the action or
disposition, an evidence gate (what must be shown before the item counts as
done), an acceptance command (the project's own configured command, never an
invented one), expected impact in seconds or share of lane time (`unknown`
when timing coverage is partial), effort, and owner when one is known.

### 1. Baseline

Record each lane's total, p50, p95, slow-tail share, and timing coverage from
the snapshot. When timing is partial or absent, say so under program limits:
item ordering then falls back to static level classification, and the program
names the configured runner's own report flag as the project command that
would supply timing on the next run. Never a request for new instrumentation.

### 2. Lane split first

Classify every test by level (in-process unit, in-process integration, child
process or CLI, end-to-end) and by resource use (network, filesystem,
subprocess, sleeps, browsers). Propose lane commands and cadences: a
pre-commit fast lane, a pre-merge lane, and a nightly or scheduled lane for
the rest. This restores the development loop before any test is touched; it is
the `SH-LC-5` → `SH-POS-5` move, and it comes first because it needs no
per-test judgment.

### 3. Ratchet budget

Propose a per-lane budget equal to the measured baseline, a target, and a
step. The project encodes the value as its declared budget: `tdd-policy`
`feedback-budget` when that policy is initialized, otherwise runner or CI
configuration or repository guidance. While a lane is above target, a breach
means slower than the last recorded run; once at target, the target is the
budget. This is what makes `SH-HC-1` measurable afterwards and lets the
prospective policy hold the line. The audit proposes the value, the project
declares it.

### 4. Slow tail first

Rank candidates by time share × cross-layer overlap × SUT risk tier and emit
items in the existing disposition vocabulary, each with its gate:

- `move down` — gate: the lower-level test fails for the same regression the
  higher-level test caught, shown by failure attribution or a deliberate
  break, before the higher-level test is demoted or retired.
- `consolidate` — gate: the lifecycle invariant holds — amortize only
  immutable or safely resettable infrastructure, never from matching setup
  text, with mutable data staying per-test.
- `schedule later` — gate: a lane move with a stated cadence, owner, exit
  criterion for returning to the fast lane, and a full-run safety net.
- `verify-then-retire` — gate: distinct-contract review plus controlled
  removal, mutation, or failure attribution evidence; similarity alone never
  closes this item.
- `strengthen` — gate: the weak assertion or scope named in the per-test
  finding is closed and the test still fails for the contract it claims.
- `keep` — recorded with its reason so the next Deep run does not re-judge it.

### 5. Runner levers

After the items above: parallelization or sharding, validated selective
execution with a full-suite safety net (`SH-HC-3` → `SH-POS-3`), and
fail-fast for the pre-commit lane. Each lever is runner work with its own
evidence gate (a timed run before and after), never a substitute for the
items in step 4.

### 6. Cadence and exit

Batch items by area or owner. After each batch, re-measure with the snapshot
helper on the new report, ratchet the budget to the new measured value, and
re-rank the remaining tail. Stop when every lane meets its target. State when
to re-run Deep: after the last batch, or when a lane breaches its ratchet
twice.

## Output block

Append after the worklist:

```markdown
## Suite recovery program

### Baseline

| Lane | Tests | Total | p50 | p95 | Slow-tail share | Timing coverage |
|---|---:|---:|---:|---:|---:|---|

### Lane proposal

| Lane | Selection | Command | Cadence | Expected total |
|---|---|---|---|---:|

### Ratchet

| Lane | Baseline | Target | Step | Encoded as |
|---|---:|---:|---:|---|

### Ordered items

1. <disposition> `<test or group>` — gate: <evidence>; accept: `<project command>`;
   impact: <seconds / share / unknown>; effort: <S / M / L>; owner: <name or unknown>

### Program limits

- <timing coverage, unknowns, static-only ordering, evidence not available>

Propose-only: this program edits, deletes, quarantines, or reschedules nothing;
the project executes it as ordinary work.
```

## Forbidden

- Deleting or retiring from similarity, count, test-to-code ratio, or
  “never failed” history; those support `verify-then-retire` only.
- Demanding instrumentation; missing timing is a program limit plus a named
  runner flag.
- Emitting a program for a healthy suite, or padding one with items the
  evidence does not rank.
- Treating test count or a pyramid shape as a target; the targets are the
  per-lane budgets.
- Editing, deleting, quarantining, or rescheduling tests, or running anything
  beyond the authorized Deep evidence ladder.
