# TDD Policy Core Workflow

Standing test-first discipline for repositories that initialize this policy, and
the on-demand "enforce TDD now" path. Enforcement posture per
[`../../../docs/policy-reference/policy-posture-core.md`](../../../docs/policy-reference/policy-posture-core.md):
once initialized, the standing line is authority before implementation-code
changes.

## Invariant

New or changed observable behavior is preceded by a focused failing test that
specifies the intent, written at the cheapest level that proves it through the
declared seam, the surface where observable behavior is measured (see `seam`
under Config options). A change with no effect visible at the seam is a
refactor, however much internal structure it moves. Behavior-preserving
refactors run under existing passing tests, adding bounded characterization
coverage only where protection is missing; a failure is never manufactured to
satisfy TDD. Trivial code (wiring, plain delegation, accessors, declarative
configuration) is covered by the seam tests that exercise it and gets no RED of
its own, unless it changes an observable outcome at the seam. Every retained
test pins behavior observable at the seam, carries distinct regression value at
an appropriate execution cost, and would survive a behavior-preserving
refactor; a scaffold test below the seam lives only until its cycle's REFACTOR.
REFACTOR consolidates or retires superseded coverage, and removing a behavior
removes its tests. Shipped behavior stays covered by at least one test that
would fail if it regressed. Behavior removal and scaffold deletion keep this
clause: removed behavior is no longer shipped, and a scaffold never pinned seam
behavior.

## Standing block template

`adopt-guidance` and the default init block follow the posture core's
standing-line rule — the invariant inline, never a bare pointer. Template:

> `tdd-policy: <variant> — new or changed behavior at the seam gets a focused failing test first,
> at the cheapest level that proves it through the seam; a change with no effect at the seam is a
> refactor and runs under existing passing tests; trivial wiring, delegation, accessors, and
> declarative config get no RED of their own unless they change an observable outcome at the
> seam. A scaffold test below the seam may drive a design step only while the seam RED fails.
> RED→GREEN→REFACTOR, and REFACTOR retires or consolidates superseded coverage and resolves scaffold
> tests before GREEN lands, rewriting each at the seam or deleting it; removing a behavior removes
> its tests; shipped behavior stays covered by at least one test that fails on regression. Tests
> reuse the suite's shared fixtures and helpers, share only immutable setup, and never depend on
> real sleeps, clocks, or the machine's locale or timezone. Seam <rule|public API of each module>.
> Scope <globs>. Budget <lane: value|inherited|none>. Exceptions <list> (logged).
> Enforcement <model|model+gate>.`

## Default profile

Bare `tdd-policy` (no options) resolves to: variant `test-first`; seam = the
public API of each module or package (see `seam`); scope = production source
(excludes tests, generated, migrations, config); exceptions =
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

Classify the change by its effect at the declared seam before choosing RED:

- **New or changed observable behavior** → RED is required; continue with
  "Selecting the RED test".
