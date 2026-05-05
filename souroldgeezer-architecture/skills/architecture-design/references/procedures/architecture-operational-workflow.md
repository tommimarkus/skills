# Architecture Operational Workflow

Load this file after `architecture-design/SKILL.md` selects Build, Extract,
Review, Lookup, or the explicit render-polish loop. It preserves the detailed
procedures that are intentionally not always loaded by the skill router.

## Mode Dispatch

### Build

Use Build for new or edited ArchiMate® diagrams from architect intent:
"design the architecture", "model the system", "sketch an ArchiMate view",
"build a capability map", "draw how this fits in the enterprise".

### Extract

Use Extract for lifting a model from existing code, IaC, and workflow
definitions: "lift architecture from the repo", "reverse-engineer the
architecture", "generate an Application Cooperation view from the project set".

Refuse Extract when the requested layers are entirely forward-only:
Business/Motivation/Strategy/Physical from source or IaC. Explain that only
Application, Technology, Implementation & Migration, and supported
`LIFT-CANDIDATE` process evidence are extractable. Suggest Build with architect
intent.

### Review

Use Review for an existing `.oef.xml`, professional-readiness review,
well-formedness, render artifacts, external validation handoff, route repair,
global polish, PNG validation, or drift detection.

Sub-behaviours:

- Artefact review: OEF file alone or "is this well-formed".
- External validation handoff: OEF plus Archi import, Validate Model, schema,
  `xmllint --schema`, or conformant-tool findings.
- Render request: OEF plus PNG/render/visual inspection/refresh request.
- Drift detection: OEF plus current code/IaC/workflows, or explicit drift
  question.

When several apply, run artefact review first, render second, drift last.

### Lookup

Use Lookup for narrow notation or model-discovery questions:
element/relationship meaning, Appendix B validity, OEF `xsi:type`, domain
discovery across canonical OEF files, or reverse lookup from symbol/file/UI/API
artifact to owning Business Process. Lookup does not mutate the model.

### Render Polish Loop

Use only when the user explicitly asks to iterate until rendered diagrams are
visually pristine or to compose all modes for render quality.

Sequence per iteration:

1. Review the current OEF, including artifact review, source-geometry gate, and
   render when available. Record `AD-Q*`, `AD-L*`, `AD-B-*`, and render findings
   by view id.
2. Extract only for current source truth; never invent forward-only content.
3. Build the smallest model/layout patch using layout strategy and professional
   readiness, preserving identifiers and valid architect placements.
4. Lookup only for bounded notation, relationship, coverage, or reverse lookup
   questions.
5. Render and compare every requested artifact, validate every PNG, inspect all
   outputs, and compare source/render snapshots against the baseline.

Stop the loop only when the source-geometry gate passes, every rendered view
passes visual inspection, no unresolved blocker/warn `AD-L*`, `AD-B-*`, or
`AD-Q*` finding caps the target quality, drift is resolved or documented as
architect-owned, and the final diff contains only intentional changes.

## Pre-flight

Before producing, editing, rendering, or reviewing a diagram, establish these
inputs. Ask only for missing answers that cannot be inferred safely.

1. **Diagram kind.** Supported kinds are Capability Map, Application
   Cooperation, Service Realization, Technology Usage, Migration, Motivation,
   and Business Process Cooperation. The English label and OEF `viewpoint=`
   value are identical. Decline other kinds unless the user asks for a narrow
   Lookup answer.
2. **Layer scope.** Default to Core Framework
   (Business/Application/Technology) unless the diagram kind implies Strategy,
   Motivation, or Implementation & Migration. Crossing extensions into a Core
   view without cause is `AD-7`.
3. **Extraction posture.** In Extract, read applicable `.NET`, Bicep, GitHub
   Actions, `host.json`, `staticwebapp.config.json`, Durable Functions
   orchestrator, and Logic Apps workflow signals. Fully forward-only layers are
   emitted only as architect-owned stubs when the diagram kind requires them.
