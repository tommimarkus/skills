---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, repairing, or looking up enterprise, solution, or application architecture models in ArchiMate® 3.2 OEF XML, including runtime layout contract checks, layout policy diagnostics, machine-readable layout warning evidence, route repair, global polish, layout-result to OEF materialization, per-view layout provenance output, rendered PNG validation, change classification, professional-readiness review of OEF views, architecture drift checks, and reverse lookup from code, UI, API, or workflow artifacts to owning Business Processes.
---

# Architecture Design

## Overview

Help Claude produce, extract, review, and look up ArchiMate® architecture diagrams that are correct by construction across layer discipline, element use, relationship well-formedness, and code-to-model consistency. The central problem, from §1 of the reference:

> `architecture-design` answers *what the enterprise consists of* — which capability does this serve, which application service realises it, which technology node hosts it, which motivational driver justifies its existence. Its sole notation is ArchiMate®.

**The reference is [../../docs/architecture-reference/architecture.md](../../docs/architecture-reference/architecture.md)** (bundled with the plugin). This skill is the *workflow* for applying it. Generated diagrams embody the reference's defaults; review output cites reference sections and ArchiMate® 3.2 chapter / Appendix B references; the skill never duplicates reference prose.

Read `references/evals` and `references/source-grounding.md` when changing trigger metadata, workflow behavior, layout/runtime gates, source grounding, or evaluation coverage.
Keep eval cases synthetic or paraphrased; avoid external diagrams, schemas, examples, screenshots, or standard text.
This skill is the architectural *bridge* between the code produced by [responsive-design](../responsive-design/SKILL.md) and [api-design](../api-design/SKILL.md) and the architect's mental model of the system. Build goes from intent to diagram. Extract goes from code and IaC to diagram, lifting the three extractable ArchiMate® layers and stubbing the three forward-only layers. Review checks both artefact well-formedness and drift between a diagram and current code. Siblings consume the canonical diagram path in their own Review mode to flag when code has drifted from the architect's model.

The quality bar has three explicit levels:

- **model-valid** — the OEF XML is parseable, uses valid ArchiMate® element / relationship types, and imports into conformant tools.
- **diagram-readable** — views have stable layout, legible labels, bounded density, coherent grouping, and no avoidable routing noise.
- **review-ready** — every view answers a clear architecture question, uses the right viewpoint semantics, curates extraction noise, and can be reviewed without the agent verbally explaining what it meant.

Every Build and Extract output must be a **materialized diagram**, not just a
model inventory: each `<view>` emitted by the skill carries concrete
`<node xsi:type="Element">` placements with `elementRef`, `x`, `y`, `w`, and
`h`, plus `<connection xsi:type="Relationship">` entries for the visual
relationships that carry the view's story. An element/relationship-only OEF can
be `model-valid`, but it is not `diagram-readable`.

Every OEF edit also carries an explicit **change classification**:
semantic model change, view geometry change, and documentation/render inventory
change. More than one can apply. View-only relationship curation is allowed
when a relationship remains in the model but is omitted or hidden in a specific
view because drawing it would duplicate the visual story; document the
relationship id and reason in the view documentation or final summary.

## Non-goals

- **Other architecture notations** (C4, UML deployment, TOGAF® content metamodel, xAF) → out of scope; ArchiMate® is the sole notation.
- **BPMN process modelling and UML sequence/interaction modelling** → explicitly out of scope (considered and cancelled in v1). Reference files, canonical paths, and smells for these notations do not exist.
- **Archi-native `.archimate` format** (Eclipse EMF XML, Archi-specific) → not emitted in v1. The skill emits OEF XML only — tool-neutral and readable by every major ArchiMate® tool. Architects who want Archi-specific canvas features (custom figures, visual grouping, canvas styling presets) model those in Archi directly after import; the skill's Review mode will still parse the OEF export.
- **Business, Motivation, and Strategy layer extraction from source code or IaC** → reference §7.2; these layers are forward-only by design. Extract emits typed stubs marked `FORWARD-ONLY — architect fills in`; the architect is responsible for populating them.
- **Physical Layer extraction** → not attempted in v1; forward-only.
- **Runtime observation of architecture** (live topology from deployed resources) → static signals only — project files, IaC, workflow definitions. Drift against a live Azure subscription is not in scope.
- **Interactive layout debugging, full relationship-matrix source provenance, mainstream tool compatibility proof, and multi-evidence recovery** → deferred backlog. Do not present debugger export, Appendix B matrix execution, mainstream-tool compatibility evidence, or multi-evidence recovery as shipped behaviour.
- **Governance, approval, or review-board workflow** → the skill produces and checks diagrams; it does not run the architectural governance process around them.
- **Project documentation packaging** → out of scope. Consuming projects decide where generated artefacts live, which README rows or galleries exist, which PNG/SVG renders are published, and which CI jobs validate those project packages. When the user explicitly requests renders, this skill can produce PNG deployment artefacts from OEF via the bundled Archi script, but it does not design the consuming project's publication package unless asked.
- **Publication readiness of a repo-specific docs package** → out of scope unless the user explicitly asks for that project packaging review. The skill's default success criterion is OEF/model/view quality, not render-gallery completeness.

## Modes

Four modes — deliberately distinct from `responsive-design` because Extract (code → diagram) is a first-class, load-bearing operation for this skill.

### Build mode

**Use for:** producing a new ArchiMate® diagram from architect intent.

**Triggers:** "design the architecture for …", "model the …", "sketch an ArchiMate® view of …", "build a capability map / application cooperation / service realization / technology usage / migration view for …", "draw how … fits in the enterprise".

### Extract mode

**Use for:** lifting an ArchiMate® diagram from existing code, IaC, and workflow definitions — the reverse direction of Build.

**Triggers:** "lift architecture from the repo", "extract an ArchiMate® diagram from this solution", "reverse-engineer the architecture", "what does this codebase look like in ArchiMate®", "generate an Application Cooperation view from the `*.csproj` set".

**Refusal condition.** Extract is refused if the requested layers are entirely forward-only (Business / Motivation / Strategy / Physical) — the skill explains which layers are extractable and suggests narrowing the request.

### Review mode

**Use for:** reviewing an existing ArchiMate® model against the reference — *professional readiness* (is this model-valid, diagram-readable, or review-ready?), *artefact well-formedness* (does the OEF XML conform to ArchiMate® 3.2?), *render artefacts* (when the user requests PNGs or visual inspection), and *drift* (does the model still reflect the current code and IaC?).

**Triggers:** "review this ArchiMate® model", "check `…oef.xml` against the standard", "is this architecture model well-formed", "is this architecture diagram professional / review-ready", "render this architecture model", "generate PNGs for this OEF", "refresh the architecture renders", "has the architecture drifted from the code", "drift check on `docs/architecture/<feature>.oef.xml`".

