---
name: architecture-design
description: Use when building, extracting, reviewing, or looking up ArchiMate® architecture models — enterprise, solution, or application architecture modelled in ArchiMate 3.2 and serialised as OEF XML per The Open Group ArchiMate Model Exchange File Format 3.2 (Appendix E of C226). Applies the bundled reference at souroldgeezer-design/docs/architecture-reference/architecture.md, enforcing The Open Group ArchiMate 3.2 (C226, March 2023) well-formedness rules including Appendix B relationship constraints, core-vs-extension layer discipline, and per-layer extractability (Application / Technology / Implementation & Migration are liftable from .NET solutions, Bicep, host.json, staticwebapp.config.json, and GitHub Actions workflows; Business / Motivation / Strategy are emitted as forward-only stubs). Output is loadable in ArchiMate-conformant tools. View layout uses the Sugiyama-v1 engine (introduced in 0.8.0) — a deterministic three-tier procedure (Tier 0 architect-position preservation; Tier 1 cycle handling, layered ordering with 4-pass barycentric crossing minimisation, median coordinate assignment, Manhattan A* edge routing with obstacle avoidance, bbox normalisation; Tier 2 per-viewpoint specialisations for each of the seven §9 viewpoints) — for cookbook-quality OEF in one shot, with zero runtime dependencies. Supports four modes — Build (intent → model), Extract (code/IaC → model), Review (artefact review + drift detection against code/IaC), Lookup (narrow notation question) — plus a matching subagent. Bridges to the sibling responsive-design and serverless-api-design skills via the canonical path docs/architecture/<feature>.oef.xml, which sibling skills consume for drift detection in their Review mode.
---

# Architecture Design

## Overview

Help Claude produce, extract, review, and look up ArchiMate architecture diagrams that are correct by construction across layer discipline, element use, relationship well-formedness, and code-to-model consistency. The central problem, from §1 of the reference:

> `architecture-design` answers *what the enterprise consists of* — which capability does this serve, which application service realises it, which technology node hosts it, which motivational driver justifies its existence. Its sole notation is ArchiMate.

**The reference is [../../docs/architecture-reference/architecture.md](../../docs/architecture-reference/architecture.md)** (bundled with the plugin). This skill is the *workflow* for applying it. Generated diagrams embody the reference's defaults; review output cites reference sections and ArchiMate 3.2 chapter / Appendix B references; the skill never duplicates reference prose.

This skill is the architectural *bridge* between the code produced by [responsive-design](../responsive-design/SKILL.md) and [serverless-api-design](../serverless-api-design/SKILL.md) and the architect's mental model of the system. Build goes from intent to diagram. Extract goes from code and IaC to diagram, lifting the three extractable ArchiMate layers and stubbing the three forward-only layers. Review checks both artefact well-formedness and drift between a diagram and current code. Siblings consume the canonical diagram path in their own Review mode to flag when code has drifted from the architect's model.

## Non-goals

- **Other architecture notations** (C4, UML deployment, TOGAF content metamodel, xAF) → out of scope; ArchiMate is the sole notation.
- **BPMN process modelling and UML sequence/interaction modelling** → explicitly out of scope (considered and cancelled in v1). Reference files, canonical paths, and smells for these notations do not exist.
- **Archi-native `.archimate` format** (Eclipse EMF XML, Archi-specific) → not emitted in v1. The skill emits OEF XML only — tool-neutral and readable by every major ArchiMate tool. Architects who want Archi-specific canvas features (custom figures, visual grouping, canvas styling presets) model those in Archi directly after import; the skill's Review mode will still parse the OEF export.
- **Business, Motivation, and Strategy layer extraction from source code or IaC** → reference §7.2; these layers are forward-only by design. Extract emits typed stubs marked `FORWARD-ONLY — architect fills in`; the architect is responsible for populating them.
- **Physical Layer extraction** → not attempted in v1; forward-only.
- **Runtime observation of architecture** (live topology from deployed resources) → static signals only — project files, IaC, workflow definitions. Drift against a live Azure subscription is not in scope.
- **Governance, approval, or review-board workflow** → the skill produces and checks diagrams; it does not run the architectural governance process around them.

## Modes

Four modes — deliberately distinct from the 3-mode symmetry of `responsive-design` / `serverless-api-design` because Extract (code → diagram) is a first-class, load-bearing operation for this skill.

### Build mode

**Use for:** producing a new ArchiMate diagram from architect intent.

**Triggers:** "design the architecture for …", "model the …", "sketch an ArchiMate view of …", "build a capability map / application cooperation / service realization / technology usage / migration view for …", "draw how … fits in the enterprise".

### Extract mode

**Use for:** lifting an ArchiMate diagram from existing code, IaC, and workflow definitions — the reverse direction of Build.

**Triggers:** "lift architecture from the repo", "extract an ArchiMate diagram from this solution", "reverse-engineer the architecture", "what does this codebase look like in ArchiMate", "generate an Application Cooperation view from the `*.csproj` set".

