# Drift detection — existing OEF model vs current code/IaC

Procedure for Review mode's drift sub-behaviour. Compares the element set in `docs/architecture/<feature>.oef.xml` against the current state of code, IaC, and workflows at the canonical paths, and reports deltas as `AD-DR-*` findings.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). Drift-finding codes are defined in [../smell-catalog.md](../smell-catalog.md).

## Inputs

1. **Existing OEF model** at `docs/architecture/<feature>.oef.xml` (required; if absent, drift detection is not applicable and the sub-behaviour is skipped with a note).
2. **Current code / IaC / workflow state**, read via the three lifting procedures:
   - [lifting-rules-dotnet.md](lifting-rules-dotnet.md) — Application Layer.
   - [lifting-rules-bicep.md](lifting-rules-bicep.md) — Technology Layer.
   - [lifting-rules-gha.md](lifting-rules-gha.md) — Implementation & Migration Layer.

Business, Motivation, and Strategy elements in the existing model are **not** subject to drift detection — they are forward-only and architect-owned (reference §7.2). They are reported as `AD-DR-10` (unverifiable; architect ownership) for transparency and then skipped.

## Procedure

### Step 0 — Parse the existing OEF model

Parse the XML and extract:

- **Element set**: each `<element>`'s `identifier`, `xsi:type`, `<name>`, `<documentation>`, properties.
- **Relationship set**: each `<relationship>`'s `identifier`, `xsi:type`, `source`, `target`.
- **View set**: each `<view>`'s `identifier`, `viewpoint`, and node/connection placements (for preserving layout).
- **Forward-only markers**: XML comment blocks (`<!-- FORWARD-ONLY -->`) surrounding stub element sections.

Record which layer each element belongs to based on its `xsi:type` (Business/Application/Technology by `xsi:type` prefix and ArchiMate 3.2 layer assignment per reference §3–§4).

### Step 1 — Run the lifting procedures on current state

Invoke the three lifting procedures in turn. Record the element and relationship set the current code/IaC/workflows *would* produce if the model were built fresh today.

### Step 2 — Diff, layer by layer

#### § Application

Compare Application Components, Services, Interfaces, and intra-Application relationships.