Review has four sub-behaviours, dispatched on inputs:
- **Artefact review** — a `.oef.xml` file alone → ArchiMate® 3.2 well-formedness + professional-readiness pass + `AD-*` / `AD-Q*` smell catalog per reference §8.
- **External validation handoff** — a `.oef.xml` plus supplied Archi import / Validate Model / schema findings → load `references/procedures/external-validation-handoff.md` before the readiness rollup.
- **Render request** — a `.oef.xml` file + a request for PNGs / rendered views / visual inspection → source-geometry gate, then `references/scripts/archi-render.sh` when Archi is installed, jArchi script support is available, and an X display is available. The render script imports the OEF, runs the bundled Validate Model jArchi script, and only then creates the PNG report; `ARCHI_VALIDATE_MODEL: INVALID` findings are render blockers, while `ARCHI_VALIDATE_MODEL: WARN` findings are surfaced as validation evidence. When PNGs are produced, validate blank/tiny/cropped/baseline-drift signals with `references/scripts/arch-layout.sh validate-png` per `references/procedures/rendered-png-validation.md`. Archi is a weak dependency: if prerequisites are missing, report the blocker and do not use a fallback renderer.
- **Drift detection** — a `.oef.xml` file + the current code/IaC at the canonical locations (§ project assimilation) → delta report (elements added / removed / changed since the model was last aligned).

### Lookup mode

**Use for:** a specific, narrow question about the ArchiMate® notation itself.

**Triggers:** "what's the difference between Business Function and Business Process", "which ArchiMate® relationship connects an Application Component to an Application Service", "is Flow valid between Motivation elements", "what's the OEF `xsi:type` for a Strategy Capability", "can a Business Process have a Location".

**Default.** If the request is ambiguous between modes, ask. If the user says "design X architecture" without attaching artefacts, assume Build. If they attach code/IaC without an existing diagram, assume Extract. If they attach a diagram, assume Review. If it's a narrow factual question, assume Lookup.

## Render polish / all-modes iteration

Use this loop when the user asks to polish an existing canonical OEF until the
rendered diagrams are visually pristine, or otherwise explicitly asks to
iterate across all modes for render quality. This is mode composition, not a
fifth mode.

**Sequence per iteration:**

`Review -> Extract -> Build -> Lookup -> render/compare`.

1. **Review** the current OEF first: run artefact review,
   `validate-oef-layout.sh`, and render all views when available; record
   `AD-Q*`, `AD-L*`, `AD-B-*`, and render findings by view id.
2. **Extract** only for source truth: rerun discovery plus applicable lifting /
   drift procedures, and do not invent forward-only content.
3. **Build** the minimal layout/model patch using the layout strategy and
   professional-readiness procedure, preserving identifiers and architect
   placements unless Review proves they are defective.
4. **Lookup** only for bounded notation, relationship, coverage, or reverse
   lookup questions; Lookup does not mutate the model.
5. **Render and compare all artifacts:** rerun the source-geometry gate,
   regenerate every requested PNG with `archi-render.sh` (including its bundled
   jArchi Validate Model step), validate PNGs with
   `arch-layout.sh validate-png`, inspect all outputs, and compare source plus
   render snapshots against the committed baseline. Missing Archi, `DISPLAY`,
   jArchi script support, or script prerequisites are disclosed exactly; project
   render artifacts are updated only when the user asked or the project already
   commits the architecture render package.

**Stop condition:** stop only when the source-geometry gate passes, every
rendered view passes visual inspection, no unresolved blocker/warn `AD-L*`,
`AD-B-*`, or `AD-Q*` finding caps the requested quality level, drift findings
are either resolved or explicitly documented as architect-owned, and the final
source/render snapshot diff contains only intentional changes. If any condition
fails, start the next iteration from Review with the newly generated OEF.

## Extensions

The skill ships without framework extensions in v1. **Per-stack lifting rules live in `references/procedures/`, not in `extensions/`.** They are consulted (read on demand) when Extract runs — the harness's Skill tool loads `SKILL.md` only; nested procedure files require an explicit `Read` tool call before they can inform the agent. The split between procedures is by *input source* (code / IaC / workflow), not by *target stack choice*.

| Procedure | Applies to | Used by |
|---|---|---|
| `references/procedures/lifting-rules-dotnet.md` | .NET solutions, Azure Functions (isolated-worker), Blazor WebAssembly | Extract → ArchiMate® Application Layer |
| `references/procedures/lifting-rules-bicep.md` | Bicep IaC | Extract → ArchiMate® Technology Layer (Nodes, System Software, Communication Network, Path, Artifact) |
| `references/procedures/lifting-rules-gha.md` | GitHub Actions workflow files | Extract → ArchiMate® Implementation & Migration Layer (Work Package, Deliverable, Implementation Event, Plateau) |
| `references/procedures/lifting-rules-process.md` | Durable Functions orchestrators and Logic Apps workflow definitions (when present) | Extract → ArchiMate® Business Layer (Business Process, Event, Interaction only) with per-element `LIFT-CANDIDATE` markers; reverse Lookup consumes the same `source=` attribute. UI route lifting is deferred — §9.3 Process-rooted modality UI Application Component and Application Interface are hand-authored by the architect per the Blazor idiom in reference §9.3 |
| `references/procedures/process-view-emission.md` | Any feature whose model contains Business Process / Event / Interaction elements | Build step 3 (when diagram kind is §9.7 or §9.3 and pre-flight Q5 process scope is `all-processes-in-feature` or `multi-feature`) and Extract step 3 (whenever `lifting-rules-process.md` emitted any element) → emit one §9.7 Business Process Cooperation view per feature plus §9.3 Service Realization coverage per distinct realization story; Review restates its rules as `AD-B-11` / `AD-B-12` / `AD-B-13` / `AD-B-14` checks |
| `references/procedures/seed-views.md` | Extract outputs with forward-only Strategy, Motivation, or Business Service stubs | Extract step 3/4 → emit FORWARD-ONLY Capability Map and Motivation seed views so architect-owned stubs are visible in the diagram canvas, not only in raw `<elements>` |
| `references/procedures/drift-detection.md` | Any diagram + code pair at canonical paths | Review → drift sub-behaviour (including process drift `AD-DR-11` / `AD-DR-12`) |
| `references/procedures/layout-strategy.md` | Any view being built or extracted | Build / Extract → backend-neutral OEF geometry policy: preserve architect geometry, build a normalized layout request, select viewpoint policy, choose backend or fallback, route/gloss, normalize generated/mixed views, and validate final OEF quality |
| `references/procedures/layout-backend-contract.md` | Build / Extract when generated or repaired geometry is needed | Defines the backend-neutral JSON Schema request/result shape for nodes, edges, hierarchy, ports, locks, semantic bands, metrics, and validation handoff |
| `references/procedures/layout-policies-by-viewpoint.md` | Build / Extract after diagram kind is known | Selects the visual grammar for Capability Map, Application Cooperation, Service Realization, Technology Usage, Migration, Motivation, and Business Process Cooperation views |
| `references/procedures/routing-and-glossing.md` | Build / Extract routing and Review route repair | Defines port-aware orthogonal routing, route-only repair, lane reservation, rip-up/reroute, post-route glossing, and the shipped `route-repair` command |
| `references/procedures/layout-fallback.md` | Build / Extract when no suitable backend is available | Fallback deterministic layered layout for small generated directed views; preserves prior deterministic conventions without treating them as a universal layout engine |
| `references/procedures/professional-readiness.md` | Any OEF model or view being built, extracted, or reviewed | Build / Extract final pass and Review artefact pass → classify `model-valid` / `diagram-readable` / `review-ready`, curate extraction noise, and emit `AD-Q*` professional-quality findings |
| `references/procedures/external-validation-handoff.md` | Read only when the user supplies Archi import errors, Archi Validate Model output, `xmllint --schema` output, or another conformant tool's validation report | Consume downstream tool findings as first-class evidence before readiness claims |
| `references/procedures/rendered-png-validation.md` | Review render requests and explicit render-polish loops after PNGs exist | Java™ ImageIO-based `validate-png` checks for blank, tiny, cropped, excessive-whitespace, and baseline-drift failures; ImageMagick is optional diagnostics only |
| `references/scripts/validate-oef-layout.sh` | Any local OEF file with materialized views | Build / Extract final self-check and Review artefact pass → executable source-geometry gate for `AD-L2`, `AD-L3`, `AD-L8`, `AD-L10`, `AD-L11`, `AD-L13`, and `AD-L15`; complements render inspection because cropped PNG exports can hide off-origin source geometry and explicit connector lanes can hide stacked-arrow / fan-out defects |
| `references/scripts/validate-model.ajs` | Archi render/load runs after OEF import and before HTML report generation | jArchi Validate Model step used by `archi-render.sh`; emits `ARCHI_VALIDATE_MODEL: INVALID` for relationship legality, missing visual references, and visual-connection endpoint defects, and `ARCHI_VALIDATE_MODEL: WARN` for empty views, unused elements, unused relationships, and possible duplicate elements |
| `references/scripts/archi-render.sh` | Any local OEF file when the user requests rendered diagrams, visual inspection, or refresh of PNG render artefacts | Review render-request sub-behaviour, explicit render-polish loop, and Build / Extract final self-check when a renderer is requested → validate XML well-formedness, import the OEF through Archi's headless CLI, run the bundled jArchi Validate Model script, then render every OEF view to PNG. Archi is a weak dependency with no fallback renderer; missing Archi / jArchi script support / `DISPLAY` / tool prerequisites are reported as "render inspection not run"; invalid Validate Model findings are render blockers, and warnings are reported without failing PNG generation |
| `references/scripts/arch-layout.sh` | Build / Extract layout contract checks, strict result-quality gates, OEF materialization, layout policy diagnostics, and layout provenance output; Review route repair, global polish, generated layout smoke, or PNG validation | Launches the packaged Java™ 21 runtime from `references/bin/arch-layout.jar` for `--version`, `validate-request`, `validate-result`, `layout-elk`, `route-repair`, `global-polish`, `materialize-oef`, `layout-provenance`, and `validate-png` |
| `references/scripts/package-arch-layout.sh` | Plugin release packaging or runtime refresh after Java™ source changes | Runs the Gradle test suite, builds the self-contained runtime JAR, copies it to `references/bin/arch-layout.jar`, and prints included/excluded package evidence |
| `references/schemas/layout-request.schema.json` / `references/schemas/layout-result.schema.json` / `references/schemas/layout-provenance.schema.json` | Backend request/result validation, runtime-honored layout policy diagnostics, and provenance reporting | Draft 2020-12 JSON contracts for generated layout, route repair, global polish handoff, and per-view layout provenance |

