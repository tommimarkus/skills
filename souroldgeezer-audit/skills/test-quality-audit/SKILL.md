---
name: test-quality-audit
description: Use when auditing unit, integration, or E2E test quality — distinguishing specification tests from characterization tests (unit), incidentally-scoped tests (integration), or scope-and-provenance failures (E2E), surfacing coupling, scope, and browser-layer smells, and producing per-test findings with severity and recommended actions. Dispatches on detected test type. Supports quick single-file / PR-diff audits and deep suite-wide audits with pluggable per-stack extensions.
---

# Test Quality Audit

## Purpose

Audit tests for quality. Select one rubric per test, then report findings using
stable smell codes from [references/smell-catalog.md](references/smell-catalog.md).

- **Unit / component:** Could this test have been written from a stated
  requirement alone, without seeing the implementation?
- **Integration:** What seam does this test integrate, and why could not a unit
  test prove the same thing?
- **E2E:** What user-observable outcome does this prove, why could not a
  cheaper test prove it, and could it have been written from the user story
  alone?

Before applying a rubric, read the matching canonical reference:

- Unit: [../../docs/quality-reference/unit-testing.md](../../docs/quality-reference/unit-testing.md)
- Integration: [../../docs/quality-reference/integration-testing.md](../../docs/quality-reference/integration-testing.md)
- E2E: [../../docs/quality-reference/e2e-testing.md](../../docs/quality-reference/e2e-testing.md)

When producing audit output, read
[references/procedures/per-test-output-fields.md](references/procedures/per-test-output-fields.md)
for per-test fields, severity rules, examples, and the required finding shape.
Before finalizing findings, consult
[references/procedures/audit-rules-and-common-mistakes.md](references/procedures/audit-rules-and-common-mistakes.md)
for cross-rubric rules and auditor failure modes.

## Modes

Use **Quick mode** for a single file, single test, or PR diff. Audit only the
target and emit per-test findings.

Use **Deep mode** for a full suite, module, or pre-refactor quality check.
Enumerate tests, produce per-test findings, per-file rollup, suite assessment,
and a prioritized remediation worklist. In deep mode, read
[references/procedures/deep-mode-output-format.md](references/procedures/deep-mode-output-format.md)
before emitting the rollup.

If the request is ambiguous between quick and deep mode, ask the user. Do not
run the full deep workflow for a single-file or PR-diff request.

## Extension Loading

Extensions live in `extensions/*.md`; read [extensions/README.md](extensions/README.md)
when extension layout or composition is relevant. Load every matching core
extension before rubric selection, then load the matching rubric addon after
step 0b.

| Signal | Extension core to load |
|---|---|
| `*.csproj` or `*.sln`; .NET test package refs such as xUnit, NUnit, MSTest, Moq, bUnit, Playwright, Selenium, or Stryker.NET | [extensions/dotnet-core.md](extensions/dotnet-core.md) |
| `package.json` or runner configs for Jest, Vitest, Mocha, `node:test`, Testing Library, Playwright, Cypress, WebdriverIO, Supertest, MSW, Testcontainers, fast-check, or Stryker JS | [extensions/nodejs-core.md](extensions/nodejs-core.md) |
| Next.js app signals: `next` dependency, `next.config.*`, App Router, Pages Router, Route Handlers, `proxy.*`, legacy `middleware.*`, or `@next/*` packages | [extensions/nodejs-core.md](extensions/nodejs-core.md) then [extensions/nextjs-core.md](extensions/nextjs-core.md) |
| Python test signals: `pyproject.toml`, `setup.cfg`, `tox.ini`, `noxfile.py`, `pytest.ini`, `unittest` / `pytest` imports, Hypothesis, pytest-asyncio, Playwright Python, Selenium, Django, Flask, FastAPI, Starlette, SQLAlchemy, or Alembic | [extensions/python-core.md](extensions/python-core.md) |
| Robot Framework signals: `.robot`, `.resource`, `.tsv`, Robot packages, `robot`, `rebot`, `pabot`, or Robot XML / xUnit result artifacts | [extensions/robotframework-core.md](extensions/robotframework-core.md) |

| Rubric selected | .NET | Node.js / TypeScript | Next.js | Python | Robot Framework |
|---|---|---|---|---|---|
| Unit / component | [dotnet-unit](extensions/dotnet-unit.md) | [nodejs-unit](extensions/nodejs-unit.md) | [nextjs-unit](extensions/nextjs-unit.md) | [python-unit](extensions/python-unit.md) | [robotframework-unit](extensions/robotframework-unit.md) |
| Integration | [dotnet-integration](extensions/dotnet-integration.md) | [nodejs-integration](extensions/nodejs-integration.md) | [nextjs-integration](extensions/nextjs-integration.md) | [python-integration](extensions/python-integration.md) | [robotframework-integration](extensions/robotframework-integration.md) |
| E2E | [dotnet-e2e](extensions/dotnet-e2e.md) | [nodejs-e2e](extensions/nodejs-e2e.md) | [nextjs-e2e](extensions/nextjs-e2e.md) | [python-e2e](extensions/python-e2e.md) | [robotframework-e2e](extensions/robotframework-e2e.md) |

