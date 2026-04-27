# Architecture Design Smell Catalog

Compact lookup table for every finding code the skill emits. The rubric prose lives in [../../../docs/architecture-reference/architecture.md](../../../docs/architecture-reference/architecture.md); drift-detection semantics live in [procedures/drift-detection.md](procedures/drift-detection.md). This file is a code-to-section-pointer index. Findings in review output cite codes from this catalog and never restate the rubric.

**Rules enforced by the skill:**

1. Cite codes, do not restate the rubric.
2. One severity per finding: `block` | `warn` | `info`. Don't stack.
3. `layer: static` for artefact smells (readable from the OEF XML source); `layer: runtime` for drift smells (requires reading current code / IaC / workflows).

## Artefact smells — `AD-*`

Readable from the `.oef.xml` source alone. Rubric: `architecture.md` §8.

| Code | Rubric | Description (one line; see rubric for full) |
|---|---|---|
| `AD-1` | §8 | Layer soup — a single diagram mixing Business / Application / Technology / Motivation / Strategy without a clear concern |
| `AD-2` | §8, §5, ArchiMate® 3.2 Appendix B | Invalid relationship per the Relationships Table — e.g., Business Process *realising* a Technology Node |
| `AD-3` | §8, §2.3 | Double aspect — element stereotyped as both Active structure and Behaviour |
| `AD-4` | §8, §2.3 | Active structure directly accessing passive structure without a Behaviour element in between |
| `AD-5` | §8 | Association overuse — more than one Association per diagram, or Association used where a typed relationship fits |
| `AD-6` | §8, §9.3 | Missing Realisation chain — Business Service with no realising Application Service, or Application Service with no realising Application Component |
| `AD-7` | §8, §3.3, §2.4 | Core / extension mixing without cause — Core view containing Motivation elements, or vice versa |
| `AD-8` | §8, §6.6–§6.7 | Identifier / `<name>` mismatch — element `identifier` slug carries different semantics than its `<name>` value |
| `AD-9` | §8, §9.5 | Migration view without Plateau axis |
| `AD-10` | §8 | Motivation elements in a non-Motivation view without a Realisation relationship |
| `AD-11` | §8, §4.8 | Empty Grouping, or Grouping used purely for visual framing |
| `AD-12` | §8, §4.3 | Technology Layer diagram reasoning about latency or residency without Path / Communication Network elements |
| `AD-13` | §8, §4.1 | Ambiguous Product / Contract / Service — Product modelled with Service semantics or vice versa; Contract used as a documentation placeholder |
| `AD-14` | §8, §7.3 | Forward-only layer (Business Actor / Role / Collaboration / Object / Contract / Product / Service / Function / Motivation / Strategy) emitted by Extract without the `FORWARD-ONLY — architect fills in` marker block |
| `AD-14-LC` | §8, §7.4 | Business Process / Event / Interaction emitted by Extract without the per-element `LIFT-CANDIDATE — architect confirms: source=..., confidence=...` XML comment (missing marker or missing required `source=` / `confidence=` attribute) |
| `AD-15` | §8, §6.4 | View `<node>` or `<connection>` emitted without an `xsi:type` (abstract complexType violates OEF schema) |
| `AD-16` | §8, §6.1a | Metadata catalog payload emitted in the ArchiMate namespace instead of a non-ArchiMate catalog namespace |
| `AD-17` | §8, §6 | Invalid top-level `<model>` child or child sequence, including model-root `<properties>` |
| `AD-18` | §8, §7.1 | Invisible RBAC — RBAC-only technology resource is served/used without a Managed Identity Access path |
| `AD-19` | §8, §9.5 | Fictitious plateaus — Extract emitted deployment Plateaus with no workflow/IaC/environment evidence |
| `AD-20` | §8, §9.5 | Plateau triggering without migration intent — parallel deployment Plateaus connected as if one becomes the next |
| `AD-21` | §8, §9.2 | Unbounded external component — external Application Component is not aggregated into an external trust-boundary Grouping |

## Professional artifact quality smells — `AD-Q*`

Readable from the `.oef.xml` source alone. Rubric: `architecture.md` §2.8, §8 *Professional artefact quality smells*, §9 professional gates, and §10.

