# Deep mode output format

**When this runs:** every Deep audit loads this file before workflow steps 5
and 6. It defines the per-file rollup, suite assessment, required Suite health
block, and prioritized remediation worklist. Quick-mode audits do not load
this procedure.

Use concise findings and a compact suite assessment by default. The tables and
per-test schemas below are the detailed report shape for a requested full
report, evaluation, or formal consumer. Combining presentation does not omit
material evidence limits, change verdict derivation, or replace unknown facts
with positive claims.

## Evidence ladder

Use the highest evidence level already available; do not build a collector,
parser, persistent store, normalized schema, or CI-provider adapter.

1. **Static snapshot:** tests, runner configuration, lane declarations,
   ownership, skip/quarantine markers, and test-to-SUT mapping.
2. **Current-run evidence:** readable runner/CI artifacts or an acceptable
   project-configured command. If a result format is unfamiliar, disclose it
   and mark unavailable fields `unknown`; do not propose parser development.
3. **Historical trends:** only history already accessible through supplied
   reports, dashboards, git history, or CI history. Keep trends separate from
   current facts.
4. **Effectiveness evidence:** only mutation results or failure-attribution
   evidence support conclusions about fault detection or retirement.

Missing optional evidence is `unknown` with a limitation, not a request to add
instrumentation. Stop only when the user explicitly requested a trend or
effectiveness conclusion that the available evidence cannot support.

## Management evidence before sampling

Before sampling tests or projecting findings, establish the portfolio target,
runner, lanes, cadence, selection policy, declared budgets, owners, and the
latest accessible run. This management evidence determines whether sampling is
safe and what it can support; sampling cannot fill an absent current-run result
or runtime distribution. If the target or runner cannot be established, stop
the suite-health verdict at `not assessed` and say why.

Also inventory lifecycle hooks at runner, suite, module/class, worker, and
per-test scope from configuration, fixtures, factories, and helpers. For each
material resource, record its current lifetime, mutability, reset mechanism,
teardown path, and isolation obligation before judging setup cost or sharing.

Prefer readable current artifacts. Use a project-configured run only when its
evidence matters to the requested conclusion. Call it a **safe one-shot suite
execution** when it is local, read-only, non-browser, non-external, and expected
to finish within about ten minutes; this is an upper safety bound, not a duty
to run a full suite when a smaller confirmation suffices.

