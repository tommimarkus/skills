---
name: tdd-policy
description: "Use when loaded repo guidance initializes tdd-policy, or when asked to inspect, adopt, or enforce test-driven development — test-first ordering, RED→GREEN→REFACTOR, the observable-behavior seam, behavioral-change vs refactor classification, RED test level and placement, execution scope, suite feedback budget, coverage floor, exceptions — before or while writing implementation code. Not for test-quality auditing or general code/module design."
---

# TDD Policy

Apply TDD when a repository initializes it or the user explicitly asks for it.
The repository's standing rule carries the invariant and is sufficient for
routine implementation when the observable behavior, test scope, and applicable
options are settled. Installation alone is passive under the shared
[policy posture](../../docs/policy-reference/policy-posture-core.md).

## Routine implementation

1. Inspect existing tests. For new or changed observable behavior, reuse or
   extend a cohesive test where possible. Observe it fail for the intended
   reason at the cheapest level that proves the change. Use existing passing
   tests for covered refactors and trivial wiring with no observable change.
2. Implement and rerun the focused test. Run affected checks after convergence
   and broader gates at the repository's declared cadence.
3. Resolve temporary scaffold tests before landing. Remove coverage for retired
   behavior. Consolidate surviving coverage when a successor catches the same
   regression.

Use `enforce-initialized` for this path and `lookup` for questions. Report the
actual checks, material limits, and meaningful exceptions in the normal result.
If essential verification is unavailable, land only with a documented or
explicitly authorized substitute.

## When to read more

- Use [the core workflow](references/core-workflow.md) for bare initialization,
  an explicit enforce request without a standing rule, or a decision the local
  rule leaves open. Open the relevant section for seam or scope ambiguity,
  missing protection, pinned expectations, retirement, feedback budgets,
  delegated work, or exceptions. Existing suite debt alone does not block a
  focused change. Honor explicit hard ceilings and landing requirements.
- For `adopt-guidance`, use the [standing block template](references/core-workflow.md#standing-block-template).
  For `preflight`, use [TDD preflight](references/core-workflow.md#tdd-preflight).
  `model` is the supported enforcement setting. Surface and resolve any
  explicit `model+gate` requirement before taking a governed action.
- For suite-wide adequacy or retirement based on similarity or history, use
  `test-quality-audit`. Use `software-design` for language-specific test idioms
  when they matter to the change.
- Before editing guidance, read the core workflow. For trigger, behavior,
  grounding, or eval edits, also read `references/evals` and
  [source grounding](references/source-grounding.md). After editing, run
  structured-file checks, `git diff --check`, and the repo's skill validation.
