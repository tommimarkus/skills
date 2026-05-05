---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, repairing, or looking up enterprise, solution, or application architecture models in ArchiMate® 3.2 OEF XML, including runtime layout contract checks, layout policy diagnostics, machine-readable layout warning evidence, route repair, global polish, layout-result to OEF materialization, per-view layout provenance output, rendered PNG validation, change classification, professional-readiness review of OEF views, architecture drift checks, and reverse lookup from code, UI, API, or workflow artifacts to owning Business Processes.
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

- `responsive-design` and `api-design` produce code/API surfaces that this skill
  can model and review for drift through `docs/architecture/<feature>.oef.xml`.
- `devsecops-audit` audits pipeline and infrastructure posture; this skill only
  models those workflows as architecture elements.

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

Always one-hop discoverable from this router:

- `../../docs/architecture-reference/architecture.md`: load for notation
  principles, element/relationship rules, OEF serialization, diagram kinds,
  smell definitions, and checklist references.
- `references/procedures/architecture-operational-workflow.md`: load for
  mode-specific steps, pre-flight details, project assimilation, render-polish
  loop, forward-only rules, preservation rules, and validation sequencing.
- `references/smell-catalog.md`: load when emitting or interpreting `AD-*`,
  `AD-L*`, `AD-B-*`, `AD-Q*`, or `AD-DR-*` findings.
- `references/procedures/professional-readiness.md`: load for every Build,
  Extract, and Review readiness verdict; it owns the per-view matrix,
  authority axis, render gate, and `AD-Q*` findings.
- `references/procedures/layout-strategy.md`: load for every Build/Extract view
  and any Review repair or polish request; it selects preserve-authored,
  route-repair-only, generated-layout-recreate, or global-reflow intent.
- `references/procedures/layout-backend-contract.md`,
  `references/procedures/layout-policies-by-viewpoint.md`,
  `references/procedures/routing-and-glossing.md`, and
  `references/procedures/layout-fallback.md`: load only when the layout strategy
  selects backend generation, viewpoint policy, routing/route repair/global
  polish, or fallback layout.
- `references/procedures/lifting-rules-dotnet.md`,
  `references/procedures/lifting-rules-bicep.md`,
  `references/procedures/lifting-rules-gha.md`,
  `references/procedures/lifting-rules-process.md`,
  `references/procedures/process-view-emission.md`, and
  `references/procedures/seed-views.md`: load only for Extract, or for Build
  when process-view emission is requested.
- `references/procedures/drift-detection.md`: load when Review includes current
  source/IaC/workflow comparison or the user asks whether a model drifted.
- `references/procedures/external-validation-handoff.md`: load only when the
  user supplies Archi import, Archi Validate Model, schema, `xmllint --schema`,
  or conformant-tool findings.
- `references/procedures/rendered-png-validation.md`: load after PNGs exist or
  when rendered view comparison is requested.
- `references/schemas/layout-request.schema.json`,
  `references/schemas/layout-result.schema.json`, and
  `references/schemas/layout-provenance.schema.json`: load when validating,
  emitting, or debugging layout request/result/provenance JSON.
- `references/bin/arch-layout.jar`: never inspect directly during normal skill
  use; it is the packaged Java runtime invoked through
  `references/scripts/arch-layout.sh`.
- `references/scripts/validate-oef-layout.sh`: run for local materialized OEF
  views in Build/Extract self-check and Review artifact passes.
- `references/scripts/arch-layout.sh`: run for layout runtime commands:
  `--version`, `validate-request`, `validate-result`, `layout-elk`,
  `route-repair`, `global-polish`, `materialize-oef`, `layout-provenance`, and
  `validate-png`.
- `references/scripts/archi-render.sh` and `references/scripts/validate-model.ajs`:
  run only for explicit render requests, render-polish loops, or visual
  inspection gates; Archi and jArchi support are weak dependencies with no
  fallback renderer.
- `references/scripts/package-arch-layout.sh`: run only for plugin release
  packaging or runtime refresh after Java source changes; it rebuilds and copies
  `references/bin/arch-layout.jar`.
- `references/red-flags.md`: load when checks fail, output contains findings,
  import/schema/Validate Model reports unresolved issues, or before claiming
  `diagram-readable` / `review-ready` after a failed check.
- `references/evals/` and `references/source-grounding.md`: load only when
  changing trigger metadata, workflow behavior, layout/runtime gates, source
  grounding, or evaluation coverage.
- `references/fixtures/README.md` and top-level fixture OEF examples
  `references/fixtures/application-cooperation.oef.xml`,
  `references/fixtures/business-process-cooperation.oef.xml`,
  `references/fixtures/capability-map.oef.xml`,
  `references/fixtures/migration.oef.xml`,
  `references/fixtures/motivation.oef.xml`,
  `references/fixtures/service-realization.oef.xml`, and
  `references/fixtures/technology-usage.oef.xml`: load only when validating or
  changing the regression corpus or example coverage.
- `references/fixtures/render-quality-gate`,
  `references/fixtures/layout-backend-contract`,
  `references/fixtures/layout-contract`,
  `references/fixtures/layout-elk-java`,
  `references/fixtures/layout-elk-realistic`,
  `references/fixtures/route-repair`,
  `references/fixtures/global-polish`,
  `references/fixtures/materialize-oef`, and
  `references/fixtures/rendered-png`: load only when changing the matching
  layout backend, route repair, global polish, OEF materialization, or PNG
  validation behavior.

Tooling support load cues:

- Use references/bin/arch-layout.jar through `references/scripts/arch-layout.sh`
  when the packaged layout runtime is needed.
- Load references/fixtures when validating the whole architecture-design fixture
  corpus.
- Load references/fixtures/layout-quality-cases.md when changing layout quality
  examples.
- Load references/fixtures/lifting-quality-cases.md when changing extraction or
  lifting examples.
- Load references/fixtures/professional-quality-cases.md when changing
  professional-readiness examples.
- Run references/fixtures/validate-render-fixtures.sh when validating render
  fixture coverage.
- Load references/fixtures/global-polish when changing global polish cases.
- Load references/fixtures/layout-backend-contract when changing backend
  request/result contracts.
- Load references/fixtures/layout-contract when changing layout schema
  acceptance or rejection behavior.
- Load references/fixtures/layout-elk-java when changing Java layout backend
  cases.
- Load references/fixtures/layout-elk-realistic when changing realistic
  request-to-materialized-OEF layout loops.
- Load references/fixtures/materialize-oef when changing layout-result to OEF
  materialization.
- Load references/fixtures/render-quality-gate when changing static render
  quality gates.
- Load references/fixtures/rendered-png when changing PNG validation.
- Load references/fixtures/route-repair when changing route repair.
- Load references/procedures/layout-backend-contract.md when changing layout
  backend contracts.
- Load references/procedures/layout-policies-by-viewpoint.md when changing
  viewpoint policy selection.
- Load references/procedures/lifting-rules-bicep.md when extracting Bicep.
- Load references/procedures/lifting-rules-dotnet.md when extracting .NET.
- Load references/procedures/lifting-rules-gha.md when extracting GitHub
  Actions.
- Load references/procedures/lifting-rules-process.md when extracting process
  candidates.
- Load references/procedures/process-view-emission.md when process views are
  emitted.
- Load references/procedures/routing-and-glossing.md when routing, route
  repair, or route glossing is needed.
- Load references/procedures/seed-views.md when Extract emits forward-only seed
  views.
- Validate references/schemas/layout-request.schema.json when checking layout
  requests.
- Validate references/schemas/layout-result.schema.json when checking layout
  results.

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