Apply [testing-core's local-confirmation rule](../../../../docs/quality-reference/testing-core.md#local-confirmation-and-task-authority)
to execution and reruns. Explicit no-rerun/existing-results-only limits remain
binding; unknown, costly, external, browser, or mutation work needs authority
covering that action and scope. Do not ask again for an already authorized action.

When a JUnit XML report is already available, the bundled one-shot parser can
extract bounded distribution evidence without retaining failure bodies or
captured output:

```text
python3 "${CLAUDE_SKILL_DIR}/references/scripts/suite_health_snapshot.py" --junit <report.xml>
python3 "<absolute-loaded-skill-dir>/references/scripts/suite_health_snapshot.py" --junit <report.xml>
```

The first form is for Claude Code. In Codex, replace
`<absolute-loaded-skill-dir>` with the absolute directory reported for the
loaded `SKILL.md`. The helper accepts one explicit `testsuite` or `testsuites`
document. It is not repository discovery, a datastore, a trend collector, or a
CI adapter, and it writes no files.

## Per-file rollup

For detailed output, emit this rollup after per-test findings:

```markdown
## Per-file rollup

| File | Tests | Spec | Char | Ambig | Top smells | Grade |
|---|---|---|---|---|---|---|
| `OrderServiceTests.cs` | 14 | 6 | 5 | 3 | HC-5, HC-7 | weak |
```

For integration files, substitute `Incidental` for `Char`; for E2E, include
the dominant sub-lane verdict. Grade is `strong`, `adequate`, `weak`, or
`not assessed`.

## Suite assessment

```markdown
## Suite assessment

- **Extensions loaded:** <names>
- **Overall verdict:** <strong / adequate / weak / not assessed>
- **Top risks:** <3-5 evidence-backed bullets>
- **Verification limits:** <unknown or unavailable evidence>
- **Assurance level:** reasonable (Deep; sampling noted when used)
- **Independence:** <independent / self-review / unknown>

### Suite health

- **Evidence sources:** <configuration, runner/CI artifacts, dashboards,
  supplied or git history, coverage/mutation reports; label each>
- **Window:** <current snapshot/run and any historical range, or unknown>
- **Limitations:** <unavailable/unreadable fields and comparability limits>
- **Current execution:** collection count; pass/fail/error/skip outcomes;
  elapsed time; duration distribution
- **Lane selection:** <selected lanes and purpose>; **ownership/cadence:**
  <available evidence or unknown>

| Lane/layer | Purpose/cadence | Count | Current result | Runtime distribution | Declared budget | Reliability | Owner |
|---|---|---:|---:|---:|---:|---|---|
| unit / pre-commit | <available value> | <N> | <pass/fail/unknown> | <median/tail or unknown> | <project-declared value> | <flake/retry/skip/quarantine facts> | <owner> |
```

In detailed output, report collection count, pass/fail/error/skip outcomes,
elapsed time, duration distribution, lane selection, and available ownership/cadence
evidence. For JUnit snapshots, report valid-versus-unknown timing coverage:
missing, malformed, negative, and non-finite durations are unknown, while a
measured zero remains zero. Percentiles and slow cases describe only observed
finite nonnegative testcase durations; mark their coverage when partial. Treat
the testcase total as unknown when any testcase duration is unknown, and treat
runtime shares as unknown when coverage is incomplete or the observed total is
zero. Do not use partial observed totals for complete cost, share, or budget
judgments. Current-run evidence is mandatory for a supported-positive **Current
execution** disposition: record the current outcomes and exit status, or
`unknown-evidence-gap` with its limit. Runtime distribution is mandatory for a supported-positive
**Efficiency** disposition: record the available distribution and slow tail, or
`unknown-evidence-gap`. Include the current-result and runtime-distribution
columns even when their values are `unknown`; other immaterial fields may be
omitted. Record layer distribution without treating a pyramid,
test count, or test-to-code ratio as a target by itself. For runtime, report the
observed distribution, slow-tail concentration, and comparable regressions.
Declare a breach only against a project-declared budget; without one, count,
elapsed time, and outliers are informational observations rather than breaches.

Keep **current facts** separate from **historical trends**. Assess all five
dimensions; present their material outcomes compactly by default. Detailed
output emits all five dimension dispositions with cited `SH-*` evidence.
Each disposition is exactly
`supported-positive`, `substantiated-finding`, or `unknown-evidence-gap`:

- **Feedback:** lane purpose, cadence, selection safety, full-suite safety net,
  and project-declared budgets.
- **Current execution:** latest result, exit status, failures, and whether a
  safe one-shot suite execution was run or intentionally not run.
- **Efficiency:** count/layer distribution, runtime and cost, slow tail,
  cross-layer overlap, and effectiveness per cost where supported.
- **Reliability:** flakes, retries, skips, quarantine ownership, exits, and
  trends where available.
- **Maintainability:** ownership, requirement/risk mapping, overlap review,
  frequent bounded portfolio gardening, and any `structure-coupled` record
  (below).

Derive the overall verdict deterministically: **weak — any block**;
**adequate — warnings or material unknowns without blocks**; **strong — all
five dimensions are supported-positive** without material limits; **not
assessed — target or runner cannot be established**. Sampling or count-only
facts never upgrade a dimension by themselves.

Classify each portfolio candidate as `keep`, `strengthen`, `move down`,
`consolidate`, `schedule later`, or `verify-then-retire`. Never recommend
deletion from coverage similarity alone. A retirement candidate needs
distinct-contract review plus mutation, failure-attribution, or
controlled-removal evidence; absent that evidence, use `verify-then-retire`.

A `structure-coupled: <named tests>` record is a compact named exception in an
ordinary task note, commit message, or PR/MR text, naming an existing test that
a behavior-preserving refactor had to edit. It is not a mandatory TDD footer.
Read it only from accessible task records or history when the project keeps it
there; when it is absent, report nothing and ask for no instrumentation. The
record needs assertion-level confirmation under
[testing-core's pin review](../../../../docs/quality-reference/testing-core.md#pinned-expectations-and-re-pin-review):
an edited justified identity or exact-output check alone is not coupling. When
incidental structure below the seam caused the edit, make the test a
`verify-then-retire` candidate whose first step is a rewrite at the seam, with the original retired under the gate above. The record is
stronger than similarity or never-failed history because a behavior-preserving
change broke the test, yet it never retires a test by itself.

### Setup/teardown lifecycle

Every Deep assessment addresses lifecycle cost and safety; use this bounded
section in detailed output:

- **Cost attribution: measured | inferred | unknown**
- **Lifecycle safety: supported-positive | substantiated-finding | unknown-evidence-gap**

Show up to five material resources/hooks. If none are material, a compact
assessment may say so; detailed output still emits both dispositions.

| Resource/hook | Current scope | Mutability/isolation need | Cost evidence | Cleanup evidence | Portfolio action |
|---|---|---|---|---|---|
| database container / suite fixture | suite | immutable infrastructure; per-test rows | <phase timing or static inference> | <reset and failure path> | <keep / strengthen / schedule later> |

`Cost attribution` is `measured` only when direct phase/timing evidence
attributes lifecycle work; `SH-HC-7` additionally requires that evidence to
attribute a declared-budget breach to unnecessary repetition of an immutable
or safely resettable resource. Use `inferred` with `SH-LC-7` when static
lifecycle evidence suggests repeated expensive setup but timing, a comparable
baseline, a declared budget, or safe-sharing evidence is incomplete. Use
`unknown` when attribution is unsupported. Never request new instrumentation
during an ordinary audit.

Derive `Lifecycle safety` from isolation and teardown evidence. Summarize
existing per-test findings such as `I-HC-A2`, `I-HC-A4`, `I-HC-A9`, and
`I-HC-A11`; do not mint a duplicate suite finding. `SH-POS-6` requires evidence
that expensive immutable or safely resettable infrastructure is safely
amortized while mutable data, users, sessions, and browser contexts remain
per-test with failure-safe cleanup.

The optimization invariant is strict: amortize only immutable or safely
resettable infrastructure; mutable data, users, sessions, and browser contexts
remain per-test. Cheap deterministic setup may repeat when it protects clarity
or isolation. Do not consolidate tests merely because their setup text matches
or their assertions differ.

### Gap report

Use one state from
[sut-surface-enumeration.md](sut-surface-enumeration.md#gap-report-format):
enumeration ran, or skipped with reason.

### Determinism findings

Use the applicable state from
[determinism-verification.md](determinism-verification.md): runtime-proven facts,
or skipped with reason.

### Mutation testing

Use the applicable state from [mutation-testing.md](mutation-testing.md): ran,
skipped because unavailable, or attempted and failed. Do not turn tool absence
into an instrumentation recommendation.

## Prioritized remediation worklist

- **P0** — <work item, evidence, expected impact, effort, candidate class>
- **P1** — <work item> `[mutation]`
- **P2** — ...

Priority is `severity × SUT risk tier` per audit-craft.md §3. Static-only gaps
are verification work. `referenced-weak` and `referenced-incidental` entries are
strengthening work. Only `confirmed-mutation` and `confirmed-manual` gaps may
become implementation work; `dismissed-indirect` gaps do not enter the worklist.
When the suite-recovery load condition in [../../SKILL.md](../../SKILL.md)
holds, load [suite-recovery.md](suite-recovery.md) and append its
`## Suite recovery program` after this worklist; it is propose-only.
The audit remains advisory and never deletes, quarantines, rewrites, or
reschedules tests automatically.
