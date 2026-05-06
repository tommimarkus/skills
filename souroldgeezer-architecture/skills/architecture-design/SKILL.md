---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, repairing, or looking up ArchiMate® 3.2 OEF XML architecture models, especially layout/runtime checks, readiness review, PNG validation, drift detection, or reverse lookup from code, UI, API, or workflows to Business Processes.
---

# Architecture Design

## Purpose

Produce, extract, review, render, validate, repair, and look up ArchiMate®
architecture models in tool-neutral OEF XML. This skill answers what the
enterprise consists of: capabilities, services, components, technology nodes,
relationships, motivation, and process ownership.

The canonical architecture reference is
[../../docs/architecture-reference/architecture.md](../../docs/architecture-reference/architecture.md).
This file is only the operational router. Load the referenced procedure files
before applying their detailed rules.

## Ownership Boundary

Owns:

- ArchiMate® 3.2 notation decisions, OEF XML authoring, and architecture model
  quality.
- Build, Extract, Review, Render, Validate, Repair, Drift, and Lookup workflows
  for architecture models.
- Materialized OEF views with concrete node geometry and relationship
  connections.
- Layout runtime orchestration, source-geometry gates, route repair,
  global polish, layout-result materialization, layout provenance, rendered PNG
  validation, and per-view readiness reporting.
- Finding namespaces `AD-*`, `AD-L*`, `AD-B-*`, `AD-Q*`, and `AD-DR-*`.

Does not own:

- C4, UML, BPMN, TOGAF content metamodel, xAF, Archi-native `.archimate`, live
  cloud-resource observation, approval-board governance, or project
  documentation packaging unless the user explicitly asks for that package.
- Business, Motivation, Strategy, or Physical layer extraction from source or
  IaC. These are forward-only and architect-owned, except for explicit
  `LIFT-CANDIDATE` process evidence from supported workflow sources.

Sibling handoffs:

- `app-design`, `api-design`, and `infra-design` own app, API, and
  infrastructure design; this skill models those surfaces and reviews paired
  `docs/architecture/<feature>.oef.xml` files for architecture drift.
- `devsecops-audit` audits security posture; this skill only models controls
  and workflows as architecture elements.

## When To Use

Use for user requests that mention ArchiMate, OEF XML, architecture model
build/extract/review/render/repair/validation, architecture drift, layout
policy diagnostics, route repair, global polish, rendered PNG architecture
views, or reverse lookup from code/UI/API/workflow artifacts to Business
Processes.

Assume Build when the user asks to design architecture without supplying an
existing model. Assume Extract when they supply code/IaC/workflows without a
diagram. Assume Review when they supply a diagram or ask whether a model is
well-formed, professional, renderable, review-ready, or drifted. Assume Lookup
for a narrow factual ArchiMate/OEF question.

Ask before continuing only when the mode, feature, diagram kind, destructive
overwrite, unsupported target, or quality target is genuinely ambiguous.

Ask vs continue:

- If the request is ambiguous, ask the user before selecting a mode or changing
  an OEF file.
- **Ask** when ambiguity affects mode selection, canonical path, diagram kind,
  layer scope, destructive overwrite, render output location, external
  validation evidence, or whether project render/package artifacts are in
  scope.
- **Continue** when the router has a safe default: Build without attached
  artifacts, Extract with attached code/IaC/workflows and no diagram, Review
  with an attached OEF, Lookup for narrow factual questions, canonical path
  `docs/architecture/<feature>.oef.xml`, Build/Extract target
  `diagram-readable`, and Review target `review-ready`.

## When Not To Use

Do not use this skill for UI implementation, HTTP API design, security audits,
test quality, repo release packaging, live cloud drift, or non-ArchiMate
notation work. Refer to the owning sibling skill or explain the out-of-scope
boundary.

Refuse Extract when the requested scope is entirely forward-only
(Business/Motivation/Strategy/Physical from source or IaC). Suggest Build with
architect intent instead.

## Modes

- **Build**: create or edit an ArchiMate model from architect intent.
- **Extract**: lift the extractable layers from source, IaC, and workflows,
  preserving architect-owned forward-only content.
- **Review**: assess OEF well-formedness, professional readiness, layout, render
  quality, external validation evidence, and drift.
- **Lookup**: answer a bounded notation, OEF, domain-discovery, or reverse
  lookup question without mutating the model.
- **Render polish loop**: explicit mode composition
  `Review -> Extract -> Build -> Lookup -> render/compare` when the user asks to
  iterate until rendered diagrams are visually pristine.

## Minimal Workflow

1. Select the mode and read
   [references/procedures/architecture-operational-workflow.md](references/procedures/architecture-operational-workflow.md)
   for the selected mode before acting.
2. Run the architecture self-check from
   [references/procedures/self-check.md](references/procedures/self-check.md);
   disclose missing references, scripts, schemas, or weak dependencies as
   `not run (blocker)` for affected checks.
3. Run pre-flight from
   [references/procedures/architecture-operational-workflow.md](references/procedures/architecture-operational-workflow.md):
   diagram kind, layer scope, extraction posture, feature slug/canonical path,
   process scope, quality target, change classification, render request,
   external validation evidence, and layout intent.
4. Assimilate the project from canonical locations only. Preserve valid existing
   identifiers, labels, documentation, properties, forward-only content, and
   architect-authored geometry. Report non-compliance and drift instead of
   copying broken relationships or layout.
