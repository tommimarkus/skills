# TDD Policy Core Workflow

Standing test-first discipline for repositories that initialize this policy, and
the on-demand "enforce TDD now" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before implementation-code
changes.

## Invariant

New or changed observable behavior is preceded by a focused failing test that
specifies the intent, written at the cheapest level that proves it.
Behavior-preserving refactors run under existing passing tests, adding bounded
characterization coverage only where protection is missing; a failure is never
manufactured to satisfy TDD. Every retained test carries distinct regression
value at an appropriate execution cost. REFACTOR consolidates or retires
superseded coverage. Shipped behavior stays covered by at least one test that
would fail if it regressed.

## Standing block template

`adopt-guidance` and the default init block follow the posture core's
standing-line rule — the invariant inline, never a bare pointer. Template:

> `tdd-policy: <variant> — new or changed behavior gets a focused failing test first, at the
> cheapest level that proves it; refactors run under existing passing tests; RED→GREEN→REFACTOR,
> and REFACTOR retires or consolidates superseded coverage; shipped behavior stays covered by
> at least one test that fails on regression. Scope <globs>. Budget <lane: value|inherited|none>.
> Exceptions <list> (logged). Enforcement <model|model+gate>.`

## Default profile

Bare `tdd-policy` (no options) resolves to: variant `test-first`; scope =
production source (excludes tests, generated, migrations, config); exceptions =
spikes/prototypes/throwaway/generated (logged); `feedback-budget` none (observe
and report); enforcement `model`.

## Variants (both preserve the invariant)

- `test-first` (default): strict RED→GREEN→REFACTOR — write the failing test,
  watch it fail, implement minimally, refactor.
- `test-alongside`: test and implementation in one change, test written and
  failing first.

`test-after` + coverage floor **relaxes the invariant** and is therefore NOT a
variant — it is a logged opt-out downgrade (see Opt-out ladder), never offered
as a way to "do TDD."

## Behavioral change or refactor

Classify the change before choosing RED:

- **New or changed observable behavior** → RED is required; continue with
  "Selecting the RED test".
- **Behavior-preserving refactor** → existing passing tests are the safety net.
  Where the code about to change has no protection, add bounded
  characterization tests that pin its current observable behavior at the
  cheapest level, then refactor under them. Never test internal structure to
  manufacture RED.
- **Intentional requirement change** → update the obsolete expectation in place
  with an explicit contract rationale; do not add a new test beside the stale
  one.

## Selecting the RED test

Inspect the existing tests before choosing where to express RED, then decide in
order:

1. **Inventory.** Inspect the existing tests, fixtures and helpers, and the
   lane's current run time against its budget when readable.
2. **Additional value.** If an existing test already detects the regression,
   extend or rely on it. Every retained addition covers a distinct behavioral
   obligation or failure mode.
3. **Level.** Choose the cheapest level that proves the behavior: in-process
   unit → in-process integration (real collaborators, no child process or
   network) → child process / CLI → end-to-end. A test above the cheapest
   feasible level names what the cheaper level cannot prove (the behavior *is*
   the exit code, environment handling, wire format, or seam); record that
   reason in the footer.
4. **Placement.** Minimally extend a suitable existing test when the expectation
   belongs to the same cohesive scenario, without removing or weakening its coverage.
   Create a new test when the behavior is distinct or reuse would make the test unclear
   or weaken its value as regression coverage — built on existing fixtures and
   helpers, not new scaffolding.
5. **Parameters.** When parameterizing, choose equivalence-partition
   representatives and boundaries, not combinatorial products; count executions
   × fixture cost before extending.
6. **RED evidence.** An existing failing test counts as RED only when its
   failure precisely represents the intended behavior.
   Unrelated failures do not establish RED; add or extend a focused test and
   observe it fail for the intended reason.
7. **Budget.** When the lane is at or over its budget, RED is still written;
   GREEN does not land until "REFACTOR includes the suite" brings the lane back
   within budget, or a logged exception applies. Without a budget there is no
   breach — the level ladder still applies and the footer reports the suite
   delta.

