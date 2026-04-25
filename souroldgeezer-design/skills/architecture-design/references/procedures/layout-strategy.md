# Layout strategy — Sugiyama-v1 engine for OEF XML views

Procedure for producing `<view>` node placements that are readable, diff-stable, and round-trippable through ArchiMate® conformant tools. Invoked by Build (always) and Extract (when an existing diagram has no prior view placements for the elements being added). Review uses the same rules — restated as checks — to flag `AD-L*` smells.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md); the structural rules this procedure operationalises live in §6.4a *Layout strategy*. Layout smell codes are defined in [../smell-catalog.md](../smell-catalog.md) (`AD-L1..AD-L11`).

**Determinism is the point.** Given the same element set, relationship set, diagram kind, and layer scope, the procedure must produce the same `x`, `y`, `w`, `h` values every run. Re-extracts don't churn coordinates; git diffs on `.oef.xml` stay narrow; architect hand-edits survive because identifiers are preserved (reference §6.6) and layout is recomputed only for elements without an architect-chosen position.

## The three tiers

The procedure is a deterministic three-tier pipeline:

1. **Tier 0 — Pre-flight.** Preserve architect-positioned `<node>` placements verbatim. Identify the §6.4a banding marker (`propid-archi-model-banded` value `v1`, `v2`, or absent).
2. **Tier 1 — Sugiyama-v1 core engine.** Six phases — cycle handling, layer assignment, within-layer ordering (4-pass barycentric crossing minimisation), coordinate assignment (median heuristic), Manhattan A* edge routing, bounding-box normalisation.
3. **Tier 2 — Per-viewpoint specialisations.** One sub-procedure per §9 viewpoint that overrides Tier 1 phases for the diagram-kind in scope.

