---
name: test-quality-audit
description: >-
  Use when auditing unit, integration, E2E, browser, or framework tests for brittle assertions, false confidence, weak scope, missing edge coverage, coupling, flakiness, or suite gaps.
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
in all modes (discipline + output contract). In Deep mode only, also load
[`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md)
(risk tier) and
[`../../docs/audit-reference/sampling-projection.md`](../../docs/audit-reference/sampling-projection.md)
(scale) — these are
Deep-scale tools; Quick must not load them.
This skill adds the test rubric and `HC-*/I-*/E-*` namespace on top; it does not
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

In Deep mode only, also load the matched stack's `deep.md` (SUT enumeration,
determinism, mutation); Quick mode never loads it.

Load [`references/extensions/authoring.md`](references/extensions/authoring.md) only when editing extension structure.

Load procedures only when needed from `references/procedures/`: per-test
output fields ([`per-test-output-fields.md`](references/procedures/per-test-output-fields.md)),
audit rules and common mistakes
([`audit-rules-and-common-mistakes.md`](references/procedures/audit-rules-and-common-mistakes.md)),
auth matrix enumeration
([`auth-matrix-enumeration.md`](references/procedures/auth-matrix-enumeration.md),
step 2.6, deep integration only), migration upgrade-path enumeration
([`migration-upgrade-path.md`](references/procedures/migration-upgrade-path.md),
step 2.7, deep integration only), guardrails, deep output, and
SUT/determinism gates. Load
[`references/procedures/mutation-nodejs.md`](references/procedures/mutation-nodejs.md) or
[`references/procedures/mutation-dotnet.md`](references/procedures/mutation-dotnet.md)
only in Deep mode when the matching stack extension is active and mutation
evidence is requested or reached.

## Modes

Quick audits one file, one test, or a PR diff with per-test findings only.
Deep audits a suite/module, enumerates tests, then adds rollups and a worklist.
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
4. Apply core smells, extension smells filtered by `Applies to:`, and exact
   carve-outs. Emit one finding per test under one rubric; cite matched codes
   and use the highest applicable severity.
5. Deep only: run gated suite checks when extension support exists and cost is
   acceptable; never run them in Quick mode, and never mutate E2E targets.
6. Report. Quick emits per-test findings only. Deep adds rollup, suite
   assessment, pyramid ratio, gap report, runtime distribution, determinism,
   mutation section, and remediation worklist.

## Rules and Stop Conditions

- Assume SUT output may be wrong; do not derive expected values from it.
- Audit public APIs/user-observable behavior, not private methods, internals, or
  delegation glue.
- Reward positives; stay read-only unless fixes are requested.
- If extension data or optional tooling is missing/fails, report the limit and
  continue with static findings.

## Skill Maintenance

Maintenance: for rubric/dispatch/output/extension/example edits, run
[`references/procedures/golden-corpus-evals.md`](references/procedures/golden-corpus-evals.md)
and use `references/golden-corpus/`. For trigger/workflow/grounding/eval edits, read `references/evals`.
For those edits, read [`references/source-grounding.md`](references/source-grounding.md);
keep evals synthetic. After skill-surface edits in the marketplace source repo, rerun its
`scripts/skill-architecture-report.sh .` (repo tooling, not bundled with the
installed plugin).