Extensions add namespaced smells, positives, detection signals, carve-outs, and
tool declarations. They never replace the core rubric. When multiple
extensions load, apply [extensions/README.md § Cross-extension composition](extensions/README.md#cross-extension-composition).

## Workflow

### 0. Detect stack and load extensions

Inspect manifests, runner configs, test files, and result artifacts. Load every
matching core extension. If no extension matches, continue with the core rubric
and disclose the limitation.

### 0b. Select the rubric

Select rubric by this precedence:

1. Explicit user instruction.
2. Project-level signal: E2E/browser project; integration project or real
   framework/infrastructure project; otherwise ordinary `*.Tests` projects
   default to unit.
3. File-level signal from loaded extensions: browser automation routes to E2E;
   real host/server/container/emulator setup routes to integration.
4. Test-level signal for mixed files.
5. E2E sub-lane signal: `A` accessibility, `P` performance, `S` security, else
   `F` functional journey.

If dispatch remains ambiguous, ask the user which rubric or E2E sub-lane to
apply. Record rubric and sub-lane selection in deep-mode output.

### 1. Establish target and scope

Identify the file, glob, PR diff, single test, project, or suite. In deep mode,
confirm the test projects or directories in scope and enumerate all test files
using loaded extension patterns.

### 2. Read supporting infrastructure

Before judging a test body, inspect referenced test bases, fixtures, custom
helpers, page objects, factories, keyword resources, and runner configuration.
This prevents false positives against idiomatic helpers.

### 3. Audit each test

Apply the selected rubric using the fields in
[references/procedures/per-test-output-fields.md](references/procedures/per-test-output-fields.md).
Apply core smells first, then loaded extension smells filtered by `Applies to:`,
then exact extension carve-outs. Emit one finding per test under exactly one
rubric; cite all matched codes but choose the highest applicable severity.

### 4. Deep-mode suite checks

Only in deep mode:

- Run SUT surface enumeration when the extension has patterns; read
  [references/procedures/sut-surface-enumeration.md](references/procedures/sut-surface-enumeration.md).
- Run auth matrix coverage when the integration extension declares it; read
  [references/procedures/auth-matrix-enumeration.md](references/procedures/auth-matrix-enumeration.md).
- Run migration upgrade-path enumeration when the extension declares it; read
  [references/procedures/migration-upgrade-path.md](references/procedures/migration-upgrade-path.md).
- Run mutation testing only when the loaded extension declares a tool and the
  detection command says it is installed; read
  [references/procedures/mutation-testing.md](references/procedures/mutation-testing.md).
- Run determinism verification only when gated in and cheap enough; read
  [references/procedures/determinism-verification.md](references/procedures/determinism-verification.md).

Never run gap detection, mutation testing, or determinism reruns in quick mode.
Never run mutation testing against E2E targets.

### 5. Report output

Quick mode emits only per-test findings. Deep mode adds the per-file rollup,
suite assessment, pyramid ratio, gap report, runtime distribution, determinism
findings, mutation testing subsection, and prioritized remediation worklist.

Static-only gaps are probable. Do not turn them into implementation work unless
the worklist item explicitly includes a verification step. Mutation-confirmed
or manually-confirmed gaps may be prioritized as confirmed work.

## Rules and Stop Conditions

- Assume the code under test may be wrong; never use observed SUT output as the
  source of truth for expected values.
- Test through public APIs and user-observable behavior; private methods,
  framework internals, and pure delegation glue are not audit targets.
- Reward positive signals explicitly.
- Be honest about static-audit limits. If spec links, coverage, mutation,
  flake history, git history, or contract pacts would change the verdict, say
  so instead of fabricating certainty.
- Stay read-only during audits unless the user explicitly asks for fixes.
- If a loaded extension lacks a needed procedure, tool declaration, or
  detection section, skip that step with a limitation instead of guessing.
- If a mutation, determinism, or gap-detection step fails, report the state and
  continue with static findings; do not make the audit fail solely on optional
  evidence tooling.

## Skill Maintenance

When changing rubric wording, dispatch rules, output contracts, extensions, or
examples for this skill, run the golden-corpus procedure in
[references/procedures/golden-corpus-evals.md](references/procedures/golden-corpus-evals.md)
using the corpus notes in [references/golden-corpus/README.md](references/golden-corpus/README.md)
and the seed cases in
[references/golden-corpus/test-quality-audit-cases.jsonl](references/golden-corpus/test-quality-audit-cases.jsonl).
Use the results to catch false-positive, false-negative, routing, severity, and
action drift before finishing the skill change.
Also read `references/evals` and `references/source-grounding.md` when changing
trigger metadata, workflow behavior, or evaluation coverage. Keep behavioral
eval cases synthetic or originally paraphrased; do not copy external prompts,
code, fixtures, tables, diagrams, or docs into this plugin.
After any skill, extension, reference, output-contract, or metadata edit, rerun
`scripts/skill-architecture-report.sh .` and repeat this maintenance check
until it reports no current advisory findings.
