# Software Design Model Pressure

Use before adding detail. Core IDs: `SD-MP-1`, `SD-MP-2`, `SD-MP-3`, `SD-MP-4`, `SD-MP-PAT-1`, `SD-MP-PRINCIPLE-1`, `SD-MP-SMELL-1`. Core lift: force fit, evidence layers, smell-code output, sibling delegation, false-positive guards, and anti-ceremony stops.

Stack records use baseline failure, accepted extension rule, retest, and merge-back condition: `SD-MP-TS-1` DTO/export drift -> exports, translation, aliases, validation ownership -> TS case -> package/export/type-runtime drift; `SD-MP-RS-1` feature/trait drift -> `pub`, features, traits as contracts -> Rust case -> feature/trait ceremony; `SD-MP-JAVA-1` module/interface drift -> exports, source sets, singletons, one-use interfaces -> Java case -> module/export/singleton/interface drift; `SD-MP-DOTNET-1` familiar EF/hosted-service patterns -> refs, friends, DI roots, EF/domain collapse, hosted-service ownership -> .NET case -> EF ceremony and hosted-service policy.

Smell-catalog expansion gate: record baseline failure, accepted smell-catalog rule, behavior eval ID, and merge-back condition. Expansion gate: record why shorter rule fails, rerun command, and removal condition.

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
