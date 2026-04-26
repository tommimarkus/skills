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

### Step 5 — Nest children into parents

For every Composition, Aggregation, or Realization relationship `(parent, child)` where **both endpoints land in the same layer AND aspect column** (per Phase 2 layer assignment + Phase 3 aspect bias):

- Place `child` as a nested `<node>` inside `parent`'s placement. Child `x = parent.x + 20`, `y = parent.y + 40 + Σ prior_children.h + 20 × prior_count`. Child `w ≤ parent.w − 40`, `h` unchanged.
- Mark the relationship edge as implicit: add `<properties>` with `<property propertyDefinitionRef="propid-archi-arm"><value xml:lang="en">hide</value></property>` to the relationship, and **do not** emit a `<connection>` for it in this view. Archi's ARM will render the nesting as-is; tools without ARM still read the relationship in the model.
- Grow the parent's `w`/`h` if needed to contain children: `parent.w = max(parent.w, max_child.x + max_child.w + 20 − parent.x)`, `parent.h = max(parent.h, last_child.y + last_child.h + 20 − parent.y)`.

Rules:

- Only nest when both endpoints share the same layer AND aspect column — cross-layer or cross-aspect nesting violates reference §2.1 / §2.3.
- A child may be nested in at most one parent per view. If a child has two valid parents, nest in the one whose relationship is Composition; fall back to the first parent in identifier order.
- Nesting depth is capped at 2 (parent → child → grandchild). Deeper chains render correctly but exceed the view budget quickly — flag as `AD-L4` risk.

### Step 5b — Multi-row sibling layout (new child, existing siblings)

Common Extract scenario: a refresh adds a new child to a parent that already contains a horizontal row of architect-positioned siblings (matched by Tier 0 Step 1). The default Phase 4 placement (centred on `parent.x`, stacked vertically below the last existing child) would put the new child on a second row beneath the first row of siblings. The parent→child Composition edge then routes (per Phase 5 orthogonal) along the shortest path, which visually passes through one or more existing sibling boxes — making the relationship look anchored on a sibling instead of on the parent.

Apply this rule before falling through to Phase 4's default centred placement for a *new* nested child whose row would land below at least one existing sibling row in the same parent:

1. **Prefer a non-colliding `x`.** Compute the candidate placement window inside the parent: `x ∈ [parent.x + 20, parent.x + parent.w − 20 − child.w]`. Scan the existing siblings on the row(s) above the new child's row and collect the union of their x-extents `[sibling.x, sibling.x + sibling.w]`. If the candidate window contains any `x` that does not overlap any sibling x-extent, place the new child at the smallest such `x` (deterministic). The Composition edge then drops vertically inside the parent's whitespace and never crosses an existing sibling box; emit it as a normal hidden ARM-managed edge per Step 5.
2. **Fall back to bendpoint routing.** If no non-colliding `x` fits within the parent's interior — every horizontal pixel inside `parent.w` overlaps an existing sibling — keep the default centred placement and emit two bendpoints in Phase 5 to route the parent→child Composition edge west of the parent (see Phase 5 *Multi-row sibling clause*, added in Task 2.6). The edge is visible (not ARM-hidden); the AD-L7 nest-and-hide rule does not apply when an explicit bend is needed to clear a sibling.
3. **Grow `parent.w` if necessary.** If the candidate window is empty because the parent is narrower than its sibling row, grow `parent.w` per Step 5's existing rule before re-evaluating clause 1.

The rule only fires when (a) the new child is genuinely new (not preserved by Tier 0 Step 1) and (b) the parent already contains at least one existing sibling on a row above the new child's row. Single-row insertions (the new child fits on the existing row at the next free slot) are unchanged from Step 5.

### Phase 5 — Edge routing (Manhattan A* with obstacle avoidance)

For every `<connection>` not hidden by Tier 0 nesting (existing ARM rule), compute an orthogonal path that **avoids** the bounding boxes of all non-source / non-target nodes.

**Algorithm:**

