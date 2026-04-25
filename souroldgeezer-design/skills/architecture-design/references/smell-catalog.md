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
| `AD-2` | §8, §5, ArchiMate 3.2 Appendix B | Invalid relationship per the Relationships Table — e.g., Business Process *realising* a Technology Node |
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

## Layout smells — `AD-L*`

Readable from the `.oef.xml` source alone. Rubric: `architecture.md` §8 *Layout smells*; structural contract: §6.4a; algorithm: [procedures/layout-strategy.md](procedures/layout-strategy.md).

| Code | Rubric | Description (one line; see rubric for full) |
|---|---|---|
| `AD-L1` | §8 layout, §6.4a | Layer-ordering violation — element's `y` falls outside the relative ordering of its ArchiMate layer (Strategy above Business above Application above Technology above Physical) after Phase 6 bbox normalisation. Severity is conditional on the §6.4a banding marker (see severity-defaults table). |
| `AD-L2` | §8 layout, §6.4a | Node overlap — two placements at the same nesting depth whose bounding boxes intersect |
| `AD-L3` | §8 layout, §6.4a | Undersize — `w < 120`, `h < 55`, or `w` too small to avoid label truncation |
| `AD-L4` | §8 layout, §6.4a | View density over budget — `>20` elements, `>30` relationships, or nesting depth `>2` |
| `AD-L5` | §8 layout, §6.4a | Excessive edge crossings — `crossings > node_count / 4` |
| `AD-L6` | §8 layout, §6.4a | Non-orthogonal routing — diagonal `<connection>` with no `<bendpoint>` between non-aligned endpoints |
| `AD-L7` | §8 layout, §6.4a | Nested-plus-edge — child nested in parent *and* the parent-child `<connection>` drawn in the same view |
| `AD-L8` | §8 layout, §6.4a | Off-grid — `x`, `y`, `w`, `h`, or `<bendpoint>` not a multiple of 10 |

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
| `AD-1`, `AD-2`, `AD-14`, `AD-14-LC` | `block` | Hard ArchiMate 3.2 violations (layer discipline, Appendix B well-formedness, forward-only / lift-candidate marker discipline) |
| `AD-3`, `AD-4`, `AD-6`, `AD-9` | `block` | Aspect / Realisation / Migration-axis discipline; rendering the diagram incoherent |
| `AD-5`, `AD-7`, `AD-8`, `AD-10`, `AD-12`, `AD-13` | `warn` | Legible but imprecise; diagram reads but makes a claim the model doesn't support |
| `AD-B-4` | `block` | Layer soup in a §9.7 view (view-kind-specific tightening of `AD-1` / `AD-7`) |
| `AD-B-1`, `AD-B-2`, `AD-B-3`, `AD-B-5`, `AD-B-6`, `AD-B-7`, `AD-B-8`, `AD-B-9`, `AD-B-10` | `warn` | Process diagram is legible but has missing participants, missing realisation, or a broken between-view invariant |
| `AD-DR-11`, `AD-DR-12` | `warn` | Real process drift between the model and backend workflow sources; architect decides which side reconciles |
| `AD-11` | `info` | Cosmetic |
| `AD-DR-1` through `AD-DR-7` | `warn` | Real drift; architect decides whether the diagram or the code is the source of truth |
| `AD-DR-8`, `AD-DR-9`, `AD-DR-10` | `info` | Drift likely, but plausible architect-chosen divergence (friendly labels, planned Plateau transitions, forward-only ownership) |
| `AD-L1` | `warn` when model carries `propid-archi-model-banded=v1`; `info` when marker absent | Structural layout failure when the model claims §6.4a conformance and breaks it; soft-graded on legacy files preserved across Extract refresh per reference §6.4a *Banding marker* |
| `AD-L2`, `AD-L3` | `warn` | Structural layout failures — diagram is misleading or unreadable (overlap, truncated label) |
| `AD-L4`, `AD-L7` | `warn` | Readability / representation failures — over-budget view, or a relationship drawn twice |
| `AD-L5`, `AD-L6`, `AD-L8` | `info` | Polish — crossings above heuristic threshold, mixed routing style, off-grid coordinates |

Severity can be overridden per finding when evidence warrants (e.g., `AD-DR-8` escalated to `warn` when the renamed project is the feature's primary Component and every other diagram also shows the old name).