4. **Feature name and canonical path.** Default to
   `docs/architecture/<feature>.oef.xml`, where `<feature>` is a short snake or
   kebab-case slug derived from the prompt, solution, or architect instruction.
5. **Process scope.** In Build, ask only when the §9.7 or §9.3 process scope is
   ambiguous. Use `single-process` when exactly one Business Process is named;
   otherwise default to `all-processes-in-feature`. `multi-feature` requires an
   explicit feature list. Extract applies process-view emission automatically
   whenever process lifting emits elements.
6. **Quality target.** Build/Extract default to `diagram-readable`. Review
   assesses whether the artifact reaches `review-ready`. This is an OEF/model
   target, not README/gallery/CI publication readiness.
7. **Change classification.** Classify intended and observed changes as
   `semantic model change`, `view geometry change`, and/or
   `documentation/render inventory change`. Hiding a relationship from one view
   while preserving it in `<relationships>` is view geometry, not semantic.
8. **Render request.** Default is no. When yes, use
   `references/scripts/archi-render.sh`; do not substitute another renderer.
9. **External validation evidence.** Load
   `external-validation-handoff.md` only when findings are supplied. Ask for the
   report if the user asks about tool-reported findings but omits it.
10. **Layout intent.** Select `preserve-authored`, `route-repair-only`,
    `generated-layout-recreate`, or `global-reflow` from
    `layout-strategy.md`. "Recreate", "regenerate", "generate all diagrams",
    "rebuild the views", or "use the improved layout backend" selects
    `generated-layout-recreate`; prior coordinates are comparison input, not
    locks, unless explicitly locked. Backup before overwrite and include the
    per-view backend report.

State deviations from defaults in the footer.

## Project Assimilation

Direction is one-way: assimilate the project to the architecture reference, not
the reference to the project. Reference layer discipline, aspect rules,
Core-vs-extension defaults, and relationship well-formedness are
non-negotiable.

Run lightweight discovery from canonical locations only:

1. Existing model at `docs/architecture/<feature>.oef.xml`. Parse identifiers,
   names, relationships, view coordinates, documentation, and properties. Reuse
   valid content and treat absence as greenfield.
2. `.NET` solution surface: `*.sln`, `*.csproj`, Azure Functions isolated
   worker, Blazor WebAssembly, Blazor Web App `.Client`, top-level class
   libraries, and `<ProjectReference>` topology.
3. Azure Functions `host.json`: bindings become Application Interfaces; host
   runtime implies System Software on a Function App/App Service Node.
4. `staticwebapp.config.json`: maps to Azure Static Web Apps Node, hosted UI
   Application Component, routes, and auth provider interfaces.
5. Bicep IaC: supported Microsoft resource types map through
   `lifting-rules-bicep.md`.
6. GitHub Actions workflows: deployment/release jobs become Work Packages;
   environments become Plateaus; successful deploys become Implementation
   Events.
7. Durable Functions and Logic Apps workflow definitions: load
   `lifting-rules-process.md` for Business Process/Event/Interaction
   `LIFT-CANDIDATE` evidence.
8. Render contracts, disclosure only: detect committed architecture PNG/SVG
   files, gallery sections, and render commands. If OEF changes and committed
   renders/galleries exist, disclose that they may need refresh. Do not update
   project packaging unless explicitly requested or render-polish is in scope.

Forward-only layers are never extracted from source. Preserve existing
Business, Motivation, Strategy, and Physical content verbatim when valid; the
architect owns it.

Reuse names freely, but reuse structure only when it is substantively compliant
with ArchiMate® 3.2. Flag and correct misplaced layers (`AD-1`/`AD-3`), invalid
relationships (`AD-2`), identifier/name mismatches (`AD-8`), missing
realisation chains (`AD-6`), missing forward-only markers (`AD-14`), invalid
model-root properties (`AD-17`), invalid metadata namespaces (`AD-16`), and
other cataloged findings. Do not propagate broken relationships into new
output.