| Delta | Code | Severity |
|---|---|---|
| Component in `*.csproj` / solution without a matching `<element xsi:type="ApplicationComponent">` in the model | `AD-DR-1` | `warn` |
| `<element xsi:type="ApplicationComponent">` in the model without a matching `*.csproj` / solution project, and the element is not marked *planned* or *external* via a `<property>` or `<documentation>` | `AD-DR-2` | `warn` |
| `<ProjectReference>` edge in solution without a matching `<relationship xsi:type="Serving|Composition|Realization">` in the model | `AD-DR-7` | `warn` |
| `<relationship>` in the model between two Components without a `<ProjectReference>` edge between their projects | `AD-DR-7` | `warn` (may be legitimate architect intent — flag, don't block) |
| `<name>` value in the model differs from the canonical project name | `AD-DR-8` | `info` (friendly-name rename is usually fine) |

**Identifier-matching precedence**: exact `identifier` match first (e.g. `id-orders-api` matches the procedure's generated identifier for `Orders.Api`); then `<name>` match; then project-name-stem match. The lifting procedures emit deterministic identifiers (reference §6.6), so the exact-match case is usually sufficient.

#### § Technology

Compare Technology Nodes, System Software, Communication Networks, Paths, Artifacts, and cross-layer Assignment / Serving from Components.

| Delta | Code | Severity |
|---|---|---|
| Bicep resource (compute / data / identity / secrets / network) without a matching `<element>` of the appropriate `xsi:type` in the model | `AD-DR-3` | `warn` |
| `<element xsi:type="Node">` (etc.) in the model without a matching Bicep resource, and the element is not marked *planned* or *out-of-scope* | `AD-DR-4` | `warn` |
| Application-to-Technology relationship implied by code + IaC combination (see [lifting-rules-bicep.md](lifting-rules-bicep.md) "Application-to-Technology linking") that is missing from the model | `AD-DR-7` | `warn` |
| Node `xsi:type` changed (e.g., App Service hosting for a Component changed to Container App — which would shift System Software associations) | `AD-DR-9` | `info` |
| `<name>` value in the model differs from the canonical Bicep `name` property | `AD-DR-8` | `info` |

#### § Implementation & Migration

Compare Work Packages, Plateaus, Gaps, Implementation Events, Deliverables.

| Delta | Code | Severity |
|---|---|---|
| Deploy workflow in `.github/workflows/*.yml` without a matching `<element xsi:type="WorkPackage">` in the model | `AD-DR-5` | `warn` |
| `<element xsi:type="WorkPackage">` in the model without a matching workflow file, and the element is not marked *planned* or *decommissioned* | `AD-DR-6` | `warn` |
| New `environment:` value in workflows (new Plateau) without a matching `<element xsi:type="Plateau">` in the model | `AD-DR-5` | `warn` |
| `<element xsi:type="Plateau">` in the model without any deploy job targeting that environment | `AD-DR-6` | `info` |

#### § Relationships (cross-layer summary)

Apply the general relationship-drift rule: any relationship emitted by the lifting procedures that is missing in the model, or has a reversed `source`/`target`, or has a different `xsi:type`, is `AD-DR-7` at `warn`. Relationships that are in the model but not emitted by the lifting procedures are `AD-DR-7` at `info` (architect may have added them intentionally as aspirational).

#### § Forward-only layers

`<element>`s with `xsi:type` in the Business / Motivation / Strategy / Physical catalog in the existing model are reported as `AD-DR-10` (unverifiable) and skipped. This is not a finding the architect must act on — it is a disclosure.

### Step 3 — Emit per-finding output

Per finding format matches Review mode's per-finding shape (from SKILL.md):

```
[<AD-DR-N>] <file>:<line or element identifier>
  layer:    runtime
  severity: block | warn | info
  evidence: <element identifier or <name> + source file where the mismatch was detected>
  action:   <one-line suggestion — either "update model" or "update code" with brief reason>
  ref:      smell-catalog.md §<AD-DR-N> + procedures/drift-detection.md §<layer section>
```

### Step 4 — Reconciliation suggestions

For each drift finding, suggest:

- **"Update the model"** when the code / IaC / workflow state is the intended source of truth and the model has fallen behind (most common for `AD-DR-1`, `AD-DR-3`, `AD-DR-5`, `AD-DR-7` when code is newer).
- **"Update the code"** when the model encodes an architectural decision that the code has drifted from (most common for `AD-DR-2`, `AD-DR-4`, `AD-DR-6` when the model shows a *planned* shape and the architect wants the code to catch up).
- **"Annotate as planned / external / out-of-scope"** when the element legitimately has no code counterpart (e.g., a third-party service modelled for completeness). Annotation is expressed via a `<property propertyDefinitionRef="…"><value>planned</value></property>` on the element, or via `<documentation>`. Extract preserves these annotations across re-runs.

The skill offers the suggestion; the architect picks.

### Step 5 — Drift rollup

After per-finding output, emit a single summary block:

```
Drift summary (docs/architecture/<feature>.oef.xml vs current repo state):
  Application:           <n_added> added, <n_removed> removed, <n_relationship> relationship deltas
  Technology:            <n_added> added, <n_removed> removed, <n_relationship> relationship deltas
  Impl & Migration:      <n_added> added, <n_removed> removed
  Forward-only layers:   <n_elements> unverifiable (AD-DR-10 reported)
  Model last modified:   <git-log date for the .oef.xml>
  View layouts:          <n_views preserved> views with architect-placed layout retained
  Drift run vs now:      <n_total> findings, <n_block>/<n_warn>/<n_info>
```

## What drift detection does not do

- **Connect to Azure or other live subscriptions.** The skill reads repository state only — `.csproj`, Bicep, `host.json`, `.github/workflows/`. If the IaC has been bypassed by manual `az` or portal changes, the deployed reality and the IaC diverge, but drift detection only sees the IaC. Escalate to Azure Resource Graph / Defender for Cloud drift-detection reports for live verification.
- **Validate the architectural intent behind the drift.** The skill reports that a Component was added; it does not judge whether the addition was wise. That judgement is the architect's.
- **Auto-apply reconciliation.** The skill proposes "update model" or "update code"; it does not run Build or Extract to perform the update unless the architect explicitly invokes that mode next.
- **Run XSD validation.** Drift detection is a *semantic* diff, not an XML-schema check. An emitted file is correct by construction (reference §6); if an architect's hand-edit produces a structurally invalid file, the downstream tool (Archi, `xmllint`) reports that, not drift detection.
- **Run across multiple feature models.** A single invocation checks a single `<feature>.oef.xml`. Fan-out across all files at `docs/architecture/*.oef.xml` is a future enhancement.