Run Tier 0 → Tier 1 → Tier 2 in order. Tier 2 may short-circuit Tier 1 phases (see each specialisation's "Replaces phases" line).

## Tier 0 — Pre-flight

### Step 1 — Preserve architect positions

If a prior view exists at the canonical path and contains a `<node>` for this element (matched by `elementRef`), reuse its `x`, `y`, `w`, `h` verbatim. Do not recompute. The architect's hand-edit is authoritative.

Record the set of *new* elements (present in this run, absent from the prior view) — only these get algorithmic placement.

### Step 2 — Read the banding marker

Inspect `<property propertyDefinitionRef="propid-archi-model-banded">` on the model root. Possible values:

- `v2` — file was authored under the Sugiyama-v1 engine (this procedure). New elements use the full Tier 1 / Tier 2 pipeline; existing layout is consistent.
- `v1` — legacy file from pre-0.8.0 banded-grid layout. Preserve all coordinates verbatim per Step 1 above; **never auto-inject the v2 marker** — auto-injection would assert §6.4a v2 conformance over coordinates that pre-date it. Architects rebrand a legacy file by re-running Build for the affected views, which writes a fresh `v2` marker.
- (absent) — pre-§6.4a legacy. Same preservation behaviour as `v1`.

Build emits `v2` on every new file (no prior view at canonical path).

## Tier 1 — Sugiyama-v1 core engine

Run phases 1–6 in order. Each phase consumes the output of prior phases.

### Phase 1 — Cycle handling

Detect cycles in the same-layer relationship sub-graph for each ArchiMate layer:

1. Build a directed graph `G_layer` for each layer where vertices = elements in that layer, edges = Realisation / Composition / Used-by / Serving relationships whose source AND target both fall in this layer.
2. Run a DFS-based cycle detection (Tarjan's algorithm, simplified): mark each vertex `unvisited` / `visiting` / `done`. A back-edge from a `visiting` vertex to another `visiting` vertex is a feedback edge.
3. Mark feedback edges with an internal flag `is-feedback=true`. Do NOT reverse the edge — ArchiMate edge directions carry semantics. Phase 5 routes feedback edges last for crossing-minimisation purposes; otherwise they're treated normally.

**Cycles are uncommon in well-formed ArchiMate models.** Used-by, Realisation, and Composition typically form trees within a layer. Phase 1 is a no-op on most inputs — don't search exhaustively when no cycle exists. If the layer has fewer than 3 same-layer edges, skip the search.

After Phase 1, the same-layer sub-graph minus feedback edges is a DAG, ready for topological sort in Phase 3.

### Phase 2 — Layer assignment

ArchiMate layer is given by the element's `xsi:type`:

| Element types | Layer |
|---|---|
| `Resource`, `Capability`, `ValueStream`, `CourseOfAction` | Strategy |
| `BusinessActor`, `BusinessRole`, ..., `BusinessObject`, `Contract`, `Product` | Business |
| `ApplicationComponent`, `ApplicationCollaboration`, ..., `DataObject` | Application |
| `Node`, `Device`, `SystemSoftware`, ..., `Artifact` | Technology |
| `Equipment`, `Facility`, `DistributionNetwork`, `Material` | Physical |

Motivation and Implementation & Migration columns span all five rows; their elements take the row of their Realisation target (or the row of the element they are assigned to). Default to Application row when no target.

Composite types (`Location`, `Grouping`) inherit the row of their dominant child element class. A Grouping containing only Application Components gets the Application row.

Output of Phase 2: each element has a `layer` ∈ {Strategy, Business, Application, Technology, Physical}.

### Phase 3 — Within-layer ordering

For each layer in top-to-bottom order (Strategy first):

1. **Topological sort.** Compute the topological order of the same-layer DAG (post-Phase 1 cycle handling). Ties broken by aspect column (Active < Behaviour < Passive < Motivation < Implementation & Migration), then identifier ascending.
2. **Aspect bias.** Within the topological order, group by aspect column — elements in the same aspect cluster together. This preserves the §2.3 default reading direction.

Then run **4 passes** of barycentric crossing-minimisation between adjacent layers (current procedure had 1 pass):

- **Pass 1 (top-down):** for each layer L from top to top+1, ..., top+(N-1): for each element `e` in layer L+1, compute `bary(e) = mean(index(n) for n in neighbours(e) where n in layer L)`. Re-sort layer L+1 by `bary(e)` ascending. Elements with no neighbours in layer L keep their Phase 3 step-1 order.
- **Pass 2 (bottom-up):** symmetric, layer L compared against layer L-1.
- **Pass 3 (top-down):** same as Pass 1 — refines convergence.
- **Pass 4 (bottom-up):** same as Pass 2.

After 4 passes, `cell_elements[layer, aspect, position]` is locked. Phase 4 reads this for coordinate computation.

**Tiebreak in barycentric:** identifier ascending (preserves determinism).

**Skip degenerate layers.** Layers with fewer than 2 elements skip the barycentric pass for that layer (no crossings possible).

### Phase 4 — Coordinate assignment

Operates **layer-by-layer top-to-bottom** (Strategy first, Physical last). Upper layers' coordinates are fixed before lower layers compute their medians, so the "median of in-edge source x-coordinates" is well-defined.

For each layer in top-down order:

1. **Compute `y` for the layer.** `y_layer_top = max(y_max_above + 60, 40)` where `y_max_above` = bottom of the lowest-placed element in the layer immediately above (or 0 if Strategy is the first populated layer). 60 px is the **layer gutter** (was 40 in pre-0.8.0).
2. **Compute `x` for each element in the layer.** Iterate elements in the order locked by Phase 3:
   - If the element has cross-layer incoming edges from already-placed upper layers, set `x = median of source x-coordinates`.
   - Else, set `x = aspect-column default centre`. The aspect-column boundaries (preserved as the macro-grid anchor): Motivation x ∈ [40, 280], Active structure [300, 540], Behaviour [560, 800], Passive structure [820, 1060], Implementation & Migration [1080, 1320]. Default centre = `(start + end) / 2 - element.w / 2`.
   - Round `x` to the nearest 10 px.
   - **On collision** (proposed `(x, y)` overlaps an already-placed element in this layer): bump `x` right by `20 + element.w` (sibling gutter is 40 px; element width plus 40 px gives this offset). Repeat until no collision.
3. **Compute `y` per element within the layer.** First element in the layer's first aspect column at `y_layer_top + 20` (top padding inside the layer band). Subsequent elements in the same aspect column at `y_prev + element.h + 40` (sibling gutter, was 20 in pre-0.8.0). Different aspect columns reset to `y_layer_top + 20`.

**Default sizes** (per reference §6.4a, 0.8.0):

| Element class | `w` | `h` |
|---|---:|---:|
| Structure (Component, Node, Device, System Software, Actor, Role, Interface, Artifact) | 160 | 64 |
| Behaviour (Process, Function, Interaction, Service, Event) | 180 | 64 |
| Motivation (Goal, Requirement, Constraint, Principle, Driver, Assessment, Stakeholder, Outcome, Value, Meaning) | 180 | 64 |
| Strategy (Capability, Value Stream, Resource, Course of Action) | 180 | 64 |
| Passive (Business Object, Data Object, Contract, Product) | 140 | 64 |
| Implementation & Migration (Work Package, Deliverable, Implementation Event, Plateau, Gap) | 180 | 64 |
| Grouping | computed; minimum 240 × 140 |
| Junction | 14 × 14 |

When a `<name>` is long enough that the default `w` would truncate, enlarge `w` in 20-px steps (assume 7 px per character at the default Archi font).

**Bounding-box normalisation runs in Phase 6, not here** — Phase 4 leaves coordinates in their absolute aspect-column / layer space; Phase 6 shifts the entire view to `(40, 40)` origin once all coordinates are computed.

### Step 5b — Multi-row sibling layout (preserved from pre-0.8.0)

The Step 5b multi-row sibling layout from the pre-0.8.0 procedure is preserved in 0.8.0 as part of Phase 4's collision handling. Its rules apply unchanged when a new nested child must be placed in a parent that already contains a row of architect-positioned siblings — see the original procedure for the full algorithm (preserve `x`, fall back to bendpoint routing, grow `parent.w`).

### Step 5 — Nest children into parents (preserved from pre-0.8.0)

Phase 4's collision logic above runs before nesting. After collision-free placement, apply the nesting rule from the pre-0.8.0 procedure unchanged: for every Composition / Aggregation / Realization relationship `(parent, child)` where both endpoints land in the same layer AND aspect column, place `child` as a nested `<node>` inside `parent`'s placement (`x = parent.x + 20`, stacked vertically inside, `w ≤ parent.w − 40`); mark the relationship edge as ARM-hidden (`<property propertyDefinitionRef="propid-archi-arm">` value `hide`); grow parent dimensions to contain children. Nesting depth capped at 2.