| Code | Rubric | Description (one line; see rubric for full) |
|---|---|---|
| `AD-Q1` | §2.8, §8 AD-Q, §10 | Inventory view — discovered elements are listed but the view does not answer an architecture question |
| `AD-Q2` | §8 AD-Q, §9 | Viewpoint mismatch — selected viewpoint does not match the concern being communicated |
| `AD-Q3` | §8 AD-Q, §10 | Unreviewable density — technically laid out but too crowded for practical review |
| `AD-Q4` | §8 AD-Q, §10 | Weak visual hierarchy — all nodes / relationships appear equally important, hiding the architecture point |
| `AD-Q5` | §8 AD-Q, §10 | Extraction leakage — implementation trivia appears in a conceptual or stakeholder-facing view |
| `AD-Q6` | §8 AD-Q, §10 | Relationship noise — mechanically complete relationships obscure the main dependency, realisation, or process path |
| `AD-Q7` | §8 AD-Q, §9.6, §10 | Orphaned decision context — motivation elements are not connected to affected architecture elements or decisions |
| `AD-Q8` | §8 AD-Q, §9.7, §10 | Process thinness — process view omits handoffs, responsibilities, trigger / flow, or value outcome |
| `AD-Q9` | §8 AD-Q, §9.3, §10 | Service Realization thinness — services are named but the realization chain is not auditable |
| `AD-Q10` | §8 AD-Q, §10 | Label ambiguity — labels are too generic, duplicated, or code-shaped for the intended audience |

## Layout smells — `AD-L*`

Readable from the `.oef.xml` source alone. Rubric: `architecture.md` §8 *Layout smells*; structural contract: §6.4a; algorithm: [procedures/layout-strategy.md](procedures/layout-strategy.md).

