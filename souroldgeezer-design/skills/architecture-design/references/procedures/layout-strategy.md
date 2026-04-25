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
