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
- Code/module design and coupling: `software-design`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues: `issue-ops`.
- Cross-plugin handoffs go by skill name, never a path: plugins install
  independently, so a relative link into another plugin cannot resolve. When
  the named skill is absent the neutral rules still stand on their own, and the
  footer records the gap as `stack idioms: n/a`.
