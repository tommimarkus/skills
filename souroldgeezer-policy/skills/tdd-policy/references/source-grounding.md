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

- Inspect the current suite first so the RED step follows the repository's test
  structure instead of assuming that every behavior needs another test.
- Extend a suitable test for a cohesive existing scenario, preserving its prior
  expectations and regression value. The synthetic cohesive-reuse behavior case
  exercises this branch.
- Create a focused test for a distinct scenario, or when reuse would weaken
  clarity or regression coverage. The synthetic distinct-scenario behavior case
  exercises this branch and requires the rationale to be visible.
- Accept an already failing test as RED only when that exact failure specifies
  the intended change; nearby or unrelated failures are not test-first evidence.

## Boundary Decisions

- Test-first enforcement while writing code: `tdd-policy`.
- Adequacy/brittleness of existing tests: `test-quality-audit`.
- Code/module design and coupling: `software-design`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues: `issue-ops`.