Smells are namespaced `AD-*` (reference §8), with sub-namespaces `AD-L*` for layout, `AD-B-*` for process-flow artefacts (§9.7 / §9.3), and `AD-Q*` for professional OEF/view quality. Use [`references/smell-catalog.md`](references/smell-catalog.md) as the compact code-to-reference index when emitting or interpreting findings. There are no framework-specific smell namespaces in v1 — architecture-design findings are notation-level, not stack-level.

Regression fixtures live under `references/fixtures`. Read [`references/fixtures/README.md`](references/fixtures/README.md) before validating the corpus or acceptance bar. Read `references/fixtures/render-quality-gate` for static `AD-L*` gate changes; `references/fixtures/layout-backend-contract`, `references/fixtures/layout-contract`, or `references/fixtures/layout-elk-java` for schema/generated-layout contract changes; `references/fixtures/layout-elk-realistic` when changing the request -> `layout-elk` -> `materialize-oef` -> source-geometry gate loop for realistic nested OEF contexts; `references/fixtures/route-repair` for route-only repair changes; `references/fixtures/global-polish` for bounded movement changes; `references/fixtures/materialize-oef` for layout-result to OEF handoff changes; and `references/fixtures/rendered-png` for `validate-png` changes.

Adding a new input source later (Terraform, Azure Pipelines YAML, ARM templates, Kubernetes manifests) means adding a new procedure file, not an extension.

## Canonical path

Diagrams written and read by the skill live at a single canonical path:

```
docs/architecture/<feature>.oef.xml
```

The path is the coupling mechanism for the sibling design skills (`responsive-design` and `api-design`). Their Review mode checks this path, and if a matching diagram exists, dispatches to `architecture-design` Review for drift detection.

`<feature>` is a short snake-case or kebab-case identifier — `checkout`, `order-to-cash`, `auth`, `ingestion-pipeline`. One file per feature; the file may contain multiple views inside its `<views>/<diagrams>` block (Capability Map, Application Cooperation, Technology Usage, etc. for the same feature). The skill suggests the filename; the architect can override.

## Render artifacts

Rendered PNGs are **deployment / publication artifacts derived from OEF**, not the architecture source of truth. OEF XML remains the model; PNGs exist so humans and documentation packages can inspect the views without opening an ArchiMate® tool.

When the user asks to render, refresh renders, inspect rendered views, or
produce PNGs:

1. Run the source-geometry gate first when a local OEF path exists.
2. Invoke [`references/scripts/archi-render.sh`](references/scripts/archi-render.sh) with the requested OEF path and any caller-supplied `--archi-bin`, `--cache-root`, `--config`, `--output-root`, or `--validate-model-script` settings.
3. Treat Archi and jArchi script support as weak dependencies. The script has no fallback support and the skill must not invent one; if Archi, jArchi script support, `DISPLAY`, `xmllint`, the Validate Model script, or another prerequisite is missing, disclose the exact failure and keep visual render inspection at `not run`. If the bundled Validate Model step reports `INVALID`, treat it as a render blocker. If it reports `WARN`, keep the render output but map the warnings through external-validation handoff before claiming readiness.
4. If rendering succeeds, inspect every emitted PNG before claiming visual quality; do not sample views. Run `references/scripts/arch-layout.sh validate-png --image <rendered.png> --result <result.json>` for invariant checks, and add `--baseline <prior.png> --tolerance <ratio>` when a previous render exists and the user requested comparison.
5. Classify changed PNGs, README rows, galleries, or provenance text as
   `documentation/render inventory change`. Do not mark a render-only refresh as
   a semantic model change unless `<elements>` or `<relationships>` changed.
6. **Render gate** (per [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md)
   §Quality verdict — *Render gate*). When the user has requested visual
   quality and render did not run, cap changed views at `model-valid` until
   render runs. Unchanged views inherit their prior classification.
7. **Render contracts disclosure** (per "Project assimilation" §Discovery pass
   step 8). When the current run produces an OEF change and the discovery pass
   detected committed render artifacts or gallery sections, the footer notes
   that those project artefacts may need refresh. The skill does not
   automatically update committed renders or gallery prose unless the user
   explicitly asks (Non-goals) or the explicit render-polish loop is in scope.

## Pre-flight (build & extract & review)

Before producing or reviewing a diagram, confirm the following. If the user hasn't supplied them, ask — don't invent answers:

1. **Diagram kind.** Capability Map / Application Cooperation / Service Realization / Technology Usage / Migration / Motivation / Business Process Cooperation (reference §9). Default: the skill offers the closest fit based on the user's prompt; asks if two are plausible. Diagrams outside the seven supported kinds are declined. Each kind's English label and OEF `viewpoint=` attribute value are identical.
2. **Layer scope.** Which ArchiMate® layers is the diagram working with? Default: Core Framework (Business + Application + Technology) unless the diagram kind implies Strategy (Capability Map), Motivation (Motivation), or Implementation & Migration (Migration). Crossing extensions into a Core view without cause triggers `AD-7`.
3. **Extraction posture (Extract mode only).** Which input sources to read — .NET solution, Bicep, GHA workflows, `host.json` / `staticwebapp.config.json`, and Durable Functions orchestrators / Logic Apps workflow definitions (when present — these enable Business Process / Event / Interaction lifting per reference §7.4 with `LIFT-CANDIDATE` markers; UI routes are not lifted in v1). Default: all of the above when present. Fully forward-only layers (Motivation / Strategy / Physical) and the forward-only subset of Business (Actor / Role / Collaboration / Object / Contract / Product / Service / Function) are emitted as typed stubs per reference §7.
4. **Feature name.** The `<feature>` slug that becomes the canonical filename. Default: derived from the user's prompt or the solution name.
5. **Process scope (Build mode only, when diagram kind is §9.7 or §9.3).** Which Business Processes does this work cover?
   - `single-process` — only the named process. Suppresses the fan-out contract; the skill emits exactly the one view the architect asked for.
   - `all-processes-in-feature` *(default when prompt mentions "the feature" / "the project" without naming one process)* — applies the full process-view emission contract per [`references/procedures/process-view-emission.md`](references/procedures/process-view-emission.md).
   - `multi-feature` — architect specifies the feature list explicitly; the contract applies per feature.

   Default heuristic: if exactly one Business Process is named in the prompt, default to `single-process`; otherwise default to `all-processes-in-feature`. Extract mode does not ask this question — Extract operates on whatever is liftable in the current source-tree slice, and always applies the emission contract when [`lifting-rules-process.md`](references/procedures/lifting-rules-process.md) lifted any element.
6. **Artifact quality target.** Which level is expected: `model-valid`, `diagram-readable`, or `review-ready`? Default for Build / Extract is `diagram-readable`; default for Review is to assess whether the model reaches `review-ready`. This is an OEF/model/view quality target only, not a project README, render, gallery, or CI package target.
7. **Change classification.** For OEF edits, classify the intended work before
   editing:
   - `semantic model change` — add/remove/rename elements, relationships, or
     relationship endpoints.
   - `view geometry change` — move nodes, resize nodes, reroute bendpoints, add
     or suppress view-specific `<connection>` entries for relationships already
     present in the model.
   - `documentation/render inventory change` — update view documentation,
     README/gallery rows, committed PNG/SVG snapshots, or provenance notes.

   Default: infer the smallest matching set from the request and restate it in
   the footer. Hiding an existing relationship from one view is a view geometry
   change, not a semantic model change, when the relationship remains under
   `<relationships>` and the omission reason is documented.
8. **Render request.** Did the user ask for PNG renders, visual render
   inspection, or render snapshot refresh? Default: no. When yes, use
   `references/scripts/archi-render.sh`; ask only for missing paths or explicit
   output location when the default `docs/architecture/<feature>.oef.xml` /
   `.cache/archi-views` convention is insufficient. Do not substitute another
   renderer if Archi is unavailable.
9. **External validation evidence.** If supplied, load `references/procedures/external-validation-handoff.md`; if the user asks about tool-reported findings but omits the report, ask for it.
10. **Layout intent.** Select `preserve-authored`, `route-repair-only`, `generated-layout-recreate`, or `global-reflow` per [`references/procedures/layout-strategy.md`](references/procedures/layout-strategy.md) §Layout decision record. "Recreate", "regenerate", "generate all diagrams", "rebuild the views", or "use the improved layout backend" selects `generated-layout-recreate`; prior coordinates are comparison input, not locks, unless explicitly locked. Backup before overwrite and include the per-view backend report.

If any answer deviates from defaults (e.g., "include Physical Layer for this data-centre diagram"), state the deviation explicitly in the output footer.

## Project assimilation (before build, extract, and review)

**Direction is one-way: the project is assimilated to the reference, not the reference to the project.** The reference's layer discipline (§2.1), aspect rules (§2.3), Core-vs-extension defaults (§2.4), and relationship well-formedness (§2.5 and ArchiMate® 3.2 Appendix B) are non-negotiable. Assimilation means discovering what the project ships so output (a) aligns to any existing diagram at the canonical path, (b) reuses project names and feature labels, and (c) surfaces drift as legacy debt rather than silently ignoring it.

Before producing or reviewing a diagram, run the discovery pass below. Keep detection lightweight — canonical locations only. If nothing found, assume greenfield and ask the architect for intent.

### Discovery pass (all modes)

1. **Existing model at the canonical path.** Check `docs/architecture/<feature>.oef.xml` for the feature in scope. If present, parse it and record the element identifiers, names, relationships, and view coordinates — Extract and Build both respect existing identifiers (no gratuitous churn). If absent, treat as greenfield for this feature.
2. **.NET solution surface.** Grep for `*.sln`, `*.csproj`, `Microsoft.Azure.Functions.Worker` (Azure Functions isolated-worker; maps to Application Component + hosted-on Technology Node), `Microsoft.NET.Sdk.BlazorWebAssembly` (Blazor WASM standalone; Application Component), `AddInteractiveWebAssemblyComponents` / `AddInteractiveWebAssemblyRenderMode` with `.Client` project (Blazor Web App `.Client`), top-level class libraries (Application Component or a shared `Artifact` depending on packaging).
3. **Azure Functions `host.json`.** Each function's bindings surface Application Interfaces; the host file itself implies an Azure Functions runtime (System Software) on an App Service / Function App (Node).
4. **Static Web App config** (`staticwebapp.config.json`). Maps to an Azure Static Web Apps Node hosting a Blazor or static Application Component; routes and auth providers map to Application Interfaces.
5. **Bicep IaC.** Grep `*.bicep` for Microsoft.Web/sites, Microsoft.Web/serverfarms, Microsoft.DocumentDB/databaseAccounts, Microsoft.Storage/storageAccounts, Microsoft.KeyVault/vaults, Microsoft.Network/virtualNetworks, Microsoft.Network/privateEndpoints, Microsoft.OperationalInsights/workspaces, Microsoft.Insights/components, Microsoft.ManagedIdentity/userAssignedIdentities. Each maps to a Technology Layer element per `references/procedures/lifting-rules-bicep.md`.
6. **GitHub Actions workflows.** Grep `.github/workflows/*.yml` for deploy / release jobs — each becomes a Work Package; environments become Plateaus; successful deploys become Implementation Events.
7. **Solution topology signals** — project reference graph (`<ProjectReference>` in `.csproj`) maps to Serving / Composition / Realisation relationships within the Application Layer.

