# Fallback deterministic layered layout

Deterministic fallback for architecture-design when no viewpoint-specific
backend is available. This preserves the useful conventions from the earlier
layered-layout procedure while making clear that the fallback is a heuristic, not a
full modern graph-layout engine.

This fallback is acceptable for small generated directed views. Prefer a mature
layered/orthogonal backend when one is available for complex generated views,
and prefer route-only repair for architect-edited views.

## Scope

Use this fallback when:

- the view is new or mixed generated geometry;
- no supported backend is available;
- the viewpoint policy does not require a specialised tile/timeline/hosting/
  lane/tree layout; and
- the view is small enough for the `AD-L4` budget.

Do not use it as the primary layout for Capability Map, Migration, Technology
Usage, Business Process Cooperation, or Motivation when their viewpoint
policies apply.

## Determinism

Given the same element set, relationship set, viewpoint policy, and prior
geometry, the fallback produces the same `x`, `y`, `w`, `h`, ports, and
bendpoints. Tiebreaks use identifier ascending.

Grid size, label-width estimates, view budgets, and crossing thresholds are
local engineering conventions. The fallback uses research-inspired layered
layout heuristics, not an optimality guarantee.

## Step 0 - Preserve architect positions

If a prior view exists at the canonical path and contains a `<node>` for this
element, matched by `elementRef`, reuse its `x`, `y`, `w`, and `h` verbatim.
Record preserved placements so later route repair and validation distinguish
authored geometry from generated geometry.

Connection bendpoints are not preserved by node identity alone. Reuse prior
bendpoints only when the prior and current `<connection>` have the same
`relationshipRef`, source node, target node, and the route passes the `AD-L11`
post-layout intersection check. If a relationship was replaced, its
source/target was inverted, or an Extract refresh changed the relationship
kind, discard the old bendpoints and reroute.

Do not read or write a model-root layout marker. Model-root `<properties>` is
invalid OEF and triggers `AD-17`.

## Step 1 - Cycle handling

For each ArchiMate layer, build a directed graph from same-layer relationships
that influence ordering: `Realization`, `Composition`, and `Serving`.

Run DFS feedback-edge marking:

1. Mark each vertex `unvisited`, `visiting`, or `done`.
2. A back edge from a `visiting` vertex to another `visiting` vertex is a
   feedback edge.
3. Mark the edge `is-feedback=true` for route-ordering only.
4. Do not reverse the edge; ArchiMate relationship direction carries semantics.

This is DFS feedback-edge marking, not full strongly-connected-component
detection. If a future implementation needs SCC handling, describe and test
that algorithm explicitly.

## Step 2 - Layer and aspect assignment

Assign each element to an ArchiMate layer from its `xsi:type`:

| Element types | Layer |
|---|---|
| `Resource`, `Capability`, `ValueStream`, `CourseOfAction` | Strategy |
| `BusinessActor`, `BusinessRole`, `BusinessProcess`, `BusinessService`, `BusinessObject`, `Contract`, `Product` | Business |
| `ApplicationComponent`, `ApplicationCollaboration`, `ApplicationService`, `ApplicationFunction`, `ApplicationInterface`, `DataObject` | Application |
| `Node`, `Device`, `SystemSoftware`, `TechnologyService`, `CommunicationNetwork`, `Path`, `Artifact` | Technology |
| `Equipment`, `Facility`, `DistributionNetwork`, `Material` | Physical |

Motivation and Implementation & Migration columns span the core layer rows.
When no target gives a better row, default to Application row.

Composite types such as `Location` and `Grouping` inherit the dominant child
layer. A Grouping containing only Application Components gets the Application
row.

## Step 3 - Within-layer ordering

For each layer in top-to-bottom order:

1. Topologically sort the same-layer graph after feedback-edge marking.
2. Break ties by aspect column: Motivation, Active structure, Behaviour,
   Passive structure, Implementation & Migration.
3. Break remaining ties by identifier ascending.

Then run 4 passes of barycentric crossing-minimisation between adjacent
populated layers: top-down, bottom-up, top-down, bottom-up. Barycentric ordering
is a heuristic that usually reduces crossings; it does not guarantee a global
minimum.

Skip degenerate layers with fewer than two elements.

## Step 4 - Coordinate assignment

Operate layer-by-layer from Strategy to Physical:

1. Compute the layer's top y-coordinate from the previous occupied layer plus a
   60-px gutter.
2. For each element in the locked ordering:
   - if it has cross-layer incoming edges from already placed upper layers, use
     the median source x-coordinate;
   - otherwise use the centre of the aspect column;
   - round to the nearest 10 px; and
   - bump right by width plus 40 px until same-depth collisions clear.
3. Stack siblings in the same aspect column with 40-px gutters.

Default sizes:

| Element class | `w` | `h` |
|---|---:|---:|
| Structure | 160 | 64 |
| Behaviour | 180 | 64 |
| Motivation | 180 | 64 |
| Strategy | 180 | 64 |
| Passive | 140 | 64 |
| Implementation & Migration | 180 | 64 |
| Grouping | computed; min 240 | computed; min 140 |
| Junction | 14 | 14 |

When a `<name>` is long enough that the default width would truncate, enlarge
`w` in 20-px steps using the local convention of 7 px per character at the
default Archi font.

## Step 5 - Nest children into parents

Represent containment by nesting only when the viewpoint policy and model
relationship support it.

Default hide-by-nesting applies to:

- `Composition`; and
- `Aggregation`, when part-whole semantics are clear.

`Assignment` nesting is allowed only when the viewpoint policy says it is the
visual grammar, such as a Technology Usage hosting stack.

Do not hide the main `Realization` spine by default. A Service Realization view
must keep the auditable Realization chain visible unless a specific
viewpoint-policy exception documents that the relationship is non-spine
redundancy.

When nesting is allowed:

1. Place child nodes inside the parent with 20-px inner padding.
2. Grow the parent to contain children.
3. Hide the represented relationship in this view only when the curation reason
   is documented.
4. Cap nesting depth at 2; deeper chains trigger `AD-L4` risk.

If a new nested child would route through existing same-parent siblings, prefer
a non-colliding child x-position. If none fits, keep the node placement and
route the parent-child edge west of the parent with explicit bendpoints rather
than hiding a misleading route.

## Step 6 - Route edges

Use [routing-and-glossing.md](routing-and-glossing.md).

Fallback routing uses a deterministic orthogonal grid or visibility graph. If
bend penalties are part of the cost, the search state includes incoming
direction and uses Dijkstra/A* priority selection over accumulated cost. Plain
BFS is allowed only for uniform movement cost with no bend optimization.

## Step 7 - Normalize generated or mixed views

After placement and routing, compute the used-region bounding box over nodes and
bendpoints. Shift generated and mixed views so the used region starts at
`(40, 40)` and keep coordinates grid-aligned.

Skip normalization only when every placement and route in the view came from
architect-authored preservation and shifting would churn authored coordinates.

## Step 8 - Validate

Run the same validation handoff as backend output:

- materialized node and relationship geometry;
- `AD-L2`, `AD-L3`, `AD-L8`, `AD-L10`, `AD-L11`, `AD-L13`, and `AD-L15`
  source-geometry gate when a local file exists;
- `AD-L20` when Service Realization hides visible Realization spine edges;
- professional-readiness classification per
  [professional-readiness.md](professional-readiness.md); and
- final OEF importability checks available in the architect's toolchain.
