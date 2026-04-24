---
name: architecture-design
description: Use when building, extracting, reviewing, or looking up ArchiMate® architecture models — enterprise, solution, or application architecture modelled in ArchiMate 3.2 and serialised as OEF XML per The Open Group ArchiMate Model Exchange File Format 3.2 (Appendix E of C226). Applies the bundled reference at souroldgeezer-design/docs/architecture-reference/architecture.md, enforcing The Open Group ArchiMate 3.2 (C226, March 2023) well-formedness rules including Appendix B relationship constraints, core-vs-extension layer discipline, and per-layer extractability (Application / Technology / Implementation & Migration are liftable from .NET solutions, Bicep, host.json, staticwebapp.config.json, and GitHub Actions workflows; Business / Motivation / Strategy are emitted as forward-only stubs). Output is loadable in ArchiMate-conformant tools. Supports four modes — Build (intent → model), Extract (code/IaC → model), Review (artefact review + drift detection against code/IaC), Lookup (narrow notation question) — plus a matching subagent. Bridges to the sibling responsive-design and serverless-api-design skills via the canonical path docs/architecture/<feature>.oef.xml, which sibling skills consume for drift detection in their Review mode.
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

**Triggers:** "design the architecture for …", "model the …", "sketch an ArchiMate view of …", "build a capability map / application cooperation / technology realisation / migration view for …", "draw how … fits in the enterprise".

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

The skill ships without framework extensions in v1. **Per-stack lifting rules live in `references/procedures/`, not in `extensions/`.** They are always loaded when Extract runs — the split is by *input source* (code / IaC / workflow), not by *target stack choice*.

| Procedure | Applies to | Used by |
|---|---|---|
| `references/procedures/lifting-rules-dotnet.md` | .NET solutions, Azure Functions (isolated-worker), Blazor WebAssembly | Extract → ArchiMate Application Layer |
| `references/procedures/lifting-rules-bicep.md` | Bicep IaC | Extract → ArchiMate Technology Layer (Nodes, System Software, Communication Network, Path, Artifact) |
| `references/procedures/lifting-rules-gha.md` | GitHub Actions workflow files | Extract → ArchiMate Implementation & Migration Layer (Work Package, Deliverable, Implementation Event, Plateau) |
| `references/procedures/drift-detection.md` | Any diagram + code pair at canonical paths | Review → drift sub-behaviour |

Smells are namespaced `AD-*` (reference §8). There are no framework-specific smell namespaces in v1 — architecture-design findings are notation-level, not stack-level.

Adding a new input source later (Terraform, Azure Pipelines YAML, ARM templates, Kubernetes manifests) means adding a new procedure file, not an extension.

## Canonical path

Diagrams written and read by the skill live at a single canonical path:

```
docs/architecture/<feature>.oef.xml
```

The path is the coupling mechanism for the sibling design skills (`responsive-design` and `serverless-api-design`). Their Review mode checks this path, and if a matching diagram exists, dispatches to `architecture-design` Review for drift detection.

`<feature>` is a short snake-case or kebab-case identifier — `checkout`, `order-to-cash`, `auth`, `ingestion-pipeline`. One file per feature; the file may contain multiple views inside its `<views>/<diagrams>` block (Capability Map, Application Cooperation, Technology Realisation, etc. for the same feature). The skill suggests the filename; the architect can override.

## Pre-flight (build & extract & review)

Before producing or reviewing a diagram, confirm the following. If the user hasn't supplied them, ask — don't invent answers:

1. **Diagram kind.** Capability Map / Application Cooperation / Application-to-Business Realisation / Technology Realisation / Migration View / Motivation View (reference §9). Default: the skill offers the closest fit based on the user's prompt; asks if two are plausible. Diagrams outside the six supported kinds are declined.
2. **Layer scope.** Which ArchiMate layers is the diagram working with? Default: Core Framework (Business + Application + Technology) unless the diagram kind implies Strategy (Capability Map), Motivation (Motivation View), or Implementation & Migration (Migration View). Crossing extensions into a Core view without cause triggers `AD-7`.
3. **Extraction posture (Extract mode only).** Which input sources to read — .NET solution, Bicep, GHA workflows, host.json / staticwebapp.config.json. Default: all of the above when present. Forward-only layers (Business / Motivation / Strategy / Physical) are emitted as typed stubs per reference §7.
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