- **Behavior-preserving refactor** → existing passing tests are the safety net.
  Where the code about to change has no protection, add bounded
  characterization tests that pin its current observable behavior at the
  cheapest level through the seam, then refactor under them. One written below
  the seam to reach that code expires when the refactor lands (see "REFACTOR
  includes the suite"). Never test internal structure to manufacture RED.
- **Trivial code** → wiring, plain delegation, accessors, and declarative
  configuration: code with no logic of its own, covered by the seam tests that
  exercise it, so it gets no RED of its own. Trivial is a classification, not
  an exception: it is not logged as an opt-out, and the footer's `change` field
  discloses it. Trivial code inside a behavioral change rides on that change's
  seam RED. A change that alters an observable outcome at the seam, such as a
  configuration default that changes a result, is behavioral, not trivial.
- **Intentional requirement change** → update the obsolete expectation in place
  with an explicit contract rationale; do not add a new test beside the stale
  one.
- **Behavior removal** → delete the removed behavior's tests in the same
  change. They need no successor, because the behavior no longer exists. Trim a
  test that also pins surviving behavior to that behavior instead of deleting
  it. When the removal leaves a new observable response in its place, such as
  an error or a fallback, that response is changed behavior and gets RED.

When it is unclear what a piece of code needs, place it by how complex it is
and how many collaborators it calls:

- trivial code → no test of its own;
- domain logic and algorithms → unit tests at the seam;
- controllers (code that mostly calls other code) → a short integration test
  at the seam;
- code both complex and highly connected → split it first, handing the design
  to `software-design`, then test each part as above.

## Selecting the RED test

Inspect the existing tests before choosing where to express RED, then decide in
order:

1. **Inventory.** Inspect the existing tests, fixtures and helpers, and the
   lane's current run time against its budget when readable.
2. **Additional value.** If an existing test already detects the regression,
   extend or rely on it. Every retained addition covers a distinct behavioral
   obligation or failure mode; judge that from the obligation. When the project
   configures a mutation-testing tool, also run it after GREEN, scoped to the
   changed code: a new test is retained only if it kills a mutant no existing
   test kills, otherwise extend or rely on the existing test. The footer
   reports the unique kills, or `n/a` without a tool.
3. **Level.** Choose the cheapest level that proves the behavior through the
   seam: in-process unit → in-process integration (real collaborators, no child
   process or network) → child process / CLI → end-to-end. A test above the
   cheapest feasible level names what the cheaper level cannot prove (the
   behavior *is* the exit code, environment handling, or wire format, or the
   declared seam itself sits at that level, as a CLI or wire-protocol seam
   does); record that reason in the footer.
4. **Retention.** Ask of every test to be kept: *Would a behavior-preserving
   refactor force this test to change?* If yes, the test is tied to internal
   structure: write it at the seam, or keep it only as a scaffold test, one
   below the seam that drives out an internal design step while the seam RED is
   failing. The seam RED always comes first, and the same cycle's REFACTOR
   resolves every scaffold (see "REFACTOR includes the suite").
5. **Placement.** Minimally extend a suitable existing test when the expectation
   belongs to the same cohesive scenario, without removing or weakening its coverage.
   Create a new test when the behavior is distinct or reuse would make the test unclear
   or weaken its value as regression coverage — built on existing fixtures and
   helpers, not new support code.
6. **Examples per rule.** Organize tests by rule, with a few key examples per
   rule. When parameterizing, choose equivalence-partition representatives and
   boundaries, not combinatorial products; count executions × fixture cost
   before extending. Split a rule that needs many examples into smaller rules,
   or cover it with one property-based test when the project has a
   property-testing tool. Scenario-level (BDD) tests stay declarative; their
   edge-case examples move down to the cheapest level through the seam.
7. **RED evidence.** An existing failing test counts as RED only when its
   failure precisely represents the intended behavior.
   Unrelated failures do not establish RED; add or extend a focused test and
   observe it fail for the intended reason. RED must be able to fail where it
   runs: formatting, parsing, collation, case-mapping, and time behavior may be
   unable to fail under the author's own locale or timezone, so run RED under a
   value that can fail — a comma-decimal locale, a locale with special case
   mapping, or a non-UTC zone with daylight saving. Classify the output first:
   For machine-facing output, invariance *is* the behavior; for human-facing
   output, the locale is an explicit test input.
8. **Budget.** When the lane is at or over its budget, RED is still written;
   GREEN does not land until "REFACTOR includes the suite" brings the lane back
   within budget, or a logged exception applies. Without a budget there is no
   breach — the level ladder still applies and the footer reports the suite
   delta. At GREEN, read the new test's duration from the focused run's
   output. If it lands in the lane's slow tail (measured against a readable
   duration distribution), apply the "Writing the test" moves or record a
   reason. Without a distribution, record the duration only.

## Writing the test

- **Reuse before define:** find the suite's shared test-support surface and
  search it and neighboring tests before defining a fixture, helper, or
  builder. Extend a shared builder with a defaulted parameter rather than
  copying it. A helper that a second module needs moves into the shared surface
  in the same cycle.
- **Setup lifetime:** the widest scope only for immutable or safely resettable
  infrastructure. Mutable data, users, and sessions stay per-test, with cleanup
  that runs even when the test fails.
- **Time and waiting:** No fixed sleeps or real clocks. Control time, or wait on
  an observable condition with a bounded timeout.
- **Machine independence:** the result must not depend on the runner's locale or
  culture, timezone, encoding, line endings, path separators, or message
  language. Set any of these the behavior depends on explicitly, preferably in
  process. When it is set through the environment, assert it took effect:
  missing locale data falls back silently. Expected values never come from the
  authoring environment.
- **Through the seam:** act and assert through the seam, on what it returns,
  emits, or persists, never on private state or internal call order. Needing a
  private member to reach the behavior is a design signal for
  `software-design`, not a reason to widen visibility for the test.
- **Minimal input:** use the smallest fixture that exhibits the behavior.
- **Isolation:** per-test temp dirs, ports, and environment; no order
  dependence.
- **Lane:** a test above the unit level carries the project's lane marker, tag,
  or location.
- **Stack idioms:** when `software-design` is available, apply its test-code
  file for the detected stack, loaded once per task. Otherwise apply these rules
  with the project's conventions and the runner's documentation, and disclose
  `stack idioms: n/a`.

