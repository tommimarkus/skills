---
name: test-quality-audit
description: >-
  Use when auditing unit, integration, E2E, browser, or framework tests for brittle assertions, false confidence, weak scope, missing edge coverage, coupling, flakiness, suite gaps, suite strategy, runtime growth, portfolio maintenance, or TDD-generated suite pressure.
---

# Test Quality Audit

Audit whether tests prove the intended contract at the right layer. Use
`../../docs/quality-reference/` rubrics. Cite
[`references/smell-catalog.md`](references/smell-catalog.md) codes.

## Contract

Own read-only unit/component, integration, and E2E audits; delegate non-test
work. Judge unit by requirement-derived behavior, integration by named seams,
and E2E by user-observable outcomes cheaper tests cannot prove.

Inputs: target/diff/suite, mode, stack signals, specs/contracts,
helpers/fixtures, and optional coverage/mutation/flake evidence. Ask/stop when
target, mode, rubric, files, sibling ownership, requested edits, or confidence
lack a safe default. For discipline on false positives, limits, and severity, see
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2–§3.

## Load Map

Load [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md)
and [`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md)
in all modes (discipline, output contract, and grounded per-test risk tier).
In Deep mode only, also load
[`../../docs/audit-reference/sampling-projection.md`](../../docs/audit-reference/sampling-projection.md)
for scale; Quick must not load it. Deep only, also load
[`../../docs/audit-reference/scaled-audit.md`](../../docs/audit-reference/scaled-audit.md)
(delegation + evidence durability) when the suite is large enough that per-test
evidence may not reach the rollup intact; if evidence starts outgrowing context
mid-run, load it then rather than continuing.
This skill adds the test rubric and `HC-*/I-*/E-*/SH-*` namespace on top; it does not
restate craft.

Load the selected rubric before judging:

- Load [`../../docs/quality-reference/unit-testing.md`](../../docs/quality-reference/unit-testing.md) for unit/component.
- Load [`../../docs/quality-reference/integration-testing.md`](../../docs/quality-reference/integration-testing.md) for integration.
- Load [`../../docs/quality-reference/e2e-testing.md`](../../docs/quality-reference/e2e-testing.md) for E2E.
- Load [`../../docs/quality-reference/testing-core.md`](../../docs/quality-reference/testing-core.md) alongside any rubric (shared discipline + sources).

Load [`extensions/index.md`](extensions/index.md) for stack signals. When stack signals match, load
the stack's `core.md` and the matching rubric addon for each loaded stack layer
(`unit.md`, `integration.md`, or `e2e.md`) — do not load the whole stack directory:

| Stack | Load |
|---|---|
| .NET | [`references/extensions/dotnet/core.md`](references/extensions/dotnet/core.md) + selected addon |
| Java | [`references/extensions/java/core.md`](references/extensions/java/core.md) + selected addon |
| Node.js / TypeScript | [`references/extensions/nodejs/core.md`](references/extensions/nodejs/core.md) + selected addon |
| Next.js | [`references/extensions/nodejs/core.md`](references/extensions/nodejs/core.md) + addon, then [`references/extensions/nextjs/core.md`](references/extensions/nextjs/core.md) + addon |
| Python | [`references/extensions/python/core.md`](references/extensions/python/core.md) + selected addon |
| Robot Framework | [`references/extensions/robotframework/core.md`](references/extensions/robotframework/core.md) + selected addon |
| Rust | [`references/extensions/rust/core.md`](references/extensions/rust/core.md) + selected addon |

For each matched stack layer, resolve the selected addon beside that row's
`core.md`: load only `unit.md` for the unit/component rubric,
`integration.md` for the integration rubric, or `e2e.md` for the E2E rubric.
Where the stack ships `unit-integration.md` (`dotnet`, `nodejs`), also load it
when the selected rubric is unit **or** integration; never load it on the E2E
path. For Next.js, apply that selection once in the Node.js directory and once
in the Next.js directory. Do not enumerate or load a whole stack directory.

Quick mode loads only the matched stack's `core.md`, `unit-integration.md` when
the rubric selects it, and one selected rubric addon.
In Deep mode only, also load the matched stack's `deep.md` (SUT enumeration,
determinism, mutation); Quick mode never loads it. Every stack ships one.

**Escalation cue.** These caps are scope, not a fidelity ceiling. If an E2E
target shows a concern the E2E lane does not cover — an in-process mocking,
test-double, fake-timer, or parameterised-input smell reached through a
component or API-level test mixed into the E2E suite — load that stack's
`unit-integration.md` before judging it and disclose the extra load in the
footer. If a Quick target raises a SUT-enumeration, determinism, or mutation
question, say so and ask for Deep rather than answering from the Quick load set.

In every Deep audit, load
[`references/procedures/deep-mode-output-format.md`](references/procedures/deep-mode-output-format.md)
for the required Suite health evidence ladder and output contract. Quick mode
remains per-test and never loads this procedure.

In Deep mode, when a JUnit XML report is already available, use the bundled
[`references/scripts/suite_health_snapshot.py`](references/scripts/suite_health_snapshot.py)
through the host-specific command documented by that procedure. Execute the
one-shot helper without loading its source during an audit. Skill maintainers
can verify its packaged entry point with `python3
"${CLAUDE_SKILL_DIR}/references/scripts/suite_health_snapshot.py" --help` in
Claude Code, or by substituting Codex's absolute loaded-skill directory.

Load [`references/extensions/authoring.md`](references/extensions/authoring.md) only when editing extension structure.

Load procedures only when needed from `references/procedures/`: per-test
output fields ([`per-test-output-fields.md`](references/procedures/per-test-output-fields.md)),
audit rules and common mistakes
([`audit-rules-and-common-mistakes.md`](references/procedures/audit-rules-and-common-mistakes.md)),
auth matrix enumeration
([`auth-matrix-enumeration.md`](references/procedures/auth-matrix-enumeration.md),
step 2.6, deep integration only), migration upgrade-path enumeration
([`migration-upgrade-path.md`](references/procedures/migration-upgrade-path.md),
step 2.7, deep integration only), guardrails, and
SUT/determinism gates. Load
[`references/procedures/mutation-nodejs.md`](references/procedures/mutation-nodejs.md) or
[`references/procedures/mutation-dotnet.md`](references/procedures/mutation-dotnet.md)
only in Deep mode when the matching stack extension is active and mutation
evidence is requested or reached.

## Modes

Quick audits one file, one test, or a PR diff with per-test findings only.
Deep audits a suite/module, enumerates tests, assesses suite health, then adds
rollups and a worklist.
Ask when mode is ambiguous; do not deep-enumerate ordinary Quick targets.

## Workflow

1. Detect stack from manifests, runner configs, files, and artifacts; load
   matches.
2. Select rubric by explicit instruction, project/file/test signal, then E2E
   sub-lane (`A`, `P`, `S`, else `F`). Ask if dispatch is unsafe.
3. Establish target; inspect bases, fixtures, helpers, page objects, factories,
   keyword resources, and runner config before judging.
3a. Deep only — risk pass: enumerate the SUT surface, assign each surface a risk
    tier per `materiality.md`, record the tier map, and focus enumeration and
    mutation budget on high-tier surfaces first.
3b. Deep only — mandatory suite-management pass: before per-test sampling,
    establish the portfolio target, configured runner, lane selection and
    cadence, declared budgets, owners, collection count, current
    pass/fail/error/skip outcomes, elapsed time, duration distribution,
    reliability evidence, overlap review, and retirement discipline. Run one
    configured full suite automatically only when it is local, read-only,
    non-browser, non-external, and expected to finish within about ten minutes;
    ask before longer, unknown, browser, external-service, rerun, or mutation
    work. Use readable artifacts when execution is not authorized or safe.
3c. Deep only — mandatory setup/teardown lifecycle pass: inventory runner,
    suite, module/class, worker, and per-test lifecycle hooks from configuration,
    fixtures, factories, and helpers. For each material resource, map its
    current lifetime, mutability, reset mechanism, teardown path, and isolation
    obligation. Amortize only immutable or safely resettable infrastructure;
    preserve per-test mutable data and session ownership. Attribute a budget
    breach to repeated lifecycle work only from direct phase/timing evidence;
    static repetition is inference, and unsupported attribution is unknown.
    Never request new instrumentation during an ordinary audit.
4. Apply core smells, extension smells filtered by `Applies to:`, and exact
   carve-outs. Emit one finding per test under one rubric; cite matched codes
   and use the highest applicable severity.
5. Deep only: combine the suite-management and setup/teardown lifecycle passes
   with sampled per-test evidence; close all five required dimensions, suite
   verdict, lifecycle cost and safety dispositions, portfolio candidates, gaps,
   determinism, mutation, and prioritized worklist. Use only
   project-configured commands and already-readable evidence; never build an
   ingestion layer. Never run suite checks in Quick mode.
6. Report. Quick emits per-test findings, then `Quick gate: <status>`. Use the
   shared precedence: fail if any substantiated in-scope `block` remains; else
   `not-evaluated` when required evidence or machinery cannot rule out blockers;
   else `pass-limited`. Warn/info do not fail, risk is orthogonal, and a
   remediated block needs a clean rerun. Quick remains per-test and never emits
   `Gap-*` findings or a remediation worklist. Deep adds rollup, suite
   assessment, required Suite health and Setup/teardown lifecycle blocks, gap
   report, determinism, mutation section, and remediation worklist.

## Rules and Stop Conditions

- Assume SUT output may be wrong; do not derive expected values from it.
- Audit public APIs/user-observable behavior, not private methods, internals, or
  delegation glue.
- Reward positives; stay read-only unless fixes are requested.
- If extension data or optional tooling is missing/fails, report the limit and
  continue with static findings.
- Evidence progresses from static snapshot, to current run when readable
  artifacts or an acceptable configured command exist, to accessible history,
  then effectiveness only with mutation or failure-attribution evidence.
  Missing optional evidence is `unknown`, not a request for instrumentation.
  Stop only when the user explicitly requires an unsupported trend or
  effectiveness conclusion.
- `tdd-policy` owns RED→GREEN→REFACTOR. This audit judges the accumulated suite;
  test count, test-to-code ratio, and “never failed” history are informational
  alone.

## Skill Maintenance

Maintenance: for rubric/dispatch/output/extension/example edits, run
[`references/procedures/golden-corpus-evals.md`](references/procedures/golden-corpus-evals.md)
and use `references/golden-corpus/`. For trigger/workflow/grounding/eval edits, read `references/evals`.
For those edits, read [`references/source-grounding.md`](references/source-grounding.md);
keep evals synthetic. Rerun obligations after craft or skill-surface changes:
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §8.
