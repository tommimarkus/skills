# Software Design Model Pressure

Use this file before adding detail to the skill or its references. Core
pressure IDs: `SD-MP-1`, `SD-MP-2`, `SD-MP-3`, `SD-MP-4`, `SD-MP-PAT-1`,
`SD-MP-PRINCIPLE-1`, `SD-MP-SMELL-1`. The lift the core demonstrated under
those pressures: force fit, evidence layers, smell-code output, sibling
delegation, false-positive guards, and anti-ceremony stops.

Each stack record carries four fields: the baseline failure the generic core
showed, the accepted extension rule that fixed it, the retest case, and the
merge-back condition — the failure class to re-check in a fresh-agent retest;
if the core alone no longer shows it, the extension rule merges back.

- `SD-MP-TS-1` — baseline failure: DTO/export drift. Accepted extension rule:
  exports, translation, aliases, validation ownership. Retest: the TS case.
  Merge-back condition: package/export/type-runtime drift.
- `SD-MP-RS-1` — baseline failure: feature/trait drift. Accepted extension
  rule: `pub`, features, traits as contracts. Retest: the Rust case.
  Merge-back condition: feature/trait ceremony.
- `SD-MP-JAVA-1` — baseline failure: module/interface drift. Accepted
  extension rule: exports, source sets, singletons, one-use interfaces.
  Retest: the Java case. Merge-back condition:
  module/export/singleton/interface drift.
- `SD-MP-CSHARP-1` — baseline failure: familiar EF/hosted-service patterns.
  Accepted extension rule: refs, friends, DI roots, EF/domain collapse,
  hosted-service ownership. Retest: the .NET case. Merge-back condition: EF
  ceremony and hosted-service policy.

Two expansion gates apply. A smell-catalog expansion must record the baseline
failure, the accepted smell-catalog rule, the behavior eval ID that exercises
it, and the merge-back condition. Any other expansion of skill detail must
record why the shorter rule fails, the rerun command, and the removal
condition.

2026-06-01 smell expansion: fixed undefined ranges; added `SD-B-2`, `SD-B-4`,
`SD-C-2`, `SD-C-4`, `SD-S-2`, `SD-E-2`, `SD-Q-2`, and .NET/Python evals.
Merge back if fresh-agent runs show no lift or weak evidence.

2026-07 Lookup load cap: Lookup answers from the matched catalog only; the
core reference is not loaded. Catalogs carry `Cite` anchors; the gating text
names the escalation cue (code evidence, cross-section tradeoffs, or no
matching row -> Review/Build or ask). Retest: behavior evals
`software-design-behavior-lookup-catalog-only` and
`software-design-behavior-lookup-escalation`; scenario `sd-lookup-principle`.
Merge back (drop the cap) if fresh-agent lookups under-answer or mis-cite
sections.

2026-07 Python application/library expansion: python.md broadened from
tooling-only to package/module/application/library design, closing the
routing residue where api-design hands general module design back while
python.md delegated all web/ASGI — Python service internals and libraries
landed core-only. Added `python.SD-B-1`, `python.SD-C-2`, `python.SD-C-3`,
`python.SD-S-1`; kept the tooling codes; web/ASGI HTTP contracts and UI still
delegate api/app-design. Retest: trigger evals
`software-design-trigger-yes-python-library-review` and
`software-design-trigger-yes-python-service-internals`; behavior evals
`software-design-behavior-python-application-module-smells` and
`software-design-behavior-python-packaging-surface`. Merge back (re-narrow to
tooling) if fresh-agent Python application reviews show no lift over core
`SD-*`.

2026-07 §3.9 concurrency/error-contract expansion: added `SD-C-6`, `SD-S-5`,
and `SD-Q-4` with playbook §3.9 (concurrency/cancellation ownership and
error-contract design); the core-only baseline missed unowned background
work, collapsed failure taxonomies, and stacked retries, or misrouted the
specialist slices instead of delegating them. Retest: behavior evals
`software-design-behavior-core-smell-unowned-concurrency`,
`software-design-behavior-core-smell-error-contract-collapse`,
`software-design-behavior-core-smell-stacked-retries`, and
`software-design-behavior-error-contract-delegation`. Merge back (retire the
codes into family prose) if fresh-agent reviews show no lift over core
`SD-C-4`/`SD-S-1`/`SD-Q-2`.

2026-07 expert-probe adoption: coverage-gap inspect/default additions from
clean-context probe runs are recorded in `../evals/expert-probe.md` (each run
entry carries the gap, the addition, and the merge-back condition); retest by
re-running the probe lens against the changed extension.

2026-07 §3.10 testability/seam expansion: added `SD-B-5` with playbook §3.10
(testability and seams) and a false-positive guard on `rust.SD-C-3` for trait
seams at genuine isolation boundaries; the core-only baseline had no owner
for designing code to be testable, and the Rust extension flagged legitimate
isolation seams as ceremony with no counterweight. Retest: behavior evals
`software-design-behavior-core-smell-missing-seam` and
`software-design-behavior-rust-legitimate-seam`. Merge back (retire `SD-B-5`
into family prose and drop the guard) if fresh-agent reviews show no lift
over core `SD-C-4`/`SD-W-1`.
