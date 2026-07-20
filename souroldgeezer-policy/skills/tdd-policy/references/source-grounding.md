# TDD Policy Source Grounding

This skill centralizes test-first discipline into a passive policy that
repositories initialize with local options and exceptions, plus an on-demand
enforce path. Plugin installation alone does not enforce it; the standing repo
guidance line — which must embed the invariant — is the enforcement authority.
`adopt-guidance` consolidates existing test-first prose into that standing block.
Enforcement is honest: a default posture in phase 1, mechanically guaranteed only
by the optional phase-2 gate. Keep guidance original; link external material only
when needed.

## Boundary Decisions

- Test-first enforcement while writing code: `tdd-policy`.
- Adequacy/brittleness of existing tests: `test-quality-audit`.
- Code/module design and coupling: `software-design`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues: `issue-ops`.