4. **Layout and naming** per reference §6.4–6.7. Emit each `<view>` with node placements (`x`, `y`, `w`, `h`) so the rendered diagram reads top-to-bottom by layer (Strategy on top, Technology on bottom, Motivation to the left, Implementation & Migration to the right) and left-to-right by aspect. Identifiers are `id-<slug>` in lowercase-with-hyphens per §6.6; `<name>` values follow the element-type conventions in §6.7.

5. **Write the canonical file.** Default location `docs/architecture/<feature>.oef.xml`. If an architect has named a specific path, honour that.

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

3. **Invoke lifting procedures:**
   - `references/procedures/lifting-rules-dotnet.md` → Application Layer elements + intra-Application relationships.
   - `references/procedures/lifting-rules-bicep.md` → Technology Layer elements + Application-to-Technology Assignment / Realisation relationships.
   - `references/procedures/lifting-rules-gha.md` → Implementation & Migration Layer elements.

4. **Emit forward-only stub blocks.** For Business, Motivation, and Strategy — even if the architect did not ask for them — emit a typed stub *only if the diagram kind requires them* (e.g., an Application-to-Business Realisation view without a Business Layer is incomplete). The stub carries the mandatory marker header (reference §7.3):

   ```
   ' =============================================================================
   ' FORWARD-ONLY — this layer was not extracted from source
   ' The architect must fill in: <layer name>
   ' The skill inferred suggestive placeholders from Application element labels
   ' =============================================================================
   ```

   Placeholders are generated from Application Component names — e.g., an `Orders.Api` Component suggests a plausible Business Service label *Order Management*. The architect confirms or rewrites.

5. **Preserve existing model content.** If `docs/architecture/<feature>.oef.xml` exists, merge rather than overwrite: existing element identifiers, `<name>` values, `<documentation>`, properties, view placements, and forward-only content are preserved; extracted elements are added, missing elements are removed (surfaced as drift findings in the footer).

6. **Self-check against reference §10** as in Build.

7. **Emit footer disclosure including the per-layer lift / stub breakdown** — which layers were lifted, which were stubbed, which sources were read.

## Review mode workflow

0. **Dispatch.** Confirm Review mode. Run pre-flight. Identify sub-behaviour:
   - Artefact review (diagram file alone, or diagram + architect asks "is this well-formed").
   - Drift detection (diagram + code/IaC at canonical locations, or architect asks "has this drifted").
   If both apply, run artefact review first, then drift detection.

### Artefact review

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

1. **Invoke `references/procedures/drift-detection.md`.** Re-run the discovery pass from project assimilation against the current code/IaC. Compare the discovered set to the diagram's element set.

2. **Report deltas as `AD-DR-*` findings** — elements added, elements removed, relationships changed. These findings carry `layer: runtime`.