**Refusal condition.** Extract is refused if the requested layers are entirely forward-only (Business / Motivation / Strategy / Physical) — the skill explains which layers are extractable and suggests narrowing the request.

### Review mode

**Use for:** reviewing an existing ArchiMate model against the reference — both *artefact well-formedness* (does the OEF XML conform to ArchiMate 3.2?) and *drift* (does the model still reflect the current code and IaC?).

**Triggers:** "review this ArchiMate model", "check `…oef.xml` against the standard", "is this architecture model well-formed", "has the architecture drifted from the code", "drift check on `docs/architecture/<feature>.oef.xml`".

Review has two sub-behaviours, dispatched on inputs:
- **Artefact review** — a `.oef.xml` file alone → ArchiMate 3.2 well-formedness + `AD-*` smell catalog per reference §8.
- **Drift detection** — a `.oef.xml` file + the current code/IaC at the canonical locations (§ project assimilation) → delta report (elements added / removed / changed since the model was last aligned).

### Lookup mode

**Use for:** a specific, narrow question about the ArchiMate notation itself.

**Triggers:** "what's the difference between Business Function and Business Process", "which ArchiMate relationship connects an Application Component to an Application Service", "is Flow valid between Motivation elements", "what's the OEF `xsi:type` for a Strategy Capability", "can a Business Process have a Location".

**Default.** If the request is ambiguous between modes, ask. If the user says "design X architecture" without attaching artefacts, assume Build. If they attach code/IaC without an existing diagram, assume Extract. If they attach a diagram, assume Review. If it's a narrow factual question, assume Lookup.

## Extensions

The skill ships without framework extensions in v1. **Per-stack lifting rules live in `references/procedures/`, not in `extensions/`.** They are consulted (read on demand) when Extract runs — the harness's Skill tool loads `SKILL.md` only; nested procedure files require an explicit `Read` tool call before they can inform the agent. The split between procedures is by *input source* (code / IaC / workflow), not by *target stack choice*.

| Procedure | Applies to | Used by |
|---|---|---|
| `references/procedures/lifting-rules-dotnet.md` | .NET solutions, Azure Functions (isolated-worker), Blazor WebAssembly | Extract → ArchiMate Application Layer |
| `references/procedures/lifting-rules-bicep.md` | Bicep IaC | Extract → ArchiMate Technology Layer (Nodes, System Software, Communication Network, Path, Artifact) |
| `references/procedures/lifting-rules-gha.md` | GitHub Actions workflow files | Extract → ArchiMate Implementation & Migration Layer (Work Package, Deliverable, Implementation Event, Plateau) |
| `references/procedures/lifting-rules-process.md` | Durable Functions orchestrators and Logic Apps workflow definitions (when present) | Extract → ArchiMate Business Layer (Business Process, Event, Interaction only) with per-element `LIFT-CANDIDATE` markers; reverse Lookup consumes the same `source=` attribute. UI route lifting is deferred — §9.3 Process-rooted modality UI Application Component and Application Interface are hand-authored by the architect per the Blazor idiom in reference §9.3 |
| `references/procedures/drift-detection.md` | Any diagram + code pair at canonical paths | Review → drift sub-behaviour (including process drift `AD-DR-11` / `AD-DR-12`) |
| `references/procedures/layout-strategy.md` | Any view being built or extracted | Build / Extract → three-tier layout engine (Tier 0 architect-position preservation; Tier 1 Sugiyama-v1 core: cycle handling, layer assignment, 4-pass barycentric, median coordinate assignment, Manhattan A* edge routing, bbox normalisation; Tier 2 per-viewpoint specialisation per §9 diagram kind); Review restates its rules as `AD-L*` checks |

Smells are namespaced `AD-*` (reference §8), with sub-namespaces `AD-L*` for layout and `AD-B-*` for process-flow artefacts (§9.7 / §9.3). There are no framework-specific smell namespaces in v1 — architecture-design findings are notation-level, not stack-level.

Adding a new input source later (Terraform, Azure Pipelines YAML, ARM templates, Kubernetes manifests) means adding a new procedure file, not an extension.

## Canonical path

Diagrams written and read by the skill live at a single canonical path:

```
docs/architecture/<feature>.oef.xml
```

The path is the coupling mechanism for the sibling design skills (`responsive-design` and `serverless-api-design`). Their Review mode checks this path, and if a matching diagram exists, dispatches to `architecture-design` Review for drift detection.

`<feature>` is a short snake-case or kebab-case identifier — `checkout`, `order-to-cash`, `auth`, `ingestion-pipeline`. One file per feature; the file may contain multiple views inside its `<views>/<diagrams>` block (Capability Map, Application Cooperation, Technology Usage, etc. for the same feature). The skill suggests the filename; the architect can override.

## Pre-flight (build & extract & review)

Before producing or reviewing a diagram, confirm the following. If the user hasn't supplied them, ask — don't invent answers:

1. **Diagram kind.** Capability Map / Application Cooperation / Service Realization / Technology Usage / Migration / Motivation / Business Process Cooperation (reference §9). Default: the skill offers the closest fit based on the user's prompt; asks if two are plausible. Diagrams outside the seven supported kinds are declined. Each kind's English label and OEF `viewpoint=` attribute value are identical.
2. **Layer scope.** Which ArchiMate layers is the diagram working with? Default: Core Framework (Business + Application + Technology) unless the diagram kind implies Strategy (Capability Map), Motivation (Motivation), or Implementation & Migration (Migration). Crossing extensions into a Core view without cause triggers `AD-7`.
3. **Extraction posture (Extract mode only).** Which input sources to read — .NET solution, Bicep, GHA workflows, `host.json` / `staticwebapp.config.json`, and Durable Functions orchestrators / Logic Apps workflow definitions (when present — these enable Business Process / Event / Interaction lifting per reference §7.4 with `LIFT-CANDIDATE` markers; UI routes are not lifted in v1). Default: all of the above when present. Fully forward-only layers (Motivation / Strategy / Physical) and the forward-only subset of Business (Actor / Role / Collaboration / Object / Contract / Product / Service / Function) are emitted as typed stubs per reference §7.
4. **Feature name.** The `<feature>` slug that becomes the canonical filename. Default: derived from the user's prompt or the solution name.

If any answer deviates from defaults (e.g., "include Physical Layer for this data-centre diagram"), state the deviation explicitly in the output footer.

## Project assimilation (before build, extract, and review)

**Direction is one-way: the project is assimilated to the reference, not the reference to the project.** The reference's layer discipline (§2.1), aspect rules (§2.3), Core-vs-extension defaults (§2.4), and relationship well-formedness (§2.5 and ArchiMate 3.2 Appendix B) are non-negotiable. Assimilation means discovering what the project ships so output (a) aligns to any existing diagram at the canonical path, (b) reuses project names and feature labels, and (c) surfaces drift as legacy debt rather than silently ignoring it.

Before producing or reviewing a diagram, run the discovery pass below. Keep detection lightweight — canonical locations only. If nothing found, assume greenfield and ask the architect for intent.

### Discovery pass (all modes)

1. **Existing model at the canonical path.** Check `docs/architecture/<feature>.oef.xml` for the feature in scope. If present, parse it and record the element identifiers, names, relationships, and view coordinates — Extract and Build both respect existing identifiers (no gratuitous churn). If absent, treat as greenfield for this feature.
2. **.NET solution surface.** Grep for `*.sln`, `*.csproj`, `Microsoft.Azure.Functions.Worker` (Azure Functions isolated-worker; maps to Application Component + hosted-on Technology Node), `Microsoft.NET.Sdk.BlazorWebAssembly` (Blazor WASM standalone; Application Component), `AddInteractiveWebAssemblyComponents` / `AddInteractiveWebAssemblyRenderMode` with `.Client` project (Blazor Web App `.Client`), top-level class libraries (Application Component or a shared `Artifact` depending on packaging).
3. **Azure Functions `host.json`.** Each function's bindings surface Application Interfaces; the host file itself implies an Azure Functions runtime (System Software) on an App Service / Function App (Node).
4. **Static Web App config** (`staticwebapp.config.json`). Maps to an Azure Static Web Apps Node hosting a Blazor or static Application Component; routes and auth providers map to Application Interfaces.
5. **Bicep IaC.** Grep `*.bicep` for Microsoft.Web/sites, Microsoft.Web/serverfarms, Microsoft.DocumentDB/databaseAccounts, Microsoft.Storage/storageAccounts, Microsoft.KeyVault/vaults, Microsoft.Network/virtualNetworks, Microsoft.Network/privateEndpoints, Microsoft.OperationalInsights/workspaces, Microsoft.Insights/components, Microsoft.ManagedIdentity/userAssignedIdentities. Each maps to a Technology Layer element per `references/procedures/lifting-rules-bicep.md`.
6. **GitHub Actions workflows.** Grep `.github/workflows/*.yml` for deploy / release jobs — each becomes a Work Package; environments become Plateaus; successful deploys become Implementation Events.
7. **Solution topology signals** — project reference graph (`<ProjectReference>` in `.csproj`) maps to Used-by / Composition / Realisation relationships within the Application Layer.

### Forward-only layers in discovery

The discovery pass **never produces Business, Motivation, Strategy, or Physical elements from source code.** These layers are reference-§7.2 forward-only. If an existing diagram at the canonical path contains them, the skill reads them verbatim and preserves them across Extract re-runs; the architect owns their content.

### Mapping existing infrastructure to reference rules

Reuse is conditional on **substantive compliance with ArchiMate 3.2**, not presence. For each discovered element in an existing diagram:

| Discovered in existing diagram | Reuse when | Flag when |
|---|---|---|
| Layer assignment per element | Element is in the correct layer per §3–4 | Misplaced element (e.g., a Service labelled Business but used as Application Service) — `AD-1` / `AD-3` |
| Aspect per element | Active / Behaviour / Passive distinction clean | Double-stereotyped box — `AD-3` |
| Relationship between two elements | Valid per Appendix B Relationships Table | Invalid relationship — `AD-2` |
| Identifier ↔ `<name>` semantics | Identifier slug agrees with `<name>` content | Mismatch — `AD-8` |
| Realisation chain | Business Service → Application Service → Application Component, complete for the scope | Missing intermediate — `AD-6` |
| Forward-only markers | `FORWARD-ONLY — architect fills in` header present for Business / Motivation / Strategy sections | Forward-only layer populated without the marker — `AD-14` |

