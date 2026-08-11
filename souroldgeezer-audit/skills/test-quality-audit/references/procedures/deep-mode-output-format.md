# Deep mode output format

**When this runs:** every Deep audit loads this file before workflow steps 5
and 6. It defines the per-file rollup, suite assessment, required Suite health
block, and prioritized remediation worklist. Quick-mode audits emit per-test
findings only and do not load this procedure.

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

Use a configured one-shot suite command only when it is read-only, has bounded
cost acceptable to the engagement, and does not mutate E2E targets or external
state. Call this a **safe one-shot suite execution** only after those checks;
otherwise rely on readable current artifacts and disclose the limitation.

## Per-file rollup

After all per-test findings, emit:

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

| Lane/layer | Purpose/cadence | Count | Current result | Runtime distribution | Declared budget | Reliability | Owner |
|---|---|---:|---:|---:|---:|---|---|
| unit / pre-commit | <available value> | <N> | <pass/fail/unknown> | <median/tail or unknown> | <project-declared value> | <flake/retry/skip/quarantine facts> | <owner> |
```

Current-run evidence is mandatory for a supported-positive **Current execution**
disposition: record a current pass/fail result, or `unknown-evidence-gap` with
its limit. Runtime distribution is mandatory for a supported-positive
**Efficiency** disposition: record the available distribution and slow tail, or
`unknown-evidence-gap`. Include the current-result and runtime-distribution
columns even when their values are `unknown`; other immaterial fields may be
omitted. Record layer distribution without treating a pyramid,
test count, or test-to-code ratio as a target by itself. For runtime, report the
observed distribution, slow-tail concentration, and comparable regressions.
Declare a breach only against a project-declared budget; without one, outliers
are observations rather than breaches.

Keep **current facts** separate from **historical trends**. Then emit all five
dimension dispositions with cited `SH-*` evidence. Each disposition is exactly
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
  and frequent bounded portfolio gardening.

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
The audit remains advisory and never deletes, quarantines, rewrites, or
reschedules tests automatically.