5. Load only the procedure references whose conditions apply. Build/Extract must
   emit materialized views; Review must classify each view before artifact
   rollup; Lookup must not mutate the model.
6. Validate before claiming quality. Use source geometry, layout runtime,
   external handoff, render, PNG, and drift checks according to the request and
   available tooling.
7. Return the required output contract and disclosure footer from
   [references/output-format.md](references/output-format.md).

## Reference Load Map

Load only the files whose conditions apply:

- Use `../../docs/architecture-reference/architecture.md` as needed for the
  full notation and modeling reference.
- Use `references/procedures/architecture-operational-workflow.md`,
  `references/procedures/self-check.md`, and `references/output-format.md` as
  needed for workflow, self-check, and response contracts.
- Use `references/smell-catalog.md` and `references/red-flags.md` as needed
  for Review findings and escalation cues.
- For readiness and validation, load `references/procedures/` files:
  `professional-readiness.md` for every Build, Extract, and Review verdict;
  `external-validation-handoff.md` for supplied Archi import, Validate Model,
  schema, `xmllint --schema`, or conformant-tool findings;
  `rendered-png-validation.md` after PNGs exist; `drift-detection.md` when
  Review compares source, IaC, or workflows.
- For layout, load `references/procedures/layout-strategy.md` for every
  Build/Extract view and any repair or polish Review; then load
  `references/procedures/layout-backend-contract.md`,
  `references/procedures/layout-policies-by-viewpoint.md`,
  `references/procedures/routing-and-glossing.md`,
  `references/procedures/layout-fallback.md`. Load `references/schemas` when
  request/result/provenance validation is in scope.
- For extraction and process views:
  load `lifting-rules-dotnet.md`, `lifting-rules-bicep.md`,
  `lifting-rules-gha.md`, `lifting-rules-process.md`,
  `process-view-emission.md`, and `seed-views.md` only for Extract, or for Build
  when process-view emission is requested.
- For local materialized OEF views, run
  `references/scripts/validate-oef-layout.sh`.
- For layout runtime work, run `references/scripts/arch-layout.sh`
  (`--version`, `validate-request`, `validate-result`, `layout-elk`,
  `route-repair`, `global-polish`, `materialize-oef`, `layout-provenance`,
  `validate-png`); use `references/bin/arch-layout.jar` only through that script.
- For explicit render/visual gates, run `references/scripts/archi-render.sh`
  and `references/scripts/validate-model.ajs`.
- For plugin release packaging or Java runtime refresh, run `references/scripts/package-arch-layout.sh`.
- For fixture corpus work, use `references/fixtures`,
  `references/fixtures/README.md`,
  `references/fixtures/validate-render-fixtures.sh`, and the matching fixture
  family.
- Use `references/fixtures/global-polish` when global polish fixtures are in scope.
- Use `references/fixtures/layout-backend-contract` when backend contract fixtures are in scope.
- Use `references/fixtures/layout-contract` when request/result schema fixtures are in scope.
- Use `references/fixtures/layout-elk-java` when Java ELK layout fixtures are in scope.
- Use `references/fixtures/layout-elk-realistic` when realistic ELK fixtures are in scope.
- Use `references/fixtures/materialize-oef` when materialization fixtures are in scope.
- Use `references/fixtures/render-quality-gate` when render quality fixtures are in scope.
- Use `references/fixtures/rendered-png` when PNG validation fixtures are in scope.
- Use `references/fixtures/route-repair` when route repair fixtures are in scope.
- For trigger metadata, workflow behavior, layout/runtime gates, source
  grounding, or evaluation coverage, load `references/evals` and
  `references/source-grounding.md`.

## Output Contract

Every final answer must include the selected mode result, evidence, quality
level, change classification, verification state, and footer fields from
[references/output-format.md](references/output-format.md).

Minimum footer fields:

- Mode, reference path, canonical OEF path, primary diagram kind, diagram kinds
  present/missing, and quality target.
- Per-view readiness and authority matrix, with artifact rollup as the worst
  view minimum.
- Change classification: semantic model, view geometry, and/or
  documentation/render inventory.
- Per-view layout backend report and source-geometry gate result.
- Self-check status, external validation handoff status, render/PNG validation
  status, runtime drift status, and weak-dependency blockers.
- Project assimilation disclosure, including existing diagram reuse,
  preserved labels, drift findings, forward-only/process-view emission notes,
  and detected render contracts when relevant.

## Stop Conditions

Stop, ask, fix, or lower the claimed quality when:

- The requested notation, extraction layer, live-resource observation, or project
  packaging scope is outside this skill.
- A required procedure/reference/script for the selected mode is missing.
- OEF XML is malformed, fails supplied downstream validation, or contains an
  unresolved model-level blocker.
- A view lacks materialized nodes/connections, source geometry fails, layout
  findings block the requested quality, or rendered PNG validation fails.
- Render was requested but Archi, jArchi script support, `DISPLAY`, XML
  validation, Validate Model marker output, or another prerequisite is missing;
  disclose visual inspection as `not run`, do not use a fallback renderer.
- Unresolved `AD-Q*`, `AD-L*`, `AD-B-*`, `AD-DR-*`, or external validation
  findings cap the requested readiness level.
- The user asks for destructive overwrite or package/render publication changes
  that were not already in scope.

## Disclosure Footer

Always disclose what was loaded, what was run, what was skipped, and why. State
external handoff counts, render blockers, weak dependency status, layout backend
or fallback per view, forward-only ownership, drift status, and whether OEF
semantics, view geometry, or documentation/render inventory changed.
