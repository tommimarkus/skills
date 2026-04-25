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
