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

## Boundary Decisions

- Test-first enforcement while writing code, including the change
  classification, RED level and placement, execution scope, and in-cycle
  retirement of a test the new test supersedes: `tdd-policy`.
- Adequacy/brittleness of existing tests, and retirement judged from similarity
  or history: `test-quality-audit`. Both read the one declared feedback budget.
- Code/module design and coupling: `software-design`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues: `issue-ops`.