Footer assimilation block reports existing diagram reuse, labels preserved,
sources read, drift/well-formedness issues, and render contracts detected.

## Build Workflow

1. Confirm Build mode. Read and run `self-check.md`; record the result.
2. Run pre-flight and project assimilation. Announce diagram kind, layer scope,
   layout intent, quality target, and change classification.
3. Load the architecture reference sections for principles, supported diagram
   kind, element palette, relationships, OEF serialization, and checklist.
   Output must obey layer separation, aspect rules, Core-vs-extension
   discipline, and Appendix B relationship well-formedness.
4. Compose elements and relationships. Use correct `xsi:type` values from the
   ArchiMate® catalog. Never emit a relationship not valid for the element pair.
   Preserve view-specific curation only when the model relationship remains and
   the view documents why the visible connection is hidden.
5. When the diagram kind and process scope require it, load and apply
   `process-view-emission.md` before layout.
6. Load `layout-strategy.md` and only the applicable layout sub-procedures.
   Create a layout decision record per emitted view: view id, viewpoint,
   layout intent, backend eligibility, selected command/fallback, request and
   result validation state, materialization state, and blockers. For
   `generated-layout-recreate`, prior coordinates are not locks. Materialize
   every view with `<node>` and `<connection>` geometry.
7. Load `professional-readiness.md`. Every emitted view names the architecture
   question it answers, curates extraction noise, and receives a readiness and
   authority classification.
8. Write the OEF to the canonical path unless the architect specified another.
   Do not emit `propid-archi-model-banded` or model-root `<properties>`.
   Include the default Dublin Core `<metadata>` block; set `dc:title` to the
   feature and `dc:creator` to `architecture-design <plugin-version>` from the
   live architecture plugin manifest. The OEF top-level child order is:
   `name`, `documentation`, `metadata`, `elements`, `relationships`,
   `organizations`, `propertyDefinitions`, `views`.
9. Validate before delivery. Run `validate-oef-layout.sh` for local OEF files.
   Treat emitted lines as source-geometry `AD-L*` findings. If rendering was
   requested, run `archi-render.sh`, require Validate Model marker output, then
   validate every PNG with `arch-layout.sh validate-png`. Consume supplied
   external validation through `external-validation-handoff.md`.
10. Emit the output contract and footer.

## Extract Workflow

1. Confirm Extract mode. Read and run `self-check.md`; record the result.
2. Run pre-flight and refuse entirely forward-only extraction requests.
3. Run project assimilation and record discovered source/IaC/workflow surfaces.
4. Read each applicable lifting procedure before using it:
   `lifting-rules-dotnet.md`, `lifting-rules-bicep.md`,
   `lifting-rules-gha.md`, `lifting-rules-process.md`.
5. If process lifting emitted Business Process/Event/Interaction elements, load
   `process-view-emission.md` before layout. If Strategy/Motivation or
   forward-only Business Service stubs are emitted, load `seed-views.md` before
   layout.
6. Load `layout-strategy.md` and applicable sub-procedures. Apply the selected
   layout intent per view. `global-reflow` attempts route repair first, then
   `global-polish` only when route-only repair cannot reach the requested
   quality. `preserve-authored` repairs or generates only invalid/missing
   geometry.
7. Emit forward-only stub blocks only when the diagram kind requires them. Use
   the mandatory marker:

   ```xml
   <!--
   ==============================================================================
   FORWARD-ONLY — this layer was not extracted from source
   The architect must fill in: <layer name>
   The skill inferred suggestive placeholders from Application element labels
   ==============================================================================
   -->
   ```

8. Merge with an existing canonical model rather than gratuitously overwriting
   it. Preserve valid identifiers, labels, documentation, properties,
   forward-only content, and stable placements. Remove missing extracted
   elements only with drift disclosure. Reroute when a preserved bendpoint is
   stale, inverted, crosses unrelated nodes, or starts/ends inside endpoint
   bodies. Report `AD-L11` if no clean route exists.
