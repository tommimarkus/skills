---
name: tdd-policy
description: "Use when loaded repo guidance initializes tdd-policy, or when asked to inspect, adopt, or enforce test-driven development — test-first ordering, RED→GREEN→REFACTOR, coverage floor, exceptions — before or while writing implementation code. Not for test-quality auditing or general code/module design."
---

# TDD Policy

Own standing test-first discipline for repositories that explicitly initialize
this policy, and answer explicit "enforce TDD now" requests. The shared
enforcement posture — passive install, opt-in through the consumer's own
guidance, the standing line (which carries the invariant itself) as enforcement
authority, low-friction opt-out — is canonical in
[`../../docs/policy-reference/policy-posture-core.md`](../../docs/policy-reference/policy-posture-core.md);
this skill supplies procedure, config, variants, and opt-out handling on demand.

Inputs: request, repo guidance, initialized options/exceptions, the code about to
change, the test command/runner, existing tests.
Evidence: cite the initialization source or explicit request, the variant and
scope in force, exceptions/opt-outs applied, and the failing-test → pass cycle or
the blocker.

Read [references/core-workflow.md](references/core-workflow.md) before real
enforcement, guidance edits, or adoption. When editing triggers, behavior, source
grounding, or evals, also read `references/evals` and
[references/source-grounding.md](references/source-grounding.md).

Modes: default `enforce-initialized` when loaded repo guidance initializes this
policy and the model is about to write/modify implementation code, or on an
explicit enforce request; otherwise default `lookup`. Narrower modes: `inspect`,
`adopt-guidance` (writes the standing block — MUST embed the invariant per the
reference template), `preflight` (check a change's TDD compliance before
commit/PR). Modes scope work; the standing line and repo guidance remain
authoritative.

Rules: do not enforce just because the plugin is installed. Enforce when loaded
repo guidance initializes `tdd-policy`, or the user explicitly asks to enforce
TDD. Treat an initialization line as current-task authority before implementation
changes; the invariant is "a failing test precedes implementation;
RED→GREEN→REFACTOR; shipped behavior stays covered." Apply initialized options;
bare initialization uses the default profile in `references/core-workflow.md`.
Keep opt-out low-friction (disable line, one-phrase per-task override logged,
scope/exception globs, `test-after` downgrade) — opt-out is where user choice
lives. `test-after` relaxes the invariant and is an opt-out, never a variant.
Delegate test adequacy to `test-quality-audit`, code/module design to
`software-design`, commit/branch preflight to `git-workflow-policy`, PR/MR to
`pr-ops`, issues to `issue-ops`.

Ask vs continue: continue when scope, variant, exceptions, and the test command
are clear. Stop and ask on ambiguous scope, an unlogged exception request, or when
the test command cannot run and no substitute exists. Malformed or ambiguous
adopting guidance → stop-and-ask or no-op; never mass-generate.

Enforcement honesty follows the posture core's limits rule (enforced-by-default
posture, no mechanical guarantee; the only mechanical path is the optional
`enforcement: model+gate` PreToolUse hook, deferred to phase 2).

Stop before letting implementation land with no failing test first unless an
explicit, logged exception applies. Stop if the required test run cannot happen and
no documented substitute exists.

After guidance edits, rerun structured-file checks, `git diff --check`, and the
repo's documented skill-architecture validation. End with the output footer from
[references/core-workflow.md](references/core-workflow.md).