## Execution scope

- RED/GREEN: run the focused scenario only.
- After convergence: run the affected module or component tests.
- Full suite: at the repository's declared cadence (pre-commit, closeout, CI),
  never per RED/GREEN step.

Inputs therefore distinguish the focused test command from the full command
when the runner supports it; the footer records which scope ran.

## REFACTOR includes the suite

After GREEN, review the tests this cycle touched or made redundant:

- Retire a test whose regression protection is now carried by the test just
  written or extended: name the successor and show it fails for the retired
  test's reason, or use a controlled removal.
- Fold duplicated scaffolding into the suite's shared helpers.
- Move a test down a level when the lower level proves the same thing.
- Where evidence is insufficient, retain the test and name the verification
  needed.

This step is bounded to supersession evidenced in this cycle. Retirement judged
from similarity or history belongs to `test-quality-audit`, which measures the
accumulated suite and applies `verify-then-retire`.

## Delegated work

Each worker applies "Selecting the RED test" inside its own write set. The
parent runs the suite step once across all workers' tests at integration,
before final verification, because only the parent sees the whole suite.

## Config options

- `variant` — which discipline satisfies the invariant (`test-first` | `test-alongside`; see Variants).
- `scope` — globs the policy governs (default: production source).
- `exceptions` — categories exempt from the failing-test-first gate, always logged.
- `feedback-budget` — `<lane>: <duration>` pairs (e.g. `unit: 30s`): the
  project-declared wall-clock ceiling for the lane the RED test runs in.
  Resolution: an explicit value; else `inherited` from a budget the repository
  already declares (guidance, a CI job timeout, a Suite health table); else
  none. Derivation: declared by the project and observed from the configured
  test command's run time when readable — never new telemetry. Consumers: the
  budget step above, the footer, and `test-quality-audit`, which reads the same
  declared budget. No numeric mandate, no test-count quota, no new enforcement
  machinery.
- `enforcement` — `model` (behavioral default) or `model+gate` (adds the phase-2 PreToolUse backstop).
- `coverage-floor` — optional numeric minimum for the `test-after` downgrade.

## Opt-out ladder (must stay low-friction — this is where choice lives)

- Disable: negate/remove the init line, or `tdd-policy: off`.
- Per-task: a single phrase ("skip TDD — spike", "over budget — accepted,
  spike") → applied and logged in the footer, never silent.
- Per-scope: `exceptions` / `scope` globs.
- Downgrade: `test-after` + coverage floor — relaxes the invariant, logged as an
  opt-out, not a variant.

Every path is one line or one phrase; none require ceremony.

## Graceful degradation

If adopting guidance is malformed, ambiguous, or self-contradictory, stop and
ask or no-op — never mass-generate output. Narrow scope keeps any failure local.

## Enforcement — honest limits

Phase 1 is model-behavioral: an enforced-by-default posture, NOT a mechanical
guarantee. Standing instructions decay over long sessions and the
"about-to-write-code" moment is fuzzy, so a model can drift past it. The only
mechanical enforcement is the optional `enforcement: model+gate` PreToolUse hook
(phase 2). State this limit; do not oversell.

## Delegation

- Test adequacy / brittle assertions, and retirement judged from similarity or
  history → `test-quality-audit`.
- Code/module design → `software-design`.
- Commit/branch preflight → `git-workflow-policy`. PR/MR → `pr-ops`. Issues → `issue-ops`.

## Output footer

End every run with:

```
tdd-policy: <mode> | variant <v> | change <behavioral|refactor|requirement-change> |
level <unit|in-process|child-process|e2e>[: reason] | ran <focused|affected|full> |
suite delta <+n/−m tests; lane <time|unknown> vs budget <value|inherited|none>> |
retired: <list|none> | exceptions/opt-outs applied: <list|none> |
enforcement <model|model+gate>, gate <ran|n/a> | reference core-workflow.md | delegated: <list|none>
```
