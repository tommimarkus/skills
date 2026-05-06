---
name: test-quality-audit
description: >-
  Use when auditing unit, integration, E2E, browser, or framework tests for brittle assertions, false confidence, weak scope, missing edge coverage, coupling, flakiness, or suite gaps.
---

# Test Quality Audit

Audit whether tests prove the intended contract at the right layer. Use
`../../docs/quality-reference/` rubrics and cite codes from
`../../references/test-quality-audit-smell-catalog.md`.

## Contract

Own read-only unit/component, integration, and E2E audits; delegate non-test
work to sibling skills. Judge unit by requirement-derived behavior, integration
by named seams, and E2E by user-observable outcomes cheaper tests cannot prove.

Inputs: target/diff/suite, mode, stack/runner signals, specs/contracts,
helpers/fixtures, optional coverage/mutation/flake evidence. Ask/stop when
target, mode, rubric, files, sibling ownership, requested edits, or confidence
lack a safe default. Reject unsupported findings: separate fact from inference,
state confidence and honest limits, downgrade static-only gaps, and avoid false
positives/negatives.

## Load Map

Load the selected rubric before judging:

- Load `../../docs/quality-reference/unit-testing.md` for unit/component.
- Load `../../docs/quality-reference/integration-testing.md` for integration.
- Load `../../docs/quality-reference/e2e-testing.md` for E2E.

Load `extensions/index.md` for stack signals and full rule packs under
`../../references/test-quality-audit-extensions/`.

Load procedures only when needed from `../../references/test-quality-audit-procedures/`:
finding fields, guardrails, deep output, and gates for SUT surface, auth matrix,
migrations, mutation, or determinism.

## Modes

Quick audits one file, one test, or a PR diff and emits per-test findings.
Deep mode audits a suite/module, enumerates tests, then adds rollups and a
remediation worklist. Ask when mode is ambiguous; do not deep-enumerate ordinary
single-file or PR-diff requests.

## Workflow

1. Detect stack from manifests, runner configs, files, and artifacts; load
   matches.
2. Select rubric by explicit instruction, project/file/test signal, then E2E
   sub-lane (`A`, `P`, `S`, else `F`). Ask if dispatch is unsafe.
3. Establish target; inspect bases, fixtures, helpers, page objects, factories,
   keyword resources, and runner config before judging.
4. Apply core smells, extension smells filtered by `Applies to:`, then exact
   carve-outs. Emit one finding per test under one rubric; cite matched codes
   and choose the highest applicable severity.
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

Maintenance: for rubric, dispatch, output, extension, or example edits, run
`../../references/test-quality-audit-procedures/golden-corpus-evals.md`
and use `references/golden-corpus/`. For trigger, workflow,
grounding, or eval edits, read `references/evals` and
`references/source-grounding.md`; keep evals synthetic. After skill-surface
edits, rerun `scripts/skill-architecture-report.sh .` until clean.
