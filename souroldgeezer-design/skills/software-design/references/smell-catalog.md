# Software Design Smell Catalog

Use this catalog with [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md). Findings should cite the smell code, evidence, smallest corrective action, verification layer, and reference section.

Severity defaults are starting points. Raise severity when the smell is in new code, sits on a load-bearing path, or blocks the requested change. Lower severity when the evidence is partial or the design has a clear local justification.

## Waste And Unnecessary Design

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-W-1` | Speculative interface | Interface has one implementation and no current variation, test seam, or boundary need. | warn |
| `SD-W-2` | Future-proof framework | Plugin system, generic pipeline, message bus, or rule engine added for imagined cases. | block when mandatory |
| `SD-W-3` | Unused extension point | Hooks/options exist but no caller uses them. | warn |
| `SD-W-4` | Inventory layer | Pass-through layer adds files but no policy, translation, or protection. | warn |
| `SD-W-5` | Repeated data model | Same shape copied between layers without semantic difference. | warn |
| `SD-W-6` | Ceremony over change | Pattern count exceeds the current use case's complexity. | warn |

## Boundary And Responsibility

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-B-1` | Responsibility drift | Module changes for unrelated reasons. | warn |
| `SD-B-2` | Folder-type boundary | Boundary mirrors controllers/services/repositories instead of volatility or ownership. | info |
| `SD-B-3` | Leaky module | External code reaches into internals, persistence details, or mutable state. | block when new |
| `SD-B-4` | Hidden mutable state | Shared mutable singleton/cache/config controls domain behavior across boundaries. | block |
| `SD-B-5` | Misplaced policy | Domain decision lives in transport, UI, storage, scheduler, or integration code. | warn |
| `SD-B-6` | Adapter owns workflow | External integration adapter becomes the owner of internal business flow. | warn |

## Coupling And Dependency Direction

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-C-1` | Dependency cycle | Modules/projects/packages reference each other directly or indirectly. | block |
| `SD-C-2` | Boundary inversion | Stable policy depends on adapter/framework/storage detail. | block when new |
| `SD-C-3` | Shared-core trap | Shared module attracts unrelated domain policy. | warn |
| `SD-C-4` | Fan-out hotspot | One module must know too many concrete collaborators. | warn |
| `SD-C-5` | Service locator coupling | Runtime lookup hides concrete dependencies and ownership. | warn |
| `SD-C-6` | Event/config backchannel | Modules couple through shared config, events, or names with no explicit contract. | warn |

## Semantic Coherence

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-S-1` | Vocabulary split | Same concept has multiple names in one boundary. | warn |
| `SD-S-2` | Homonym concept | Same term means different things in one boundary. | warn |
| `SD-S-3` | Aggregate leakage | Internal state/invariant model is changed from outside its owner. | block when invariant-bearing |
| `SD-S-4` | Convenience shared kernel | Shared model exists without shared ownership and change protocol. | warn |
| `SD-S-5` | Missing translation | External/legacy/partner vocabulary flows into internal policy. | warn |

## Evolution And Refactoring Safety

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-E-1` | Shotgun change risk | A likely change requires edits across many modules or owners. | warn |
| `SD-E-2` | Unsafe refactor jump | Proposed redesign lacks characterization, specification, runtime, or human evidence. | warn |
| `SD-E-3` | Flag pile-up | Behavior branches multiply in one module instead of revealing a boundary. | warn |
| `SD-E-4` | Permanent strangler | Old and new paths coexist without retirement criteria. | warn |

## Quality-Attribute Tradeoff

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-Q-1` | Unstated tradeoff | Design optimizes a quality attribute without naming the cost. | warn |
| `SD-Q-2` | Local optimization | Performance/cost tactic increases design complexity without measurement. | info |
| `SD-Q-3` | Specialist concern absorbed | API, UI, security, test, or architecture-model concern is handled here instead of delegated. | warn |

## Socio-Technical Fit

| Code | Name | Signal | Default |
|---|---|---|---|
| `SD-T-1` | Ownership mismatch | Boundary forces frequent coordination between unrelated owners. | warn when human evidence exists |
| `SD-T-2` | Cognitive load cliff | Small change requires understanding too many concepts, frameworks, or conventions. | warn |
| `SD-T-3` | Orphaned shared code | Shared module has no clear owner or change protocol. | warn |
