# TDD Policy Source Grounding

This skill centralizes test-first discipline into a passive policy that
repositories initialize with local options and exceptions, plus an on-demand
enforce path. Plugin installation alone does not enforce it; the standing repo
guidance line — which must embed the invariant — is the enforcement authority.
`adopt-guidance` consolidates existing test-first prose into that standing block.
Enforcement is honest: a default posture in phase 1, mechanically guaranteed only
by the optional phase-2 gate. Keep guidance original; link external material only
when needed.

## RED Test Selection Rationale

- Classify the change first. Behavior-preserving refactors run under existing
  passing tests; demanding fresh RED for them manufactures implementation-detail
  tests, a silent growth driver under the earlier contract. Bounded
  characterization coverage is added only where protection is missing.
- Inspect the current suite first so the RED step follows the repository's test
  structure instead of assuming that every behavior needs another test.
- Extend a suitable test for a cohesive existing scenario, preserving its prior
  expectations and regression value. The synthetic cohesive-reuse behavior case
  exercises this branch.
- Create a focused test for a distinct scenario, or when reuse would weaken
  clarity or regression coverage. The synthetic distinct-scenario behavior case
  exercises this branch and requires the rationale to be visible.
- Weigh additional value and cost. Suite run time is driven by the slow tail of
  expensive tests, not by test count — in the maintainers' own suite a tenth of
  the tests held more than half the run time. Hence the level ladder, the
  parameter-partition rule, and the named seam reason for a higher-level test.
- Scope execution: the focused scenario during RED/GREEN, affected tests after
  convergence, the full suite at the declared cadence. The cycle must not pay
  the full-suite cost per step.
- Accept an already failing test as RED only when that exact failure specifies
  the intended change; nearby or unrelated failures are not test-first evidence.
- Keep the suite in REFACTOR. The earlier contract preserved coverage but never
  retired anything. In-cycle supersession is the one retirement the author can
  evidence — the successor fails for the retired test's reason — so it lives
  here; retirement judged from similarity or history stays with
  `test-quality-audit` as `verify-then-retire`.
- The feedback budget is declared once by the project and `inherited` where a
  budget already exists. The policy observes the configured command's run time
  and adds no telemetry, so an absent budget yields observation, not a gate.
- Each cost-aware rule above has a synthetic behavior case in
  `references/evals/behavior-cases.jsonl`; the contract test keys every case to
  its rule.

## Test Authoring Rationale