9. Load `professional-readiness.md`, classify each view and artifact rollup,
   validate source geometry, run requested render/PNG checks, and emit the
   per-layer lift/stub breakdown in the footer.

## Review Workflow

1. Confirm Review mode. Read and run `self-check.md`. Missing
   `architecture.md`, `smell-catalog.md`, `validate-oef-layout.sh`, or an
   applicable procedure is `not run (blocker)` for affected findings.
2. Run pre-flight, classify requested or observed changes, and identify
   sub-behaviours.

### Artefact Review

1. Parse the OEF into elements, relationships, views, nodes, connections, and
   placements. If a local file path exists, run `validate-oef-layout.sh` and
   include `AD-L*` findings directly.
2. Cap at `model-valid` before judging polish when a view lacks materialized
   element nodes, node `x/y/w/h`, visual relationship connections, or unique
   identifiers.
3. Load `external-validation-handoff.md` only when external findings are
   supplied. Map findings before readiness rollup.
4. Load `professional-readiness.md`. Classify each view, derive artifact rollup
   as the worst-view minimum, and cap by unresolved model-level blockers
   (`AD-15`, `AD-17`, `AD-14`, `AD-14-LC`, `AD-16`, `AD-22`).
5. Walk the reference checklist. For each item record pass, fail, or
   not-applicable. Failures become namespaced findings using
   `smell-catalog.md`.

Layout-severity dispatch: `AD-L11` is always blocking. `AD-L12` through
`AD-L20` block `diagram-readable` and `review-ready` when they make layout
communication unreliable, even if their finding severity is `warn`.

Per-finding format:

```text
[<AD-N>] <file>:<line or element identifier>
  layer:    static | runtime
  severity: block | warn | info
  evidence: <quoted XML fragment: element, relationship, or view node>
  action:   <suggested fix referencing architecture.md and ArchiMate>
  ref:      architecture.md §<n.m> + ArchiMate® 3.2 §<chapter> / Appendix B
```

### Render Request

Run static artifact checks first. Then run `archi-render.sh` only when render,
PNG, visual inspection, or refresh is requested. Pass through caller-supplied
`--archi-bin`, `--cache-root`, `--config`, `--output-root`, and
`--validate-model-script`.

The render script imports OEF through Archi's headless CLI, runs
`validate-model.ajs`, requires `ARCHI_VALIDATE_MODEL:` marker output, and then
renders every OEF view to PNG. Missing Archi, jArchi script support, `DISPLAY`,
`xmllint`, Validate Model script, marker output, malformed XML, invalid Validate
Model findings, or script exit is a render blocker, not a fallback opportunity.
Report the exact command/failure and `Visual render inspection: not run`.

`ARCHI_VALIDATE_MODEL: INVALID` findings are render blockers.
`ARCHI_VALIDATE_MODEL: WARN` findings are surfaced as external validation
evidence. When PNGs are produced, inspect every emitted PNG and run
`arch-layout.sh validate-png --image <rendered.png> --result <result.json>`.
Add baseline/tolerance only when a prior render exists and comparison was
requested.

Render gate: when visual quality was requested and render did not run, changed
views are capped at `model-valid`. Unchanged views inherit their prior
classification.

### Drift Detection

1. Load `drift-detection.md`.
2. Re-run project assimilation against current source/IaC/workflows.
3. Compare discovered elements/relationships to the OEF.
4. Report deltas as `AD-DR-*` findings with `layer: runtime`.
5. Suggest either updating the diagram to match current source truth or updating
   code to match an intentional architect-owned model.
6. Emit well-formedness and drift rollups.

## Lookup Workflow

### Notation Q&A

Search only the relevant architecture reference section for the element type,
relationship, diagram kind, OEF `xsi:type`, or Appendix B entry. Answer in one
or two sentences with reference anchors.

### Domain Discovery

