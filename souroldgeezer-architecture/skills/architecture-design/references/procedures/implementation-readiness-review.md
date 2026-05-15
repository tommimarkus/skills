# Implementation-Readiness Review

Use in Review mode when the user asks whether architecture docs are enough as
an implementation handoff, where findings should live, or whether a package can
guide implementation without the rest of the source material.

Report: implementation-readiness verdict; evidence inventory; architecture-documentation findings; other source material findings; skill/package issue classification; ArchiMate equivalence; Implementation impact. Recommend links to implementation contracts, not duplicated contracts. Do not treat architecture docs as a complete implementation specification. runtime/package readiness claims are separate from implementation-handoff completeness claims.

For architecture-documentation findings, include `Finding`, `Expected in
architecture docs`, `Expected form`, `ArchiMate equivalence`,
`Architecture-design skill issue`, `Implementation impact`.

Architecture-owned classes: product/stakeholder intent; confirmed process
semantics with source-lifted content kept `candidate-from-source` until
confirmed; API surface; data ownership/lifecycle; security/trust boundaries;
environment; operations/gates. These map to Motivation, Strategy, Capability,
Business, Application, Technology, Implementation/Migration, Requirement,
Constraint, Grouping, Serving, Access, Triggering, Flow, Realization,
Assignment, and related ArchiMate concepts; ADRs, decisions, wire contracts,
UI behavior, runbooks, commands, and schemas are companion material.

Route out unless claimed by the package: exact API shapes, persistence schemas,
UI/browser/copy/a11y/i18n/perf behavior, OAuth/cookie/token mechanics,
Bicep/GitHub workflow variables, tests/fixtures/CI jobs, class design, DI,
mappers, algorithms, caching, retries.

Code routing: `ARCH-Q-3` for readiness claims beyond evidence; `ARCH-X-2` for
absent required architecture evidence; `ARCH-V-4` for intentionally absent
supported diagram kind; `ARCH-V-3` or `ARCH-Q-2` for views that cannot answer
the handoff question; `ARCH-M-4` for architect-owned content presented as
extracted fact. Do not report source-material gaps as architecture-design
defects unless the package claimed that detail.