1. **Source attach point** = side-midpoint of source `<node>` facing the target. Decision rule: pick the side closest to target's centre, breaking ties by preference order: right > down > left > up.
2. **Target attach point** = side-midpoint of target `<node>` facing the source. Same decision rule (mirror).
3. **Path: BFS over a 10-px grid.** Each grid cell is `(x // 10, y // 10)`. Start cell = source attach point grid-aligned. Goal cell = target attach point grid-aligned.
4. **Obstacle map.** For every `<node>` other than source, target, **and any ancestral container of source or target** (parent → grandparent → ... in the Step 5 nesting hierarchy), mark all grid cells inside `(x, y, x + w, y + h)` AND a 10-px halo around it as forbidden. Ancestor exclusion lets the BFS path leave a nested element through its container's boundary; without it, a nested source / target would be trapped.
5. **Cost function:** `cost = grid_step_count + bend_count × 5`. Each move along the same direction adds 1; each 90° turn adds the bend penalty (5 grid steps default).
6. **Bend points:** every grid cell where the path direction changes becomes a `<bendpoint x="..." y="..."/>` child of `<connection>`. Convert grid-cell back to pixel by `x = cell_x × 10`.
7. **Parallel edges in the same lane** (same source midpoint, same target midpoint) space 20 px apart in the perpendicular direction.

**Multi-row sibling clause** (referenced by Step 5b clause 2). When Step 5b falls back to bendpoint routing for a new nested child placed below existing siblings, Phase 5 emits **two bendpoints** to route the parent→child Composition edge west of the parent's left edge: bendpoint 1 at `(parent.x − 20, parent.y + parent.h / 2)` (round to grid) and bendpoint 2 at `(parent.x − 20, child.y + child.h / 2)` (round to grid). The edge attaches to the parent's left midpoint and the child's left midpoint.

**Specialisation hook for §9.4 Technology Usage:** hosting Assignment edges (`Assignment` relationships from Application Component to Technology Node) skip the A* and draw straight-vertical from source bottom-midpoint to target top-midpoint. Tier 2 §9.4 specialisation enables this carve-out.

**Feedback edges** (marked by Phase 1) route last so other edges' lanes are placed first. No semantic difference; just a layering trick to reduce crossings on common paths.

**Worked example.** Application Cooperation view (reference §9.2) with three Application Components and one Application Service:

- `C1` = Orders API (ApplicationComponent, out-degree 2)
- `C2` = Payments API (ApplicationComponent, out-degree 1)
- `C3` = Orders Core (ApplicationComponent, in-degree 2; Composition parent of C1 and C2)
- `S1` = Place Order (ApplicationService; realised by C1)

Phase 2: all elements → Application layer.

Phase 3: topological order (C3 → C1 → C2 → S1). Aspect grouping: C1, C2, C3 → Active structure column; S1 → Behaviour column.

Phase 4 placements (single Application layer, `y_layer_top = 40` after Phase 6 normalisation; pre-normalisation values shown):

- C3 at `(320, 540, 200, 200)` (grown to contain children).
- C1 at `(340, 580, 160, 64)` (nested inside C3).
- C2 at `(340, 664, 160, 64)` (nested inside C3, below C1, sibling gutter 40 px applies between non-nested but C1/C2 are nested — use the inner stacking rule of `+ element.h + 20` for nested children).
- S1 at `(600, 540, 180, 64)`.

Phase 5: only edge to route is `C1 → S1` (Realization). Composition edges C3 → C1, C3 → C2 are ARM-hidden by Step 5 nesting.

Source: C1 right midpoint = `(500, 612)`. Target: S1 left midpoint = `(600, 572)`. BFS path: right from `(500, 612)` to `(600, 612)` (10 grid steps), up to `(600, 572)` (4 grid steps). One bend at `(600, 612)`. Total cost = 14 + 5 = 19.

Phase 6: `(min_x, min_y) = (320, 540)`. Shift by `(40 - 320, 40 - 540) = (-280, -500)`. After shift:
- C3 at `(40, 40, 200, 200)`. C1 at `(60, 80, 160, 64)`. C2 at `(60, 164, 160, 64)`. S1 at `(320, 40, 180, 64)`. Bend at `(320, 112)`.

Result: one view, four elements, one visible connection, zero crossings, origin-aligned canvas.

### Phase 6 — Bounding-box normalisation

After Phases 1–5 complete, compute the used-region bounding box and shift the entire view to canvas origin.