## Execution scope

- RED/GREEN: run the focused scenario only.
- After convergence: run the affected module or component tests.
- Full suite: at the repository's declared cadence (pre-commit, closeout, CI),
  never per RED/GREEN step.

Inputs therefore distinguish the focused test command from the full command
when the runner supports it; the footer records which scope ran.

## REFACTOR includes the suite

After GREEN, or once a behavior-preserving refactor is complete, review the
tests this cycle wrote, touched, or made redundant:

- **Scaffold tests.** Resolve every scaffold test this cycle wrote: rewrite it
  at the seam when it pins a distinct seam obligation, otherwise delete it.
  Deleting a scaffold needs no supersession proof, because it never pinned
  seam behavior. GREEN does not land with an unresolved scaffold test.
- **Superseded tests.** A test that pins seam behavior retires only through
  supersession. Retire a test whose regression protection is now carried by
  the test just written or extended: name the successor and show it fails for
  the retired test's reason, or use a controlled removal.
- **Characterization expiry.** When a refactor lands, characterization tests it
  added below the seam are deleted or rewritten at the seam. Those written at
  the seam stay as ordinary regression tests and retire later only through
  supersession.
- **Structure-coupled tests.** When a behavior-preserving refactor in this
  cycle needed edits to existing tests, those tests are structure-coupled. List
  them in the footer's `structure-coupled:` field, and rewrite each at the seam
  where the cycle's scope allows; otherwise leave it. The footer is the record,
  with no new telemetry: `test-quality-audit` weighs it as `verify-then-retire`
  evidence, and it never retires a test by itself.
- **Shared setup.** Fold duplicated setup code into the suite's shared helpers.
  When the project configures a duplication detector, run it on the test files
  touched this cycle and fold its findings into shared helpers.
- **Level.** Move a test down a level when a lower level proves the same thing
  through the seam.
- **Insufficient evidence.** Where evidence is insufficient, retain the test
  and name the verification needed.

Retirement here is bounded to what this cycle evidences: supersession, the
cycle's own scaffold and characterization tests, and removed behavior (see
"Behavioral change or refactor"). Retirement judged from similarity or history
belongs to `test-quality-audit`, which measures the accumulated suite and
applies `verify-then-retire`.

## Delegated work

Each worker applies "Selecting the RED test" inside its own write set and
resolves its own scaffold tests before handing back, reporting them and any
structure-coupled tests for the parent's footer; a scaffold never waits for the
parent. The parent runs the suite step once across all workers' tests at
integration, before final verification, because only the parent sees the whole
suite. The parent names the shared test-support paths in each worker's reads.

## Config options

- `variant` — which discipline satisfies the invariant (`test-first` | `test-alongside`; see Variants).
- `scope` — globs the policy governs (default: production source).
- `seam` — the surface observable behavior is measured at: globs or a rule
  (e.g. "public exports of each package"). Bare initialization resolves it to
  the public API of each module or package (its exported or public symbols),
  not individual functions or classes. Derivation: declared by the project;
  else the language's own visibility markers (exports, `public`, `__all__`, the
  package boundary); when neither resolves it for the code about to change,
  ask. Consumers: the change classification, the level ladder, the retention
  check, scaffold resolution, and the footer.
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
  history → `test-quality-audit`, which reads `structure-coupled` records as
  `verify-then-retire` evidence.
- Code/module design, including splitting code that is both complex and highly
  connected → `software-design`.
- Language-specific test-code idioms → `software-design`.
- Commit/branch preflight → `git-workflow-policy`. PR/MR → `pr-ops`. Issues → `issue-ops`.

## Output footer

End every run with:

```
tdd-policy: <mode> | variant <v> | seam <declared rule|public API> |
change <behavioral|refactor|trivial|requirement-change|behavior-removal> |
level <unit|in-process|child-process|e2e>[: reason] | ran <focused|affected|full> |
suite delta <+n/−m tests; lane <time|unknown> vs budget <value|inherited|none>> |
cost <duration|unknown>[: reason] | mutation <n unique kills|n/a> |
stack idioms <software-design:<stack>|n/a> |
scaffold: <name: rewritten|deleted|none> | structure-coupled: <list|none> |
retired: <list|none> | exceptions/opt-outs applied: <list|none> |
enforcement <model|model+gate>, gate <ran|n/a> | reference core-workflow.md | delegated: <list|none>
```

`retired:` entries name their successor, or carry `behavior removed` (behavior
removal) or `characterization expired` (characterization expiry) instead.
Scaffold deletions go in `scaffold:`, not `retired:`.