8. **Repo render contracts (disclosure-only).** Detect — but do not unilaterally update — committed render artifacts and gallery conventions:
   - Committed PNG / SVG renders under `docs/architecture/**/*.png`, `docs/architecture/**/*.svg`, `docs/diagrams/**/*.png`, or sibling render-output directories the architect has chosen (look for filenames matching `<feature>*.png` next to `<feature>.oef.xml`).
   - README architecture-gallery sections — grep `README.md`, `docs/README.md`, or `docs/architecture/README.md` for headings or tables naming the canonical OEF feature(s) currently in scope.
   - Repo render commands — grep `package.json` `scripts`, `Makefile`, `Justfile`, `.github/workflows/*.yml`, or `azure-pipelines*.yml` for invocations of `archi-render.sh`, `archi`, `archi-cli`, or equivalent renderer commands.
   Report what was found in the `Project assimilation:` footer block under a `Render contracts detected:` sub-block with three keys: `committed renders`, `gallery sections`, `render commands`. When the current run produces an OEF change and committed renders or gallery sections are detected, the footer notes "OEF changed; <n> committed renders / <m> gallery sections may need refresh — architect decides whether to update them in this run." This is disclosure, not auto-update; updating committed render artifacts and gallery prose is in scope only when the user explicitly asks (per the *Non-goals* section) or the user has invoked the explicit render-polish loop.

### Forward-only layers in discovery

The discovery pass **never produces Business, Motivation, Strategy, or Physical elements from source code.** These layers are reference-§7.2 forward-only. If an existing diagram at the canonical path contains them, the skill reads them verbatim and preserves them across Extract re-runs; the architect owns their content.

### Mapping existing infrastructure to reference rules

Reuse is conditional on **substantive compliance with ArchiMate® 3.2**, not presence. For each discovered element in an existing diagram:

| Discovered in existing diagram | Reuse when | Flag when |
|---|---|---|
| Layer assignment per element | Element is in the correct layer per §3–4 | Misplaced element (e.g., a Service labelled Business but used as Application Service) — `AD-1` / `AD-3` |
| Aspect per element | Active / Behaviour / Passive distinction clean | Double-stereotyped box — `AD-3` |
| Relationship between two elements | Valid per Appendix B Relationships Table | Invalid relationship — `AD-2` |
| Identifier ↔ `<name>` semantics | Identifier slug agrees with `<name>` content | Mismatch — `AD-8` |
| Realisation chain | Business Service → Application Service → Application Component, complete for the scope | Missing intermediate — `AD-6` |
| Forward-only markers | `FORWARD-ONLY — architect fills in` header present for Business / Motivation / Strategy sections | Forward-only layer populated without the marker — `AD-14` |

**Name adoption is always fine.** If the project calls its checkout function `CheckoutFunction` and an existing ArchiMate® diagram labels the Application Component `Checkout Service`, adopt the existing diagram label — the rule is layer and relationship discipline, not spelling. Extract preserves existing labels; Build defaults to project names with architect-editable suggestions.

**Substantive non-compliance is never fine.** If an existing diagram shows a Business Process *realising* a Technology Node (reference §5.5, Appendix B), Build and Extract do not propagate the broken relationship into new output — the finding is reported and the correct relationship is emitted.

### Footer additions

All mode footers gain a `Project assimilation:` block listing: existing diagram reused, element labels preserved, and any drift or well-formedness issues flagged. Example:

See [`references/output-format.md`](references/output-format.md) §Project assimilation block for the canonical example, including the `Render contracts detected:` sub-block and the OEF-changed refresh note.

## Build mode workflow

0. **Dispatch.** Confirm Build mode. `Read` and run [`references/procedures/self-check.md`](references/procedures/self-check.md) to verify required reference files, procedures, and scripts are present and runnable; record the self-check outcome for the footer. Run the pre-flight above. Announce the diagram kind, layer scope, and change classification.