Enumerate `docs/architecture/**/*.oef.xml`. Parse views whose diagram kind is
§9.7 Business Process Cooperation or §9.3 Service Realization. List each
Business Process/Event/Interaction with its name, owning view identifier, and
file path. Filter by feature basename when the question narrows the area.
Rank by feature proximity, then incoming Triggering edge count.

### Reverse Lookup

Backend symbol path:

1. Locate the symbol in source.
2. Find the enclosing Durable Functions orchestrator or Logic Apps workflow.
3. Search canonical OEF files for a Business Process whose XML comment,
   `source=` property, or normalized name matches.
4. Return the process name, owning view, and file path. Follow one-hop parent
   process back-pointers from §9.3 sub-process views when present.

UI path:

1. Locate Blazor `*.razor`, Next.js `app/**/page.tsx` or `pages/*.tsx`, or React
   Router component files.
2. Search canonical OEF files for a UI Application Component in a §9.3 view
   whose name, `source=` property, or documentation matches.
3. Walk outgoing Realisation to the top Business Process and return name, view,
   and file path.

If no match exists, report `unmodelled` and suggest Extract for backend
workflow symbols or manual §9.3 authoring for UI components. Do not fabricate a
process name.

## Validation And Quality Rules

Validation layers:

- `[static]`: inspect OEF source, relationships, geometry, identifiers, metadata,
  and reference checklist.
- `[external]`: consume downstream Archi/import/schema/Validate Model evidence
  through `external-validation-handoff.md`.
- `[visual]`: run render tooling when requested and inspect every emitted PNG.
- `[runtime]`: compare source/IaC/workflow state for drift when in scope.

Use `validate-oef-layout.sh` for local materialized views before claiming
`diagram-readable` or `review-ready`. Use `arch-layout.sh` for
`validate-request`, `validate-result`, `layout-elk`, `route-repair`,
`global-polish`, `materialize-oef`, `layout-provenance`, and `validate-png`
when those runtime paths apply.

Classify quality per view first, then derive the artifact rollup as the
worst-view minimum. Report the independent authority axis from
`professional-readiness.md`: `lifted-from-source`,
`forward-only-or-inferred`, `architect-approved`, or
`stakeholder-validated`. Authority does not gate readiness. Emit `AD-Q11` when
an authority override claims architect/stakeholder approval while unresolved
`FORWARD-ONLY` or `LIFT-CANDIDATE` content remains.

Do not claim `review-ready` for a view with unresolved `AD-Q*`, `AD-L2`,
`AD-L3`, `AD-L4`, `AD-L11` through `AD-L20`, `AD-B-*`, `AD-6`, `AD-2`,
`AD-18`, `AD-20`, `AD-21`, or unresolved external validation findings. Do not
claim artifact-level `review-ready` while model-level blockers remain.

## Render Artifacts

Rendered PNGs are deployment/publication artifacts derived from OEF, not the
architecture source of truth. OEF XML remains the model.

When rendering succeeds, classify changed PNGs, README rows, galleries, or
provenance text as `documentation/render inventory change`. Do not classify a
render-only refresh as a semantic model change unless `<elements>` or
`<relationships>` changed.

When OEF changes and project assimilation found committed renders or gallery
sections, disclose that those artifacts may need refresh. Update them only when
the user requested that work or the explicit render-polish loop is in scope.

## Finding Namespaces

Use `references/smell-catalog.md` as the compact code-to-reference index.
Architecture findings are notation-level, not stack-level. Preserve these
namespaces:

- `AD-*`: architecture reference and OEF/model findings.
- `AD-L*`: layout, geometry, routing, and render-readability findings.
- `AD-B-*`: Business Process and process-flow artifacts.
- `AD-Q*`: professional-readiness and quality findings.
- `AD-DR-*`: drift findings.

Load `red-flags.md` when output contains findings, imports fail, schema or
Validate Model reports unresolved issues, or a failed check precedes a readiness
claim.
