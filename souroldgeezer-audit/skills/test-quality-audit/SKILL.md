---
name: test-quality-audit
description: >-
  Use when auditing unit, integration, E2E, browser, or framework tests for brittle assertions, false confidence, weak scope, missing edge coverage, coupling, flakiness, or suite gaps.
---

# Test Quality Audit

Audit whether tests prove the intended contract at the right layer. Use
`../../docs/quality-reference/` rubrics. Cite `references/smell-catalog.md`
codes.

## Contract

Own read-only unit/component, integration, and E2E audits; delegate non-test
work. Judge unit by requirement-derived behavior, integration by named seams,
and E2E by user-observable outcomes cheaper tests cannot prove.

Inputs: target/diff/suite, mode, stack signals, specs/contracts,
helpers/fixtures, and optional coverage/mutation/flake evidence. Ask/stop when
target, mode, rubric, files, sibling ownership, requested edits, or confidence
lack a safe default. Separate fact from inference, state limits, downgrade
static-only gaps, and avoid false positives/negatives.

## Load Map

Load the selected rubric before judging:

- Load `../../docs/quality-reference/unit-testing.md` for unit/component.
- Load `../../docs/quality-reference/integration-testing.md` for integration.
- Load `../../docs/quality-reference/e2e-testing.md` for E2E.

Load `extensions/index.md` for stack signals. When stack signals match, load
the corresponding core pack and selected rubric addons:

| Stack | Load |
|---|---|
| .NET | `references/extensions/dotnet/` |
| Java | `references/extensions/java/` |
| Node.js / TypeScript | `references/extensions/nodejs/` |
| Next.js | `references/extensions/nodejs/`, then `references/extensions/nextjs/` |
| Python | `references/extensions/python/` |
| Robot Framework | `references/extensions/robotframework/` |
| Rust | `references/extensions/rust/` |

Load `references/extensions/authoring.md` only when editing extension structure.

Load procedures only when needed from `references/procedures/`
for finding fields, guardrails, deep output, and SUT/auth/migration/mutation/
determinism gates.

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
`references/procedures/golden-corpus-evals.md` and use
`references/golden-corpus/`. For trigger/workflow/grounding/eval edits, read `references/evals`.
For those edits, read `references/source-grounding.md`; keep evals synthetic. After skill-surface edits, rerun
`scripts/skill-architecture-report.sh .`.