| Code | Rubric | Description (one line; see rubric for full) |
|---|---|---|
| `AD-L1` | §8 layout, §6.4a | Layer-ordering violation — element's `y` falls outside the relative ordering of its ArchiMate layer (Strategy above Business above Application above Technology above Physical) after Phase 6 bbox normalisation |
| `AD-L2` | §8 layout, §6.4a | Node overlap — two placements at the same nesting depth whose bounding boxes intersect |
| `AD-L3` | §8 layout, §6.4a | Undersize — `w < 120`, `h < 55`, or `w` too small to avoid label truncation |
| `AD-L4` | §8 layout, §6.4a | View density over budget — `>20` elements, `>30` relationships, or nesting depth `>2` |
| `AD-L5` | §8 layout, §6.4a | Excessive edge crossings — `crossings > node_count / 6` (was `node_count / 4`; threshold tightened in 0.8.0 because Sugiyama's 4-pass barycentric materially reduces crossings vs the prior 1-pass procedure) |
| `AD-L6` | §8 layout, §6.4a | Non-orthogonal routing — diagonal `<connection>` with no `<bendpoint>` between non-aligned endpoints |
| `AD-L7` | §8 layout, §6.4a | Nested-plus-edge — child nested in parent *and* the parent-child `<connection>` drawn in the same view |
| `AD-L8` | §8 layout, §6.4a | Off-grid — `x`, `y`, `w`, `h`, or `<bendpoint>` not a multiple of 10 |
| `AD-L9` | §8 layout, §6.4a | Hierarchy not respected — Realization / Used-by / Serving relationship between same-layer elements drawn against topological direction (e.g. realised-by-edge points up the layer when the realised element is below). Detected by Tier 1 phase 1 (cycle handling) + phase 3 (topological sort) failures. |
| `AD-L10` | §8 layout, §6.4a | Canvas not normalised — top-left of the used region (smallest `x` / `y` over all `<node>` placements + `<bendpoint>`s) is not at `(40, 40) ± 10 px`. Tier 1 phase 6 (bbox normalisation) emits this naturally; smell catches non-normalised legacy or hand-shifted output. |
| `AD-L11` | §8 layout, §6.4a | Connector-through-node — a `<connection>` segment crosses a node that is neither source, target, nor required source/target ancestor container |
| `AD-L12` | §8 layout, §6.4a | View-orphan element — non-legend node has no same-view connection |
| `AD-L13` | §8 layout, §6.4a | Stacked connector lane — visible connectors share a lane closely enough to overlap arrowheads or labels |
| `AD-L14` | §8 layout, §6.4a | Wide empty layer gap — excessive vertical whitespace separates occupied layer bands |
| `AD-L15` | §8 layout, §6.4a | Local fan-out crisscross — high-degree local edges cross each other or a non-endpoint sibling |

## Process-flow smells — `AD-B-*`

Readable from the `.oef.xml` source alone. Rubric: `architecture.md` §8 *Process-flow smells*; diagram kinds: §9.7 (Business Process Cooperation) and §9.3 (Service Realization); between-view invariant: §7.4.

| Code | Rubric | Description (one line; see rubric for full) |
|---|---|---|
| `AD-B-1` | §8 AD-B, §9.7 | Missing trigger chain — §9.7 view where two or more Behaviour elements (Business Process / Event / Interaction) are not linked by any Triggering / Flow relationship into one temporal chain |
| `AD-B-2` | §8 AD-B, §9.7, §2.3 | Disconnected participant — Business Actor / Role / Collaboration in a §9.7 view with no Assignment to any Behaviour element |
| `AD-B-3` | §8 AD-B, §9.7 | Orphan Business Object — Business Object / Contract / Product / Data Object in a §9.7 view with no Access from any Behaviour element |
| `AD-B-4` | §8 AD-B, §9.7, §2.4 | Non-Business element in §9.7 — Application / Technology / Motivation / Strategy element present in a Business Process Cooperation view |
| `AD-B-5` | §8 AD-B, §9.7 | Chain without entry or exit — §9.7 chain has no Business Event at its origin and no terminal Business Service / Event |
| `AD-B-6` | §8 AD-B, §9.3 | §9.3 view (Process-rooted modality) with a Business Process at top but no Application Service realising it |
| `AD-B-7` | §8 AD-B, §9.3 | §9.3 view with an Application Service but no Application Component realising it |
| `AD-B-8` | §8 AD-B, §9.7, §9.3, §7.4 | Orphan Business Process (§9.7 end) — Business Process in a §9.7 view has no Realisation chain into any §9.3 view (Process-rooted modality) for the same feature |
| `AD-B-9` | §8 AD-B, §9.3, §9.7, §7.4 | Orphan Application Service (§9.3 end) — Application Service in a §9.3 view (Process-rooted modality) realises no Business Process present in any §9.7 view for the same feature |
| `AD-B-10` | §8 AD-B, §9.3, §4.1 | User-driven process without UI entry point — §9.3 view (Process-rooted modality) for a Business Process carrying a Business Actor Assignment lacks a UI Application Component and Application Interface |
| `AD-B-11` | §8 AD-B, §9.7 | Single-process cooperation view — Business Process Cooperation view contains exactly one Business Process |
| `AD-B-12` | §8 AD-B, §9.3, §7.4 | Sub-process without its own §9.3 drill-down view, unless `propid-drilldown-exclude=true` is set |
| `AD-B-13` | §8 AD-B, §9.7, §7.4 | Top-level Business Process missing from the feature's §9.7 cooperation view, unless `propid-coop-view-exclude=true` is set |

## Drift smells — `AD-DR-*`

Require reading current code / IaC / workflow state against the diagram. Procedure: [procedures/drift-detection.md](procedures/drift-detection.md).

| Code | Procedure §, rubric | Description |
|---|---|---|
| `AD-DR-1` | drift §Application, `architecture.md` §7.1 | Application Component exists in `*.csproj` / solution but is missing from the diagram |
| `AD-DR-2` | drift §Application, `architecture.md` §7.1 | Application Component exists in the diagram but has no corresponding `*.csproj` / solution project (not marked *planned* or *external*) |
| `AD-DR-3` | drift §Technology, `architecture.md` §7.1 | Technology Node exists in Bicep / IaC but is missing from the diagram |
| `AD-DR-4` | drift §Technology, `architecture.md` §7.1 | Technology Node exists in the diagram but has no corresponding IaC resource (not marked *planned* or *out-of-scope*) |
| `AD-DR-5` | drift §ImplMigration, `architecture.md` §7.1 | Work Package exists in `.github/workflows/` but is missing from the diagram |
| `AD-DR-6` | drift §ImplMigration, `architecture.md` §7.1 | Work Package exists in the diagram but has no corresponding workflow file |
| `AD-DR-7` | drift §Relationships, `architecture.md` §5 | Application-to-Technology Assignment / Realisation relationship implied by IaC (`<ProjectReference>` or Bicep `dependsOn`) is missing or reversed in the diagram |
| `AD-DR-8` | drift §Labels, `architecture.md` §6.5 | Element label in the diagram differs from the canonical label in source (e.g., project renamed; Bicep resource renamed; workflow renamed). Low severity: architect may have chosen a human-friendly label intentionally |
| `AD-DR-9` | drift §LayerAssignment, `architecture.md` §3 | Layer assignment drift — an element now hosted by different System Software / on a different Node class than the diagram shows (e.g., moved from App Service to Container Apps) |
| `AD-DR-10` | drift §ForwardOnly, `architecture.md` §7.2 | Business / Motivation / Strategy element appears in the current diagram without a `FORWARD-ONLY` marker; drift detection cannot verify these — reported as *unverifiable; architect ownership* |
| `AD-DR-11` | drift §Process, `architecture.md` §7.4 | Model process has no code — Business Process / Event / Interaction in `docs/architecture/**/*.oef.xml` has no matching Durable Functions orchestrator or Logic Apps workflow (either by `LIFT-CANDIDATE source=` mismatch or by `<name>` mismatch when no marker is present) and no `planned` / `external` property |
| `AD-DR-12` | drift §Process, `architecture.md` §7.4 | Code workflow has no model — Durable Functions orchestrator or Logic Apps workflow exists in the repo but no Business Process in any OEF file references it (directly or via `LIFT-CANDIDATE source=`) |

## Severity defaults

| Code range | Default severity | Rationale |
|---|---|---|
| `AD-1`, `AD-2`, `AD-14`, `AD-14-LC`, `AD-15`, `AD-16`, `AD-17` | `block` | Hard ArchiMate 3.2 / OEF violations (layer discipline, Appendix B well-formedness, marker discipline, schema-import discipline) |
| `AD-3`, `AD-4`, `AD-6`, `AD-9`, `AD-18`, `AD-20`, `AD-21` | `block` | Aspect / Realisation / Migration-axis / security-boundary discipline; rendering the diagram incoherent or misleading |
| `AD-5`, `AD-7`, `AD-8`, `AD-10`, `AD-12`, `AD-13`, `AD-19` | `warn` | Legible but imprecise; diagram reads but makes a claim the model doesn't support |
| `AD-Q1`, `AD-Q2`, `AD-Q8`, `AD-Q9` | `warn` | Professional-readiness blockers — the model may be valid, but the view does not yet carry its intended architecture message |
| `AD-Q3`, `AD-Q4`, `AD-Q5`, `AD-Q6`, `AD-Q7`, `AD-Q10` | `info` by default; escalate to `warn` when the affected view is claimed as `review-ready` | Quality degradations; severity depends on whether the artefact is a draft or presented for review |
| `AD-B-4` | `block` | Layer soup in a §9.7 view (view-kind-specific tightening of `AD-1` / `AD-7`) |
| `AD-B-1`, `AD-B-2`, `AD-B-3`, `AD-B-5`, `AD-B-6`, `AD-B-7`, `AD-B-8`, `AD-B-9`, `AD-B-10`, `AD-B-11`, `AD-B-12`, `AD-B-13` | `warn` | Process diagram is legible but has missing participants, missing realisation, or a broken between-view invariant |
| `AD-DR-11`, `AD-DR-12` | `warn` | Real process drift between the model and backend workflow sources; architect decides which side reconciles |
| `AD-11` | `info` | Cosmetic unless it obscures a required trust-boundary Grouping; use `AD-21` for missing external trust boundaries |
| `AD-DR-1` through `AD-DR-7` | `warn` | Real drift; architect decides whether the diagram or the code is the source of truth |
| `AD-DR-8`, `AD-DR-9`, `AD-DR-10` | `info` | Drift likely, but plausible architect-chosen divergence (friendly labels, planned Plateau transitions, forward-only ownership) |
| `AD-L1` | `warn` | Structural layout failure against the §6.4a contract |
| `AD-L2`, `AD-L3` | `warn` | Structural layout failures — diagram is misleading or unreadable (overlap, truncated label) |
| `AD-L4`, `AD-L7` | `warn` | Readability / representation failures — over-budget view, or a relationship drawn twice |
| `AD-L5`, `AD-L6`, `AD-L8` | `info` | Polish — crossings above heuristic threshold, mixed routing style, off-grid coordinates |
| `AD-L9`, `AD-L12`, `AD-L13`, `AD-L14`, `AD-L15` | `warn` | Mechanical layout/readability failures that should be fixed before diagram-readable or review-ready output |
| `AD-L11` | `block` | Connector crossing an unrelated node body creates false visual semantics; professional readiness cannot exceed `model-valid` |
| `AD-L10` | `info` | Polish — canvas not normalised at `(40, 40) ± 10 px` origin; architect may have hand-shifted |

Severity can be overridden per finding when evidence warrants (e.g., `AD-DR-8` escalated to `warn` when the renamed project is the feature's primary Component and every other diagram also shows the old name).