**Name adoption is always fine.** If the project calls its checkout function `CheckoutFunction` and an existing ArchiMate diagram labels the Application Component `Checkout Service`, adopt the existing diagram label — the rule is layer and relationship discipline, not spelling. Extract preserves existing labels; Build defaults to project names with architect-editable suggestions.

**Substantive non-compliance is never fine.** If an existing diagram shows a Business Process *realising* a Technology Node (reference §5.5, Appendix B), Build and Extract do not propagate the broken relationship into new output — the finding is reported and the correct relationship is emitted.

### Footer additions

All mode footers gain a `Project assimilation:` block listing: existing diagram reused, element labels preserved, and any drift or well-formedness issues flagged. Example:

```
Project assimilation:
  Existing model: docs/architecture/checkout.oef.xml (last modified 2026-04-12)
    elements preserved: 11/11, identifiers preserved: 11/11, view layouts preserved: 3/3
  Layers extracted (Extract mode):
    Application:  from Orders.Api.csproj, Orders.Core.csproj, Blazor.Client.csproj — 3 components
    Technology:   from infra/main.bicep — 1 Function App + 1 Cosmos account + 1 Storage account + 1 Key Vault + 1 Managed Identity
    Impl & Migr:  from .github/workflows/deploy.yml — 1 Work Package, 3 Plateaus (dev/staging/prod)
  Forward-only layers: Business, Motivation, Strategy — typed stubs emitted; architect fills in
  Drift vs existing diagram: 1 element added (Cosmos account), 1 removed (Table Storage account)
```

## Build mode workflow

0. **Dispatch.** Confirm Build mode. Run the pre-flight above. Announce the diagram kind and layer scope.