The "Writing the test" rules rest on Kent Beck's
[Test Desiderata](https://testdesiderata.com/) (properties such as isolated,
deterministic, fast, and structure-insensitive) and the Google Testing Blog's
[test-size restrictions](https://testing.googleblog.com/2010/12/test-sizes.html)
(smaller tests forgo sleeps, system properties, and external resources). Paraphrased
rationale per rule:

- Reuse before define: a helper defined twice drifts twice; a defaulted
  parameter on the shared builder keeps one definition serving every caller.
- Setup lifetime: sharing only immutable setup keeps tests isolated, and
  cleanup that survives failure stops one broken test from poisoning the next.
- Time and waiting: fixed sleeps are either too short, which makes the test
  flaky, or too long, which makes the suite slow; a controlled clock or a
  bounded wait on an observable condition is neither.
- Machine independence: a test passed in its author's environment and failed on
  a colleague's machine because the decimal separator differed by locale. That
  is why RED must be able to fail where it runs, and why expected values never
  come from the authoring environment. Missing locale data falls back silently,
  so a requested setting is asserted to have taken effect.
- Minimal input and isolation: the smallest fixture keeps failures diagnosable
  and fast; per-test resources remove order dependence.
- Lane: a marker, tag, or location lets the project run each size where it
  belongs and keeps the budget measurable per lane.
- Duplication evidence from the maintainers' own suite: nine test modules
  re-implemented a module loader and git helpers that the suite's shared support
  file already provided, data builders were redefined in up to five modules, and
  blocking clones in the tests directory climbed from 0 to 168 because no gate
  scanned it. Hence reuse-before-define, the duplication-detector step in
  REFACTOR, and naming the shared support paths in delegated reads.

## Seam and Retention Rationale

The size brake works inside each cycle: a test is retained only if it pins
behavior at the declared seam and would survive a behavior-preserving refactor.
Sources are linked and paraphrased; none of their text is bundled.

- The seam. Ian Cooper's talk, as
  [distilled by Herberto Graca](https://herbertograca.com/2018/08/27/distillation-of-tdd-where-did-it-all-go-wrong/),
  argues that the unit under test is a module rather than a class or method and
  that a new test is triggered by a new requirement, not by a new function. The
  default seam, the public API of each module or package, follows from that;
  the project may declare another rule, and the language's visibility markers
  derive it otherwise.
- Retention check. Vladimir Khorikov's four properties of a good test
  (regression protection, resistance to refactoring, fast feedback,
  maintainability), in
  [one reader's notes](https://olano.dev/blog/unit-testing-principles), say that
  a test coupled to implementation details raises false alarms. Asking whether a
  behavior-preserving refactor would force the test to change puts that
  maintenance cost on the cost axis. The Practical Test Pyramid
  [article](https://martinfowler.com/articles/practical-test-pyramid.html)
  treats the urge to test a private method as a design signal, advises deleting a
  higher-level test that lower-level tests already cover, and warns against
  keeping a test out of sunk cost.
- Trivial code. The same notes describe Khorikov's four kinds of code: trivial
  code needs no test of its own, domain logic and algorithms get unit tests,
  controllers get a short integration test, and code both complex and highly
  connected is split first. That is the decision aid behind `trivial`; the split
  is handed to `software-design` by skill name. `trivial` is a classification,
  not an exception, so a trivial change that alters seam-visible behavior is
  behavioral.
- Scaffold tests. A test below the seam may drive out a design step, as Kent
  Beck's [Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd) turns one list
  item at a time into a test. It is resolved in REFACTOR of the same cycle:
  rewritten at the seam or deleted. Deleting it needs no supersession proof
  because it never pinned seam behavior.
- Characterization expiry. Characterization coverage exists to protect a
  refactor in flight, so only what sits below the seam expires with it. Tests
  already at the seam are ordinary regression tests and leave only through
  supersession.
- Behavior removal. A test for behavior that no longer ships has nothing to
  regress against, so it goes in the same change and needs no successor. The
  coverage clause is intact: removed behavior is no longer shipped.
- Examples per rule. Organizing by rules with a few examples under each is the
  [Example Mapping](https://www.cucumber.io/docs/bdd/example-mapping) shape;
  splitting a rule that needs many examples, or covering it with one
  property-based test, is this policy's own corollary, not a claim of that page.
  [Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/) supports
  keeping scenarios declarative: wording that would change with the
  implementation should be rewritten.
- Diff-scoped mutation evidence. Google's
  [mutation testing work](https://research.google/pubs/state-of-mutation-testing-at-google/)
  runs a diff-based approach during code review, which motivates scoping a
  configured mutation tool to the changed code. A new test that kills no mutant
  the existing tests miss adds no distinct regression value. No new option is
  added; it follows the duplication-detector shape.
- `structure-coupled` records. A test that a behavior-preserving refactor had to
  edit is tied to internal structure. Listing it in the footer is evidence for
  `test-quality-audit`'s `verify-then-retire`, stronger than similarity or
  history, but it never retires a test by itself. The footer is the record; no
  telemetry is added.

Rejected, with reasons:

- Count quotas and coverage targets: they reward tests for trivial code, which
  this policy deliberately leaves untested.
- Automated suite minimization: Noemmer and Haas
  ([SWQD 2020](https://teamscale.com/hubfs/26978363/Publications/2020-test-suite-minimization-swqd.pdf?hsLang=en))
  found suites could shrink in size and execution time by over 70% on average,
  at an average loss of about 12.5% in fault detection (mutation score), up to
  21% for some projects. That supports the stance that similarity never retires
  a test.
- Test impact analysis and predictive test selection
  ([Meta](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/)):
  already a runner lever in `test-quality-audit`'s suite-recovery procedure, so
  it stays there.

## Forward Checks

Two fresh-agent runs (Claude Sonnet, 2026-10-15) on synthetic Python
repositories with a shared `tests/support.py` loader and builder. pytest was not
installed, so a shared support module stood in for `conftest.py`.

- Standing line only, skill not loaded. The task was a CSV export whose amount
  column must use a dot on every machine. The agent reused the existing loader
  and row builder. It made RED fail under a comma-decimal condition set in
  process, by patching the locale lookup rather than calling `setlocale`, then
  confirmed the command under a real comma-decimal locale after GREEN. That
  meets the rule. Patching the lookup does tie the test to how the code reads
  the locale; setting a real locale in process, with a took-effect check,
  avoids that coupling.
- Skill loaded, `software-design` absent. The task was a readiness poller with a
  timeout. The agent injected a fake clock (no real sleeps), placed it in the
  shared support module, and read the new test's duration from the focused
  run. Its footer carried `cost` and `stack idioms n/a`.

## Boundary Decisions

- Test-first enforcement while writing code, including the change
  classification, RED level and placement, execution scope, and in-cycle
  retirement of a test the new test supersedes: `tdd-policy`.
- Adequacy/brittleness of existing tests, and retirement judged from similarity
  or history: `test-quality-audit`. Both read the one declared feedback budget.
  `structure-coupled` records feed its `verify-then-retire` and never retire a
  test by themselves.
- Code/module design and coupling: `software-design`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues: `issue-ops`.
- Cross-plugin handoffs go by skill name, never a path: plugins install
  independently, so a relative link into another plugin cannot resolve. When
  the named skill is absent the neutral rules still stand on their own, and the
  footer records the gap as `stack idioms: n/a`.