1. **Compute bounds.** Iterate every `<node>`'s `(x, y, x + w, y + h)` and every `<bendpoint>`'s `(x, y)`. Record `min_x`, `min_y`, `max_x`, `max_y`.
2. **Compute shift.** `dx = 40 - min_x`, `dy = 40 - min_y`. (`40` is the canvas inset — leaves a 4-cell margin on the top and left edges of the diagram.)
3. **Apply shift.** For every `<node>`: `x += dx`, `y += dy`. For every `<bendpoint>`: `x += dx`, `y += dy`.
4. **Round to grid.** All resulting `x`, `y` should already be on the 10-px grid (Phases 4 and 5 placed everything on grid, and `dx`/`dy` are differences of grid-aligned values), but defensive rounding (`x = round_to_10(x)`) catches any accumulated drift.

After Phase 6, the diagram's used region's top-left is at `(40, 40)`; total view width is `max_x - min_x + 80` (40 px margin on each side). Archi opens the file with the diagram visible immediately — no scroll-to-find.

**Skip Phase 6 only when:** the prior view at the canonical path was authored with `propid-archi-model-banded=v1` and Tier 0 preserved its coordinates verbatim (Phase 6 would shift the architect's hand-positions away from where they expected them).

## Tier 2 — Per-viewpoint specialisations

Each specialisation overrides Tier 1 phases for its diagram kind. The override is bounded — phases 1, 2, 5, 6 always run unless the specialisation explicitly carves them out.

Dispatch by the view's `viewpoint=` attribute:

| `viewpoint=` | Specialisation | Replaces Tier 1 phases |
|---|---|---|
| `Capability Map` | §9.1 tile grid | 3, 4 |
| `Application Cooperation` | §9.2 hub-and-spoke (when hub detected) | 3, 4 |
| `Service Realization` | §9.3 vertical-stack | 3, 4 |
| `Technology` | §9.4 hosting tower | 3, 4; carves phase 5 for hosting Assignment |
| `Migration` | §9.5 Plateau timeline | 2, 3, 4 |
| `Motivation` | §9.6 hierarchical tree | 3, 4 |
| `Business Process Cooperation` | §9.7 process-flow lanes | 3, 4 |

Each sub-section below documents one specialisation.

### §9.4 Technology Usage — hosting tower

**Override:** phases 3, 4. **Carves:** phase 5 for `Assignment` relationships.

**Visual idiom:** Application Components stack directly above their hosting Technology Nodes; hosting Assignment edges drawn straight-vertical (the structural axis of the diagram); Communication Network / Path elements drawn as horizontal bars between Technology Nodes.

**Phase 3 (override).** Order Application elements by their hosting Node's identifier (so Apps that share a Node cluster). Order Technology elements by `degree(out)` descending (Nodes that host many Apps centred).

**Phase 4 (override).**
1. Place Technology Nodes first in a horizontal row at `y_tech = 40 + total_app_height + 60` (pre-normalisation; Phase 6 normalises `(min_x, min_y)` back to `(40, 40)`). Tech Nodes spaced horizontally with 40 px gutter, ordered per Phase 3 step 2 (highest out-degree centred). Width per Tech Node = default 160 (or grown for label).
2. Each Application Component placed at `(host_node.x + (host_node.w - app.w) / 2, y_tech - app.h - 60)`. The Application is centred horizontally above its host, with a 60 px vertical gap between Application bottom and Technology top. If multiple Apps share a Node, group horizontally above with 40 px sibling gutter.
3. Communication Network / Path elements placed as horizontal bars between Tech-row Nodes at `y = y_tech + node.h / 2 - bar.h / 2`, spanning the gap between their two endpoints.
4. Tech Nodes that no Application hosts (data-plane: Cosmos, Storage, Key Vault) and observability Nodes (Application Insights, Log Analytics) place to the right of the hosting tower in their own column, vertically stacked with 40 px sibling gutter.

**Phase 5 carve-out.** Assignment relationships from Application Component to Technology Node (`Assignment` xsi:type, source = Application Component, target = Technology Node) skip the A* router. Draw straight-vertical: source bottom-midpoint to target top-midpoint. No bend points.

All other relationships (Realization, Used-by, Serving) route via Phase 5's standard A*.

Acceptance: §9.4 view from `/tmp/lfm/docs/architecture/lfm.oef.xml` rebuilds with apps directly above their hosts and vertical hosting edges; data-plane / observability cluster to the right of the hosting tower.