1. **Principles scan.** Read reference [§2 Principles](../../docs/architecture-reference/architecture.md#2-principles). Output must not violate: §2.1 layer separation, §2.3 aspect rules, §2.4 Core-vs-extension discipline, §2.5 relationship well-formedness.

2. **Pick the diagram kind from reference §9.** The kind fixes the element palette and prevents layer soup (`AD-1`). Re-use an existing diagram at the canonical path when one exists; otherwise create fresh.

3. **Compose elements and relationships.**
   - Element types from reference §4 (per layer).
   - Relationship types from reference §5.
   - Well-formedness per ArchiMate® 3.2 Appendix B — never emit a relationship not found in the table for the given element-pair.
   - OEF XML serialisation per reference §6. Emit every element with its correct `xsi:type` from the ArchiMate® 3.2 element catalog; emit every relationship with its correct `xsi:type` per ArchiMate® 3.2 Appendix B.
   - View-specific relationship curation is valid only after the relationship
     remains in the model. If drawing the relationship would repeat the same
     story already carried by nesting, a realisation spine, or a shared
     process-rooted view, omit or hide that view connection and document the
     relationship id plus reason. Do not delete the model relationship unless
     the architecture semantics actually changed.
   - **If diagram kind is §9.7 or §9.3 and pre-flight Q5 process scope is `all-processes-in-feature` or `multi-feature`**, `Read` and apply [`references/procedures/process-view-emission.md`](references/procedures/process-view-emission.md). The procedure emits the full §9.7 view plus §9.3 Service Realization coverage per distinct realization story — consolidating same-story process roots instead of emitting near-identical drill-downs. Step 4's layout invocation runs once per emitted view.

4. **Layout and naming** per reference §6.4-6.7. `Read` [`references/procedures/layout-strategy.md`](references/procedures/layout-strategy.md) before invoking it. For every emitted view, build a layout decision record containing view id, viewpoint, layout intent, backend eligibility, selected command or fallback, request validation state, result validation state, materialization state, and skip/blocker reason. Preserve architect geometry only when the layout intent is `preserve-authored` / `route-repair-only`, the user explicitly locked geometry, or validation proves the existing geometry is the only acceptable policy. A `generated-layout-recreate` request does not treat all prior coordinates as locked. Read only the sub-procedures whose conditions apply (backend contract, viewpoint policy, fallback, routing/glossing). Validate final OEF geometry before claiming `diagram-readable` or `review-ready`, and do not treat the backend name as quality evidence.
   Identifiers are `id-<slug>` in lowercase-with-hyphens per §6.6; `<name>` values follow the element-type conventions in §6.7.
   Then `Read` and apply [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md): every emitted view must name the architecture question it answers, remove or group extraction noise, and be classified as `model-valid`, `diagram-readable`, or `review-ready`. Before leaving this step, materialize every view with `<node>` and `<connection>` geometry; never leave a generated view as element / relationship definitions only.

5. **Write the canonical file.** Default location `docs/architecture/<feature>.oef.xml`. If an architect has named a specific path, honour that. Do **not** emit `propid-archi-model-banded` or any other layout marker on the `<model>` element; model-root `<properties>` is invalid OEF and triggers `AD-17`. Emit a default Dublin Core `<metadata>` block per reference §6.1a, with `dc:title` set to the feature name and `dc:creator` set to `architecture-design <plugin-version>` (read the live version from `souroldgeezer-design/.claude-plugin/plugin.json`); namespace constraint per `MetadataType`'s `<xs:any namespace="##other"/>` is non-negotiable (`AD-16`). **Emit all top-level `<model>` children in OEF sequence per reference §6** — `name → documentation → metadata → elements → relationships → organizations → propertyDefinitions → views`. `<propertyDefinitions>` follows `<organizations>` and immediately precedes `<views>`.

6. **Self-check against reference §10 and the professional-readiness procedure** before declaring done. When the OEF exists as a local file, run [`references/scripts/validate-oef-layout.sh`](references/scripts/validate-oef-layout.sh) against it before visual render inspection; treat every emitted line as a source-geometry `AD-L*` finding and fix blocking / warning layout findings before claiming `diagram-readable`. Each checklist item carries `[static]`, `[visual]`, or `[runtime]` verification-layer tags. Walk each item:
   - `[static]` — verify against the diagram source just produced.
   - `[external]` — when downstream validation evidence is supplied, load [`external-validation-handoff.md`](references/procedures/external-validation-handoff.md), map findings to `AD-*` evidence, disclose mapped / unresolved / unmapped counts, and cap quality as that procedure defines.
   - `[visual]` — when rendering is requested and Archi is available, run
     [`references/scripts/archi-render.sh`](references/scripts/archi-render.sh),
     then inspect all emitted PNGs for connector-through-node, stacked connector
     lanes, orphan nodes, wide empty layer gaps, local fan-out crisscross, long
     peripheral bus routes, duplicate visible story paths, misleading boundary
     crossings, and ambiguous nested ownership. Do not sample. If Archi or
     jArchi script support, the Validate Model script, or another script
     prerequisite is unavailable, disclose "render inspection not run" with the
     blocker; do not weaken static `AD-L*` findings from the
     source-geometry gate.
     **Render gate.** When the user has requested visual quality (explicit
     render request, render-polish loop, or `[visual]` self-check requested in
     pre-flight) and render did not run, cap changed views at `model-valid` per
     [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md)
     §Quality verdict — *Render gate*. Unchanged views inherit their prior
     classification. The footer reports the gate state.
   - `[runtime]` — verify against the current `.csproj` / Bicep / workflow state; if out of scope, mark "source-aligned; runtime verification required."
   If any `[static]` or supplied `[external]` item fails, fix or explicitly
   lower the claimed quality before delivering.
   Classify quality **per `<view>` first** per [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md) §Quality verdict, then derive the artifact rollup as the worst-view minimum. For each view also derive **authority** (§Authority levels in the same procedure): `lifted-from-source` by default when every element resolves to a current source; `forward-only-or-inferred` when any element comes from a `FORWARD-ONLY` block or unconfirmed `LIFT-CANDIDATE`; `architect-approved` or `stakeholder-validated` only when the view's `propid-authority` property (reference §6.4b) is set. Authority does not gate readiness — both axes are reported independently. Emit the per-view readiness matrix (with Authority column) in the self-check block when the artifact contains more than one materialized view; single-view artifacts may use a single-row matrix. State whether architecture semantics changed. Do not claim `review-ready` for a view if any `AD-Q*`, `AD-L2`, `AD-L3`, `AD-L4`, `AD-L11` through `AD-L20`, `AD-B-*`, `AD-6`, `AD-2`, `AD-18`, `AD-20`, `AD-21`, or unresolved external validation finding remains for that view, and do not claim `review-ready` for the artifact rollup if any model-level blocker (`AD-15`, `AD-17`, `AD-14`, `AD-14-LC`, `AD-16`, `AD-22`) remains unresolved. Emit `AD-Q11` for any view whose `propid-authority` override claims `architect-approved` or `stakeholder-validated` while still containing unresolved `FORWARD-ONLY` or `LIFT-CANDIDATE` content.

7. **Emit footer disclosure.**

## Extract mode workflow

0. **Dispatch.** Confirm Extract mode. `Read` and run [`references/procedures/self-check.md`](references/procedures/self-check.md) to verify required reference files, procedures, and scripts are present and runnable; record the self-check outcome for the footer. Run the pre-flight above. Confirm which layers to extract (default: all three extractable — Application / Technology / Implementation & Migration) and state the change classification.

1. **Refuse if scope is entirely forward-only.** If the architect has asked for Business / Motivation / Strategy / Physical only, refuse with:
   - the reference §7.2 explanation of why these layers are forward-only;
   - a suggestion to run Build mode with the architect's intent as input.

2. **Run the discovery pass (above).** Record what was found — solution surface, Bicep resources, workflows, existing diagram at the canonical path.

3. **Read each applicable procedure file, then invoke it.** The Skill tool that loaded this `SKILL.md` does not auto-inject nested files; each procedure must be `Read` explicitly before its rules can inform the agent.
   - `references/procedures/lifting-rules-dotnet.md` → Application Layer elements + intra-Application relationships (when .NET solution sources are present).
   - `references/procedures/lifting-rules-bicep.md` → Technology Layer elements + Application-to-Technology Assignment / Realisation relationships (when Bicep is present).
   - `references/procedures/lifting-rules-gha.md` → Implementation & Migration Layer elements (when `.github/workflows/*.yml` is present).
   - `references/procedures/lifting-rules-process.md` → Business Process / Event / Interaction `LIFT-CANDIDATE` emission (when Durable Functions orchestrators or Logic Apps workflows are present).
   - `references/procedures/process-view-emission.md` → §9.7 cooperation view + §9.3 Service Realization coverage per distinct realization story (whenever `lifting-rules-process.md` emitted any element). Runs after `lifting-rules-process.md` (so it has elements to emit views for) and before `layout-strategy.md` (so layout sees the full view set).
   - `references/procedures/seed-views.md` → FORWARD-ONLY Capability Map and Motivation seed views whenever Extract emitted Strategy / Motivation / forward-only Business Service stubs. Runs after forward-only stubs exist and before `layout-strategy.md`.
   - `references/procedures/layout-strategy.md` plus its backend contract, viewpoint policy, routing/glossing, and fallback sub-procedures -> per-view layout decision records plus view placements and route repair. For `generated-layout-recreate`, run generated-layout handling for every eligible view even when prior geometry exists. For `global-reflow`, attempt route repair first for architect-authored views, then `global-polish` when route-only repair cannot reach the requested quality without broad movement. For `preserve-authored`, generate or repair only elements and connections not carrying valid architect-authored geometry in the prior diagram at the canonical path.
   - `references/procedures/professional-readiness.md` → final curation pass over the generated view set. Preserve traceability in the model, but do not leave a view as a raw inventory dump; every view must answer a stated architecture question.

4. **Emit forward-only stub blocks.** For Business, Motivation, and Strategy — even if the architect did not ask for them — emit a typed stub *only if the diagram kind requires them* (e.g., a Service Realization view without a Business Layer is incomplete). The stub carries the mandatory marker header (reference §7.3):

   ```xml
   <!--
   ==============================================================================
   FORWARD-ONLY — this layer was not extracted from source
   The architect must fill in: <layer name>
   The skill inferred suggestive placeholders from Application element labels
   ==============================================================================
   -->
   ```

   Placeholders are generated from Application Component names — e.g., an `Orders.Api` Component suggests a plausible Business Service label *Order Management*. The architect confirms or rewrites.

5. **Preserve existing model content.** If `docs/architecture/<feature>.oef.xml` exists, merge rather than overwrite: existing element identifiers, `<name>` values, `<documentation>`, valid element / relationship / view properties, stable view placements, and forward-only content are preserved; extracted elements are added, missing elements are removed (surfaced as drift findings in the footer). Do not preserve old connection bendpoints when a relationship is replaced, its source/target endpoints are inverted, the preserved route now crosses unrelated nodes, or the first / last preserved bendpoint sits inside the source / target node body; reroute and report `AD-L11` if no clean route exists. If preserving a model relationship but suppressing its visible connection in one view, record it as a view geometry change and document the relationship id plus rationale. If an existing file has a model-root `<properties>` block used for the old layout marker, omit it from newly-emitted output and report `AD-17` in Review. Layout conformance is checked directly from view geometry, not from a marker.

6. **Self-check against reference §10 and the professional-readiness procedure** as in Build, including the per-view readiness matrix from [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md) §Quality verdict. State the per-view classifications and the artifact rollup (worst-view minimum), plus any remaining modeling work required before the model can be called `review-ready`.

7. **Emit footer disclosure including the per-layer lift / stub breakdown** — which layers were lifted, which were stubbed, which sources were read, and the change classification.

## Review mode workflow

0. **Dispatch.** Confirm Review mode. `Read` and run [`references/procedures/self-check.md`](references/procedures/self-check.md) to verify required reference files, procedures, and scripts are present and runnable; record the self-check outcome for the footer. A missing `architecture.md`, `smell-catalog.md`, `validate-oef-layout.sh`, or applicable procedure must be reported as "not run (blocker)" in affected findings rather than silently skipped. Run pre-flight. Identify sub-behaviour:
   - Artefact review (diagram file alone, or diagram + architect asks "is this well-formed").
   - Drift detection (diagram + code/IaC at canonical locations, or architect asks "has this drifted").
   - Render request (diagram + user asks for PNGs, render refresh, or visual
     inspection).
   If multiple apply, run artefact review first, render second, then drift
   detection. When a diff or edit request is in scope, classify the observed
   changes as semantic model, view geometry, and/or documentation/render
   inventory.

### Artefact review

**Layout-severity dispatch.** Layout findings are evaluated from view geometry directly. There is no valid model-root layout marker. `AD-L11` is always `block`; `AD-L12` through `AD-L20` are readability blockers for `diagram-readable` and `review-ready` when they make layout communication unreliable, even when their finding severity is `warn`.

1. **Parse the `.oef.xml`** into elements (with `xsi:type`, identifier, name), relationships (with `xsi:type`, source, target), views and their node/connection placements. If a local file path is available, run [`references/scripts/validate-oef-layout.sh`](references/scripts/validate-oef-layout.sh) and include its `AD-L*` findings directly in the Review output; this catches `AD-L10` origin drift, `AD-L11` endpoint bendpoints inside endpoint boxes, `AD-L13` stacked lanes, and `AD-L15` local fan-out crossings even when a renderer crops the PNG to plausible bounds. If a view has no materialized element nodes, missing `x` / `y` / `w` / `h`, no relationship connections for its visual story, or duplicate `identifier` attributes in the OEF file, cap the artefact at `model-valid` and report it before judging layout polish.

2. **Consume external validation evidence when supplied.** Load [`external-validation-handoff.md`](references/procedures/external-validation-handoff.md) before the readiness rollup only when the user supplied Archi import / Validate Model / schema findings.

3. **Run professional-readiness review.** `Read` and apply [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md). Classify each `<view>` as `model-valid`, `diagram-readable`, or `review-ready`, then derive the artifact rollup as the worst-view minimum (capped at `model-valid` by any unresolved model-level blocker — `AD-15`, `AD-17`, `AD-14`, `AD-14-LC`, `AD-16`, `AD-22`). Emit the per-view readiness matrix as the lead block of the Review output ([`references/output-format.md`](references/output-format.md) §Review mode). Findings become `AD-Q*` smell codes from reference §8.

4. **Walk reference §10 checklist bucket by bucket.** For each item, inspect the diagram and record: pass / fail / not-applicable. Failures become findings with `AD-*` smell codes from reference §8.

4a. **Render on request.** If the user requested renders or visual inspection,
run `references/scripts/archi-render.sh` after static checks. Pass through
caller-provided `--archi-bin`, `--cache-root`, `--config`, `--output-root`, and
`--validate-model-script` when supplied. A missing Archi executable, missing
jArchi script support, missing `DISPLAY`, malformed XML, invalid Validate Model
finding, or script exit code is not a fallback opportunity; report the exact
command, failure, and "Visual render inspection: not run". Map Validate Model findings
through [`external-validation-handoff.md`](references/procedures/external-validation-handoff.md)
before the readiness rollup. Apply the render gate from
[`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md)
§Quality verdict — *Render gate*: when render did not run and visual quality
was requested, cap changed views at `model-valid` for this Review.

4. **Per-finding format.** Match the sibling-skill convention:

   ```
   [<AD-N>] <file>:<line or element identifier>
     layer:    static | runtime
     severity: block | warn | info
     evidence: <quoted XML fragment — element, relationship, or view node>
     action:   <suggested fix referencing reference §X and ArchiMate® 3.2 §/Appendix>
     ref:      architecture.md §<n.m> + ArchiMate® 3.2 §<chapter> / Appendix B
   ```

### Drift detection

1. **`Read` and invoke `references/procedures/drift-detection.md`.** The Skill tool loads `SKILL.md` only; the drift procedure must be `Read` explicitly before its rules can inform the agent. Once read, re-run the discovery pass from project assimilation against the current code/IaC and compare the discovered set to the diagram's element set.

2. **Report deltas as `AD-DR-*` findings** — elements added, elements removed, relationships changed. These findings carry `layer: runtime`.

3. **Suggest reconciliation.** For each drift finding, suggest either "update the diagram to match current code" (if code is the source of truth for that layer) or "update the code to match the diagram" (if the architect's model is intentional and code has drifted).

4. **Rollup.** After per-finding output, one paragraph summarising well-formedness health and drift summary.

5. **Emit footer disclosure.**

## Lookup mode workflow

0. **Dispatch.** Confirm Lookup. Identify sub-behaviour from the question shape:
   - **Notation Q&A** — "what does Assignment mean", "is a Business Process allowed to trigger an Application Event", "which Appendix B entry covers Serving between Component and Interface". Go to step 1a.
   - **Domain discovery** — "what processes exist in / for / around {feature}", "what business processes have we modelled". Go to step 1b.
   - **Reverse lookup** — "which process does {symbol | file | function | endpoint | UI component} belong to". Go to step 1c.

1a. **Notation Q&A — locate.** Grep reference for the concept (element type, relationship, diagram kind, OEF `xsi:type`, Appendix B entry). Load only the matched section.

1b. **Domain discovery — scan canonical paths.** Enumerate `docs/architecture/**/*.oef.xml`. Parse each file and filter views by diagram kind (§9.7 Business Process Cooperation or §9.3 Service Realization). Within filtered views, list each Business Process / Event / Interaction element with its `<name>`, owning view identifier, and the file path. If the question narrows to a feature area, filter by feature-file basename (e.g., "order-to-cash" → `docs/architecture/order-to-cash.oef.xml`). Return a ranked list — by feature proximity, then by number of incoming Triggering edges (entry-point processes first).

1c. **Reverse lookup — backend path.** If the symbol is a backend orchestrator / workflow: (i) locate the symbol via `Grep` / `Glob`; (ii) find the enclosing Durable Functions orchestrator (`[Function]` on a function whose trigger parameter is `TaskOrchestrationContext` / `IDurableOrchestrationContext`) or Logic Apps workflow (`workflow.json`, `*.logicapp.json`, or Bicep `Microsoft.Logic/workflows`); (iii) search `docs/architecture/**/*.oef.xml` for a Business Process element whose preceding XML comment carries `LIFT-CANDIDATE source=<matching path>` — or whose `<name>` (case-insensitive, whitespace-trimmed) matches the orchestrator / workflow name — or whose `source=` custom property matches. Return the Business Process's `<name>`, owning view, and file path. If the matched Business Process has its own §9.3 view rooted on a sub-process, the §9.3 view's `<documentation>` block carries a `Parent process: <id-bp-...>` back-pointer (per [`references/procedures/process-view-emission.md`](references/procedures/process-view-emission.md) §2 rule 3) leading to the parent's §9.3 in one hop.

1c. **Reverse lookup — UI path.** If the symbol is a UI file (Blazor `*.razor`, Next.js `app/**/page.tsx` or `pages/*.tsx`, or a React Router component file): search `docs/architecture/**/*.oef.xml` for a UI Application Component in a §9.3 view (Process-rooted modality) whose `<name>` equals the file's repo-relative path, or whose `source=` custom property matches the file path, or whose `<documentation>` contains the file's basename. If matched, walk the outgoing Realisation edge to the Business Process at the top of the §9.3 stack. Return its `<name>`, owning view, and file path.

1c. **Reverse lookup — unmodelled fallback.** If neither path finds a match: report "unmodelled — for backend symbols, consider running Extract to generate a `LIFT-CANDIDATE` stub; for UI components, check the §9.3 view (Process-rooted modality) for this feature and author the UI Application Component per the Blazor idiom in reference §9.3". Do not fabricate a process name.

2. **Answer concisely.** Notation Q&A: one or two sentences citing the reference section and (if applicable) the ArchiMate® 3.2 chapter or Appendix B entry. Domain discovery / reverse lookup: return the ranked list or the single resolved Business Process; keep it to one line per entry. Include the default rule when a §4 layer-specific preference or §5.5 well-formedness rule applies.

## Output format

Every mode returns the mode result, evidence, quality level, change classification,
verification state, and footer fields needed by downstream agents. Read
[references/output-format.md](references/output-format.md) before emitting a final
Build, Extract, Review, or Lookup response, and copy the relevant skeleton rather
than inventing a new shape.

Minimum footer fields for all modes:

- Mode.
- Reference path.
- Canonical OEF path.
- Primary diagram kind and all diagram kinds present/missing.
- Per-view readiness matrix (when more than one materialized view) carrying Readiness (`model-valid` / `diagram-readable` / `review-ready`) and Authority (`lifted-from-source` / `forward-only-or-inferred` / `architect-approved` / `stakeholder-validated`) per view; artifact-rollup quality is the worst-view readiness minimum.
- Change classification: semantic model, view geometry, documentation/render inventory.
- Per-view layout backend report: one row per materialized view, distinguishing `layout-elk`, `route-repair`, `global-polish`, deterministic fallback, viewpoint-specific manual policy, preserved-authored geometry, unavailable backend, and validation-only PNG checks.
- Self-check (skill tooling — reference files, procedures, and scripts present/missing, weak-dependency status), self-check (run — §10 checklist pass/fail), source-geometry gate, external validation handoff, visual render inspection, render artifacts, and runtime drift state.
- Project assimilation and forward-only / process-view emission disclosure when applicable.

`Diagram kinds present` / `Diagram kinds missing` are computed by scanning the produced or parsed OEF for every `<view>` `viewpoint=` attribute and matching against the seven canonical strings in reference §9.1–§9.7 (Capability Map · Application Cooperation · Service Realization · Technology Usage · Migration · Motivation · Business Process Cooperation). The `M of 7` count is the file-wide coverage; `Diagram kind:` above remains the primary kind in scope for the current run (the one the architect asked for in pre-flight, or the kind being reviewed). For a single-kind file, `Diagram kinds present: 1 of 7` and the `Diagram kind:` line agree.

## Red flags

Read [references/red-flags.md](references/red-flags.md) when output contains an
`AD-*`, `AD-Q*`, `AD-L*`, or `AD-B-*` finding, when an emitted OEF fails import,
when Archi Validate Model or schema validation reports unresolved findings, or
before claiming `diagram-readable` / `review-ready` after a failed check.
Those red flags are stop conditions: fix them or explicitly lower the claimed
quality level before delivering.

## Complementary skills

- **`responsive-design`** (same plugin `souroldgeezer-design`) — produces the UI Application Components this skill models. Its Review mode checks for `docs/architecture/<feature>.oef.xml` and dispatches to this skill for drift detection when present.
- **`api-design`** (same plugin) — produces the HTTP API Application Components and, through loaded runtime/data extensions, the Technology Layer resources this skill models, such as Cosmos DB, Blob Storage, Key Vault, managed identity, or Function Apps. Same auto-dispatch pattern in its Review mode.
- **`devsecops-audit`** (plugin `souroldgeezer-audit`) — pipeline and IaC posture audit. Complements this skill: `architecture-design` proves the architecture *model* is well-formed; `devsecops-audit` proves the pipeline and infrastructure posture are secure. The GitHub Actions workflows that become Implementation & Migration Work Packages here are the same workflows audited there.

## Honest limits

- **Extract is bounded by the three extractable layers.** Business, Motivation, Strategy, and Physical are forward-only — no amount of reading code will produce them honestly. Output makes the boundary explicit; architects own the stubs.
- **Drift detection reads the repo, not a live Azure subscription.** The skill detects drift between a diagram and the committed code / IaC state; it does not detect drift between the IaC and actual deployed resources. Real-world drift (someone ran `az` in production) needs Azure Resource Graph or Defender for Cloud, not this skill.
- **Archi-specific canvas features are lost.** OEF is tool-neutral; custom figures, visual group styling, and Archi-specific viewpoint editor state are not round-tripped. Architects who need these edit in Archi directly after the skill's initial import. Reference §6.10.
- **The well-formedness checker is the skill, not the schema.** The skill does not run XSD validation at runtime — emitted files are correct by construction (every `xsi:type` drawn from the ArchiMate® 3.2 catalog, every relationship validated against Appendix B in Build and Review). XSD validation is delegated to the architect's toolchain: Archi's import rejects malformed XML; `xmllint --schema http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd <file>.oef.xml` is the explicit path. **`xmllint --noout` alone is not sufficient** — it checks XML well-formedness only and will not catch schema-level issues such as abstract-type violations (`AD-15`). Build's `[static]` self-check passing does not guarantee schema validity — it guarantees ArchiMate® well-formedness only.
- **The seven supported diagram kinds are a deliberate subset** of ArchiMate®'s expressive range. ViewPoints and less-common kinds (Product Map, Organisation Structure, Information Structure, Layered, Physical) are expressible in OEF but not first-class in v1 — reference §9.
- **Project packaging belongs to the consuming project.** The skill can review OEF/model/view quality by default. It does not own README entries, render galleries, screenshot freshness, publication pages, or project CI packaging unless the user explicitly asks for a separate project documentation review.