1. **Principles scan.** Read reference [§2 Principles](../../docs/architecture-reference/architecture.md#2-principles). Output must not violate: §2.1 layer separation, §2.3 aspect rules, §2.4 Core-vs-extension discipline, §2.5 relationship well-formedness.

2. **Pick the diagram kind from reference §9.** The kind fixes the element palette and prevents layer soup (`AD-1`). Re-use an existing diagram at the canonical path when one exists; otherwise create fresh.

3. **Compose elements and relationships.**
   - Element types from reference §4 (per layer).
   - Relationship types from reference §5.
   - Well-formedness per ArchiMate 3.2 Appendix B — never emit a relationship not found in the table for the given element-pair.
   - OEF XML serialisation per reference §6. Emit every element with its correct `xsi:type` from the ArchiMate 3.2 element catalog; emit every relationship with its correct `xsi:type` per ArchiMate 3.2 Appendix B.

4. **Layout and naming** per reference §6.4–6.7. `Read` [`references/procedures/layout-strategy.md`](references/procedures/layout-strategy.md) before invoking it (the Skill tool loads `SKILL.md` only; nested files are not auto-injected). The procedure runs the **three-tier layout engine** introduced in 0.8.0:
   - **Tier 0** preserves architect-positioned `<node>` placements verbatim from any prior view at the canonical path (existing rule).
   - **Tier 1** runs the Sugiyama-v1 core engine — six phases: (1) cycle handling, (2) layer assignment, (3) within-layer ordering with 4-pass barycentric crossing minimisation, (4) coordinate assignment via median heuristic, (5) Manhattan A* edge routing with obstacle avoidance, (6) bounding-box normalisation to `(40, 40)` origin.
   - **Tier 2** applies the per-viewpoint specialisation matching the §9 diagram kind in scope (Capability Map / Application Cooperation / Service Realization / Technology Usage / Migration / Motivation / Business Process Cooperation).
   Identifiers are `id-<slug>` in lowercase-with-hyphens per §6.6; `<name>` values follow the element-type conventions in §6.7.

5. **Write the canonical file.** Default location `docs/architecture/<feature>.oef.xml`. If an architect has named a specific path, honour that. Emit the §6.4a banding marker on every new file. Declare under `<propertyDefinitions>` at the model root:

   ```xml
   <propertyDefinition identifier="propid-archi-model-banded" type="string">
     <name xml:lang="en">archi-model-banded</name>
   </propertyDefinition>
   ```

   The `<name>` child is **required** by the OEF schema (`PropertyDefinitionType` mandates a `<name>` element); the self-closing form `<propertyDefinition .../>` fails Archi's import with `cvc-complex-type.2.4.b: The content of element 'propertyDefinition' is not complete`. The same `<name>`-required rule applies to every `<propertyDefinition>` (e.g. `propid-archi-arm`, `propid-strength`). Apply the marker via `<property propertyDefinitionRef="propid-archi-model-banded"><value xml:lang="en">v2</value></property>` once under `<properties>` on the `<model>` element. Build emits the §6.4a banding marker value `v2` on every new file in 0.8.0; legacy `v1` markers on existing files are preserved verbatim by Extract and never auto-upgraded. The marker is the authoritative signal for AD-L1 severity in Review. Also emit a default Dublin Core `<metadata>` block per reference §6.1a, with `dc:title` set to the feature name and `dc:creator` set to `architecture-design <plugin-version>` (read the live version from `souroldgeezer-design/.claude-plugin/plugin.json`); namespace constraint per `MetadataType`'s `<xs:any namespace="##other"/>` is non-negotiable (`AD-16`). **Emit all top-level `<model>` children in OEF sequence per reference §6** — `name → documentation → properties → metadata → elements → relationships → organizations → propertyDefinitions → views`; the `<properties>` element (carrying the banding marker's value) precedes `<metadata>` and `<elements>`, while `<propertyDefinitions>` (carrying the banding marker's definition) follows `<organizations>` and immediately precedes `<views>`. The two blocks are non-adjacent (`AD-17`).

6. **Self-check against reference §10** before declaring done. Each checklist item carries `[static]` or `[runtime]` verification-layer tags. Walk each item:
   - `[static]` — verify against the diagram source just produced.
   - `[runtime]` — verify against the current `.csproj` / Bicep / workflow state; if out of scope, mark "source-aligned; runtime verification required."
   If any `[static]` item fails, fix before delivering.

7. **Emit footer disclosure.**

## Extract mode workflow

0. **Dispatch.** Confirm Extract mode. Run the pre-flight above. Confirm which layers to extract (default: all three extractable — Application / Technology / Implementation & Migration).

1. **Refuse if scope is entirely forward-only.** If the architect has asked for Business / Motivation / Strategy / Physical only, refuse with:
   - the reference §7.2 explanation of why these layers are forward-only;
   - a suggestion to run Build mode with the architect's intent as input.

2. **Run the discovery pass (above).** Record what was found — solution surface, Bicep resources, workflows, existing diagram at the canonical path.

3. **Read each applicable procedure file, then invoke it.** The Skill tool that loaded this `SKILL.md` does not auto-inject nested files; each procedure must be `Read` explicitly before its rules can inform the agent.
   - `references/procedures/lifting-rules-dotnet.md` → Application Layer elements + intra-Application relationships (when .NET solution sources are present).
   - `references/procedures/lifting-rules-bicep.md` → Technology Layer elements + Application-to-Technology Assignment / Realisation relationships (when Bicep is present).
   - `references/procedures/lifting-rules-gha.md` → Implementation & Migration Layer elements (when `.github/workflows/*.yml` is present).
   - `references/procedures/lifting-rules-process.md` → Business Process / Event / Interaction `LIFT-CANDIDATE` emission (when Durable Functions orchestrators or Logic Apps workflows are present).
   - `references/procedures/layout-strategy.md` → view placements for any element not carrying an architect-authored position in the prior diagram at the canonical path (always; Step 1 of the procedure preserves hand edits, only new elements are placed algorithmically).

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

5. **Preserve existing model content.** If `docs/architecture/<feature>.oef.xml` exists, merge rather than overwrite: existing element identifiers, `<name>` values, `<documentation>`, properties, view placements, and forward-only content are preserved; extracted elements are added, missing elements are removed (surfaced as drift findings in the footer). The §6.4a banding marker (`propid-archi-model-banded=v1`) is preserved if present and **never auto-injected** on a legacy file — auto-injecting would assert §6.4a conformance over coordinates that pre-date the bands. Legacy files therefore stay unmarked and Review soft-grades AD-L1 to `info` per reference §8; architects who want full conformance run Build for the affected views, which writes a fresh marker.

6. **Self-check against reference §10** as in Build.

7. **Emit footer disclosure including the per-layer lift / stub breakdown** — which layers were lifted, which were stubbed, which sources were read.

## Review mode workflow

0. **Dispatch.** Confirm Review mode. Run pre-flight. Identify sub-behaviour:
   - Artefact review (diagram file alone, or diagram + architect asks "is this well-formed").
   - Drift detection (diagram + code/IaC at canonical locations, or architect asks "has this drifted").
   If both apply, run artefact review first, then drift detection.

### Artefact review

**Banding-marker dispatch.** Severity of layout findings is conditional on the `propid-archi-model-banded` property:

| Marker on file | AD-L1..L8 severity | AD-L9, AD-L11 severity | AD-L10 severity |
|---|---|---|---|
| `propid-archi-model-banded=v2` (Sugiyama-v1 engine, 0.8.0+) | `warn` | `warn` | `info` |
| `propid-archi-model-banded=v1` (legacy banded grid, pre-0.8.0) | `warn` | `info` | `info` |
| (no marker) | `info` | `info` | `info` |

The marker is the authoritative signal for the file's layout-conformance contract. Build emits `v2` on every new file in 0.8.0; Extract preserves existing markers and never auto-upgrades a `v1` file (the architect rebrands by re-running Build for the affected views).

1. **Parse the `.oef.xml`** into elements (with `xsi:type`, identifier, name), relationships (with `xsi:type`, source, target), views and their node/connection placements.

2. **Walk reference §10 checklist bucket by bucket.** For each item, inspect the diagram and record: pass / fail / not-applicable. Failures become findings with `AD-*` smell codes from reference §8.

3. **Per-finding format.** Match the sibling-skill convention:

   ```
   [<AD-N>] <file>:<line or element identifier>
     layer:    static | runtime
     severity: block | warn | info
     evidence: <quoted XML fragment — element, relationship, or view node>
     action:   <suggested fix referencing reference §X and ArchiMate 3.2 §/Appendix>
     ref:      architecture.md §<n.m> + ArchiMate 3.2 §<chapter> / Appendix B
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

1c. **Reverse lookup — backend path.** If the symbol is a backend orchestrator / workflow: (i) locate the symbol via `Grep` / `Glob`; (ii) find the enclosing Durable Functions orchestrator (`[Function]` on a function whose trigger parameter is `TaskOrchestrationContext` / `IDurableOrchestrationContext`) or Logic Apps workflow (`workflow.json`, `*.logicapp.json`, or Bicep `Microsoft.Logic/workflows`); (iii) search `docs/architecture/**/*.oef.xml` for a Business Process element whose preceding XML comment carries `LIFT-CANDIDATE source=<matching path>` — or whose `<name>` (case-insensitive, whitespace-trimmed) matches the orchestrator / workflow name — or whose `source=` custom property matches. Return the Business Process's `<name>`, owning view, and file path.

1c. **Reverse lookup — UI path.** If the symbol is a UI file (Blazor `*.razor`, Next.js `app/**/page.tsx` or `pages/*.tsx`, or a React Router component file): search `docs/architecture/**/*.oef.xml` for a UI Application Component in a §9.3 view (Process-rooted modality) whose `<name>` equals the file's repo-relative path, or whose `source=` custom property matches the file path, or whose `<documentation>` contains the file's basename. If matched, walk the outgoing Realisation edge to the Business Process at the top of the §9.3 stack. Return its `<name>`, owning view, and file path.

1c. **Reverse lookup — unmodelled fallback.** If neither path finds a match: report "unmodelled — for backend symbols, consider running Extract to generate a `LIFT-CANDIDATE` stub; for UI components, check the §9.3 view (Process-rooted modality) for this feature and author the UI Application Component per the Blazor idiom in reference §9.3". Do not fabricate a process name.

2. **Answer concisely.** Notation Q&A: one or two sentences citing the reference section and (if applicable) the ArchiMate 3.2 chapter or Appendix B entry. Domain discovery / reverse lookup: return the ranked list or the single resolved Business Process; keep it to one line per entry. Include the default rule when a §4 layer-specific preference or §5.5 well-formedness rule applies.

3. **Footer disclosure** (single line in lookup mode).

## Output format

### Build mode

```
<OEF XML document>

Self-check:
  Well-formedness:       <n>/<n>  [static verified]
  Layer discipline:      <n>/<n>  [static verified]
  Appendix B relations:  <n>/<n>  [static verified]
  Runtime correspondence: <n>/<n> [runtime verified — or source-aligned, IaC verification required]

Deviations from defaults (if any): <list with reason>
```

### Extract mode

```
<OEF XML document with FORWARD-ONLY comment blocks around fully-stubbed element sections, and LIFT-CANDIDATE XML comments preceding each Business Process / Event / Interaction emitted from backend workflow sources>

Extraction summary:
  Layers lifted:          Application (<n>), Technology (<n>), Implementation & Migration (<n>), Business-Process (<n_lift_candidates>)
  Layers stubbed (forward-only): Motivation, Strategy; Business-other (Actor / Role / Collaboration / Object / Contract / Product / Service / Function)
  Sources read:           <list of files, including Durable Functions orchestrators and Logic Apps workflows when present>
  LIFT-CANDIDATE confidence: <n_high> high / <n_medium> medium / <n_low> low
  Elements preserved from existing diagram: <n>/<n>
  Drift vs existing diagram: <added / removed / changed counts, or n/a if greenfield>
```

### Review mode

Per-finding block for each failure, then rollup. All findings cite `AD-*` code + reference §n + ArchiMate 3.2 §/Appendix. Each finding includes a `layer:` field so the reader knows how to confirm: `static` (diagram-source inspection), `runtime` (vs current code/IaC). Only `static` findings are definitively pass / fail from source alone; `runtime` findings are "source-aligned, confirmation requires re-running drift detection on current code."

### Lookup mode

Two to four lines of prose + one footer line.

### Footer (all modes)

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-design/docs/architecture-reference/architecture.md
Canonical path: docs/architecture/<feature>.oef.xml
Diagram kind: <reference §9 kind name — primary kind in scope this run>
Diagram kinds present: <M> of 7 (<comma-separated canonical viewpoint names>)
Diagram kinds missing: <comma-separated canonical viewpoint names, or "none">
Layout engine: Sugiyama-v1 [+ <viewpoint> specialisation, when applicable]
Layers in scope: <comma-separated>
Self-check: pass | <n failures> | n/a
Project assimilation:
  <block per the Project assimilation section above>
Forward-only layers stubbed: <list, or "none">
Runtime-verified drift: <n findings, or "drift detection not run">
```

`Diagram kinds present` / `Diagram kinds missing` are computed by scanning the produced or parsed OEF for every `<view>` `viewpoint=` attribute and matching against the seven canonical strings in reference §9.1–§9.7 (Capability Map · Application Cooperation · Service Realization · Technology Usage · Migration · Motivation · Business Process Cooperation). The `M of 7` count is the file-wide coverage; `Diagram kind:` above remains the primary kind in scope for the current run (the one the architect asked for in pre-flight, or the kind being reviewed). For a single-kind file, `Diagram kinds present: 1 of 7` and the `Diagram kind:` line agree.

## Red flags — stop and re-run

Output contains any of the following? Stop; fix before delivering:

- **Invalid relationship per Appendix B.** Fix per `AD-2`; consult ArchiMate 3.2 Appendix B (Relationships Table).
- **Business Actor, Role, Collaboration, Object, Contract, Product, Service, or Function emitted by Extract mode without a `FORWARD-ONLY` XML-comment marker.** Fix per `AD-14`; these elements are forward-only by design (reference §7.2). The marker is an XML comment (`<!-- ... -->`) per reference §7.3; the `'`-prefixed form is wrong (PlantUML / INI syntax) — OEF output is XML.
- **Business Process, Event, or Interaction emitted by Extract mode without a `LIFT-CANDIDATE` marker** (or with a marker missing the required `source=` or `confidence=` attribute). Fix per `AD-14-LC`; these elements are *partially* forward-only — lifted from backend workflow sources per reference §7.4 and tagged so the architect can confirm each one.
- **Motivation or Strategy elements emitted by Extract mode without a `FORWARD-ONLY` marker.** Fix per `AD-14`.
- **Layer soup** — a single diagram containing Business, Application, Technology, Motivation, and Strategy elements without a clear concern. Fix per `AD-1`; pick one of the seven supported diagram kinds (reference §9).
- **Business Process Cooperation view lacking a Triggering or Flow chain** through its Behaviour elements, or containing non-Business-layer elements. Fix per `AD-B-1` / `AD-B-4`.
- **§9.3 Service Realization view (Process-rooted modality) with a Business Process at top but no realising Application Service** (`AD-B-6`) or **no Application Component realising the Application Service** (`AD-B-7`).
- **§9.3 Service Realization view for a user-driven Business Process** (one with a Business Actor Assignment per reference §4.1) **lacking a UI Application Component and Application Interface** at the entry point. Fix per `AD-B-10`; add the UI Component (for Blazor: `<name>` = the page component's file path) and the Application Interface (`<name>` = the `@page` route) with the appropriate Realisation / Assignment edges.
- **Business Process in a §9.7 view with no Realisation into any §9.3 view (Process-rooted modality) for the same feature.** Fix per `AD-B-8`; either author the drill-down view or retract the process.
- **Missing Realisation chain** — a Business Service in scope with no Application Service realising it, or an Application Service with no Application Component. Fix per `AD-6`.
- **Active structure directly accessing passive structure** — an Actor drawn accessing a Business Object without a Process / Function in between. Fix per `AD-4`.
- **Association overuse** — more than one Association relationship in a single diagram. Fix per `AD-5`; pick a real relationship.
- **Migration view without a Plateau axis.** Fix per `AD-9`.
- **Extract refused with no guidance.** Fix by suggesting the correct mode (Build) and naming the forward-only layers.
- **Drift finding asserting a pass from static review alone.** Fix: restate as "source-aligned; drift re-check required against current code/IaC."
- **Emitting elements with invalid `xsi:type`.** Every `<element>` and `<relationship>` must use an exact ArchiMate 3.2 type name (reference §6.2 for elements, §6.3 for relationships). Misspellings (`Application_Component`, `app-component`, `ApplicationAPI`) break tool import.
- **View `<node>` or `<connection>` emitted without `xsi:type`.** Fix per `AD-15`; OEF's `ViewNodeType` and `ConnectionType` are abstract complexTypes — `<node>` must carry `xsi:type="Element"` (or `Container` / `Label`) and `<connection>` must carry `xsi:type="Relationship"` (or `Line`). Archi's XSD-validating import rejects bare elements with `cvc-type.2`. `xmllint --noout` does *not* catch this — use `xmllint --schema <url>` or open in Archi.
- **`<metadata>` block with catalog payload in the ArchiMate namespace** — the catalog content beyond the optional `<schema>` / `<schemaversion>` SchemaInfoGroup prelude. Fix per `AD-16`; the prelude legitimately inherits the ArchiMate default namespace, but catalog payload elements must come from a non-ArchiMate namespace (Dublin Core or similar). See reference §6.1a for the canonical block layout. `xmllint --noout` does *not* catch this; `xmllint --schema <url>` and Archi import do.
- **Model children out of OEF sequence.** Fix per `AD-17`; reference §6 states the mandatory order — `name → documentation → properties → metadata → elements → relationships → organizations → propertyDefinitions → views`. Most commonly hit when the §6.4a banding marker's `<properties>` and `<propertyDefinitions>` blocks are emitted adjacently rather than at the correct sequence positions. Archi rejects out-of-order with `cvc-complex-type.2.4.a`. `xmllint --noout` does *not* catch this — use `xmllint --schema <url>` or open in Archi.
- **Node placed in violation of relative layer ordering.** Fix per `AD-L1`; reference §6.4a defines the relative ordering (Strategy above Business above Application above Technology above Physical) — absolute y-bands are no longer specified in 0.8.0 (Phase 6 bbox normalisation makes them content-dependent). Severity follows the §6.4a banding marker — `warn` when `propid-archi-model-banded=v2`, `warn` when `v1`, `info` when absent.
- **Two nodes overlapping** at the same nesting depth in the same view. Fix per `AD-L2`; re-run the layout procedure or widen the containing cell.
- **Label truncation risk** (`w < 120`, `h < 55`, or `w` too small for the `<name>`). Fix per `AD-L3`; enlarge `w` in 20-px steps until the label fits at the default Archi font.
- **View over budget** — >20 elements or >30 relationships in a single `<view>`. Fix per `AD-L4`; split the view, or promote a cluster to a Grouping (§4.8; logical, never a layer container).
- **Nested-plus-edge** — a child node visually nested inside a parent *and* the parent–child `<connection>` also drawn in the same view. Fix per `AD-L7`; hide the edge via the `propid-archi-arm` = `hide` property on the relationship, or draw the two elements side-by-side (un-nest).
- **Off-grid coordinates** — any `x`, `y`, `w`, `h`, or `<bendpoint>` not a multiple of 10. Fix per `AD-L8`; re-snap to the 10-px grid.
- **Hierarchy violation.** Fix per `AD-L9`; a Realization / Used-by / Serving edge between same-layer elements drawn against topological direction. Re-run Tier 1 phase 3 (within-layer ordering); if cycle present, phase 1 handles.
- **Canvas not normalised at origin.** Fix per `AD-L10`; the used region's top-left should be at `(40, 40) ± 10 px`. Re-run Tier 1 phase 6 (bbox normalisation).
- **Edge passes through a non-source / non-target node body.** Fix per `AD-L11`; Tier 1 phase 5 (Manhattan A* with obstacle avoidance) should prevent. Most often caused by adjacent-cell edges where the simpler shortest-path route was kept after a hand-edit.

## Complementary skills

- **`responsive-design`** (same plugin `souroldgeezer-design`) — produces the UI Application Components this skill models. Its Review mode checks for `docs/architecture/<feature>.oef.xml` and dispatches to this skill for drift detection when present.
- **`serverless-api-design`** (same plugin) — produces the HTTP API Application Components and the Technology Layer resources (Cosmos DB, Blob Storage, Key Vault, managed identity, Function Apps) this skill models. Same auto-dispatch pattern in its Review mode.
- **`devsecops-audit`** (plugin `souroldgeezer-audit`) — pipeline and IaC posture audit. Complements this skill: `architecture-design` proves the architecture *model* is well-formed; `devsecops-audit` proves the pipeline and infrastructure posture are secure. The GitHub Actions workflows that become Implementation & Migration Work Packages here are the same workflows audited there.

## Honest limits

- **Extract is bounded by the three extractable layers.** Business, Motivation, Strategy, and Physical are forward-only — no amount of reading code will produce them honestly. Output makes the boundary explicit; architects own the stubs.
- **Drift detection reads the repo, not a live Azure subscription.** The skill detects drift between a diagram and the committed code / IaC state; it does not detect drift between the IaC and actual deployed resources. Real-world drift (someone ran `az` in production) needs Azure Resource Graph or Defender for Cloud, not this skill.
- **Archi-specific canvas features are lost.** OEF is tool-neutral; custom figures, visual group styling, and Archi-specific viewpoint editor state are not round-tripped. Architects who need these edit in Archi directly after the skill's initial import. Reference §6.10.
- **The well-formedness checker is the skill, not the schema.** The skill does not run XSD validation at runtime — emitted files are correct by construction (every `xsi:type` drawn from the ArchiMate 3.2 catalog, every relationship validated against Appendix B in Build and Review). XSD validation is delegated to the architect's toolchain: Archi's import rejects malformed XML; `xmllint --schema http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd <file>.oef.xml` is the explicit path. **`xmllint --noout` alone is not sufficient** — it checks XML well-formedness only and will not catch schema-level issues such as abstract-type violations (`AD-15`). Build's `[static]` self-check passing does not guarantee schema validity — it guarantees ArchiMate well-formedness only.
- **The seven supported diagram kinds are a deliberate subset** of ArchiMate's expressive range. ViewPoints and less-common kinds (Product Map, Organisation Structure, Information Structure, Layered, Physical) are expressible in OEF but not first-class in v1 — reference §9.