3. **Suggest reconciliation.** For each drift finding, suggest either "update the diagram to match current code" (if code is the source of truth for that layer) or "update the code to match the diagram" (if the architect's model is intentional and code has drifted).

4. **Rollup.** After per-finding output, one paragraph summarising well-formedness health and drift summary.

5. **Emit footer disclosure.**

## Lookup mode workflow

0. **Dispatch.** Confirm Lookup.

1. **Locate.** Grep reference for the concept (element type, relationship, diagram kind, OEF `xsi:type`, Appendix B entry). Load only the matched section.

2. **Answer concisely.** One or two sentences citing the reference section and (if applicable) ArchiMate 3.2 chapter or Appendix B entry. Include the default rule when it's a §4 layer-specific preference or a §5.5 well-formedness rule.

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
<OEF XML document with FORWARD-ONLY comment blocks around stub element sections>

Extraction summary:
  Layers lifted:          Application (<n>), Technology (<n>), Implementation & Migration (<n>)
  Layers stubbed (forward-only): Business, Motivation, Strategy — architect fills in
  Sources read:           <list of files>
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
Diagram kind: <reference §9 kind name>
Layers in scope: <comma-separated>
Self-check: pass | <n failures> | n/a
Project assimilation:
  <block per the Project assimilation section above>
Forward-only layers stubbed: <list, or "none">
Runtime-verified drift: <n findings, or "drift detection not run">
```

## Red flags — stop and re-run

Output contains any of the following? Stop; fix before delivering:

- **Invalid relationship per Appendix B.** Fix per `AD-2`; consult ArchiMate 3.2 Appendix B (Relationships Table).
- **Business Process, Business Function, Business Service, Business Actor, Business Role, or Business Object emitted by Extract mode without a `FORWARD-ONLY` marker.** Fix per `AD-14`; these layers are forward-only by design.
- **Motivation or Strategy elements emitted by Extract mode without a `FORWARD-ONLY` marker.** Fix per `AD-14`.
- **Layer soup** — a single diagram containing Business, Application, Technology, Motivation, and Strategy elements without a clear concern. Fix per `AD-1`; pick one of the six supported diagram kinds (reference §9).
- **Missing Realisation chain** — a Business Service in scope with no Application Service realising it, or an Application Service with no Application Component. Fix per `AD-6`.
- **Active structure directly accessing passive structure** — an Actor drawn accessing a Business Object without a Process / Function in between. Fix per `AD-4`.
- **Association overuse** — more than one Association relationship in a single diagram. Fix per `AD-5`; pick a real relationship.
- **Migration View without a Plateau axis.** Fix per `AD-9`.
- **Extract refused with no guidance.** Fix by suggesting the correct mode (Build) and naming the forward-only layers.
- **Drift finding asserting a pass from static review alone.** Fix: restate as "source-aligned; drift re-check required against current code/IaC."
- **Emitting elements with invalid `xsi:type`.** Every `<element>` and `<relationship>` must use an exact ArchiMate 3.2 type name (reference §6.2 for elements, §6.3 for relationships). Misspellings (`Application_Component`, `app-component`, `ApplicationAPI`) break tool import.
- **View `<node>` or `<connection>` emitted without `xsi:type`.** Fix per `AD-15`; OEF's `ViewNodeType` and `ConnectionType` are abstract complexTypes — `<node>` must carry `xsi:type="Element"` (or `Container` / `Label`) and `<connection>` must carry `xsi:type="Relationship"` (or `Line`). Archi's XSD-validating import rejects bare elements with `cvc-type.2`. `xmllint --noout` does *not* catch this — use `xmllint --schema <url>` or open in Archi.

## Complementary skills

- **`responsive-design`** (same plugin `souroldgeezer-design`) — produces the UI Application Components this skill models. Its Review mode checks for `docs/architecture/<feature>.oef.xml` and dispatches to this skill for drift detection when present.
- **`serverless-api-design`** (same plugin) — produces the HTTP API Application Components and the Technology Layer resources (Cosmos DB, Blob Storage, Key Vault, managed identity, Function Apps) this skill models. Same auto-dispatch pattern in its Review mode.
- **`devsecops-audit`** (plugin `souroldgeezer-audit`) — pipeline and IaC posture audit. Complements this skill: `architecture-design` proves the architecture *model* is well-formed; `devsecops-audit` proves the pipeline and infrastructure posture are secure. The GitHub Actions workflows that become Implementation & Migration Work Packages here are the same workflows audited there.

## Honest limits

- **Extract is bounded by the three extractable layers.** Business, Motivation, Strategy, and Physical are forward-only — no amount of reading code will produce them honestly. Output makes the boundary explicit; architects own the stubs.
- **Drift detection reads the repo, not a live Azure subscription.** The skill detects drift between a diagram and the committed code / IaC state; it does not detect drift between the IaC and actual deployed resources. Real-world drift (someone ran `az` in production) needs Azure Resource Graph or Defender for Cloud, not this skill.
- **Archi-specific canvas features are lost.** OEF is tool-neutral; custom figures, visual group styling, and Archi-specific viewpoint editor state are not round-tripped. Architects who need these edit in Archi directly after the skill's initial import. Reference §6.10.
- **The well-formedness checker is the skill, not the schema.** The skill does not run XSD validation at runtime — emitted files are correct by construction (every `xsi:type` drawn from the ArchiMate 3.2 catalog, every relationship validated against Appendix B in Build and Review). XSD validation is delegated to the architect's toolchain: Archi's import rejects malformed XML; `xmllint --schema http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd <file>.oef.xml` is the explicit path. **`xmllint --noout` alone is not sufficient** — it checks XML well-formedness only and will not catch schema-level issues such as abstract-type violations (`AD-15`). Build's `[static]` self-check passing does not guarantee schema validity — it guarantees ArchiMate well-formedness only.
- **The six supported diagram kinds are a deliberate subset** of ArchiMate's expressive range. ViewPoints and less-common kinds (Product Map, Organisation Structure, Information Structure, Physical) are expressible in OEF but not first-class in v1 — reference §9.
