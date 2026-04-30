# Routing and glossing

Connector routing policy for architecture-design OEF views. This procedure is
independent of the layout backend. It applies to generated geometry, future
backend results, and route-only repair of architect-edited diagrams.

## Default routing stance

Use orthogonal routing by default. A route may intersect only:

- its source node;
- its target node; and
- required source/target ancestor containers needed to leave nested structure.

Crossing any unrelated node body, or placing the first/last bendpoint inside
the endpoint node body, is a blocking `AD-L11` failure.

## Port assignment

Before routing:

1. Generate candidate ports for each node side.
2. Score ports by viewpoint, relationship type, semantic direction, edge
   priority, congestion, and prior-lane preservation.
3. Reserve ports for high-priority edges first.
4. Route high-priority edges before secondary edges.
5. Separate parallel edges by stable lane offsets.

Candidate ports start with `north`, `south`, `east`, and `west`. High-density
views may split each side into deterministic indexed ports such as `east-1`,
`east-2`, and `south-1`.

## Relationship-family preferences

| Relationship family | Preferred routing |
|---|---|
| Realization | Along the realization spine direction; keep the main spine visible |
| Serving | Provider side to consumer side, preserving service direction |
| Assignment / hosting | Vertical where Technology Usage hosting-stack policy applies |
| Flow / Triggering | Process direction in Business Process Cooperation |
| Access | Behaviour/active element to the passive object side, usually short vertical in process lanes |
| Composition / Aggregation | May be hidden when represented by valid nesting and not needed as a visible story path |
| Association | Low-priority context edge; route after main story edges |

Do not use a side-midpoint-only rule when multiple high-priority edges need the
same side. Use ports and lane offsets.

## Preferred router

Use an object-avoiding orthogonal connector router when available.

Acceptable backend behavior:

- fixed-node orthogonal routing;
- explicit source and target ports;
- obstacle avoidance;
- connector spacing;
- parallel-edge separation;
- incremental rerouting; and
- route simplification.

## Fallback router

If no backend is available, use deterministic direction-aware Dijkstra/A* over
a sparse orthogonal visibility graph or grid.

Search state must include `(x, y, incomingDirection)` so bend penalties are
applied to direction changes. Step cost may include movement cost, turn cost,
port cost, obstacle clearance cost, and lane reuse penalty.

Plain BFS may be used only when all movement costs are uniform and bends are not
being optimized. Do not call BFS with bend penalties "A*".

## Route-only repair

For existing architect-edited views:

1. Preserve locked node coordinates.
2. Validate existing bendpoints against current relationship endpoints and
   `AD-L11`.
3. Preserve passing authored bendpoints.
4. Rip up only stale, generated, or invalid routes.
5. Reroute failed connections through available ports and lanes.
6. Move generated/unlocked nodes only when no clean route exists within the view
   budget.
7. Escalate to user-visible finding rather than moving locked geometry without
   an explicit global reflow request.

## Rip-up and reroute

When routes conflict:

- reroute low-priority/generated edges before high-priority edges;
- preserve the main realization/process/hosting spine;
- keep route changes local to the affected view;
- avoid pushing locked nodes;
- allow push-and-shove only for generated, unlocked geometry; and
- fail with a precise `AD-L*` finding if the route cannot be repaired safely.

## Glossing

After routing:

1. Remove redundant collinear bendpoints.
2. Remove tiny zigzags.
3. Prefer monotonic paths if they do not violate obstacles.
4. Align parallel connector lanes.
5. Separate overlapping or coincident lanes.
6. Preserve explicit architect-authored bendpoints unless they fail `AD-L`
   checks.
7. Re-run post-route validation.

## PCB/EDA-inspired concepts

Borrowed from PCB/EDA routing, adapted for diagrams:

- design-rule-check-like visual validation;
- route priority;
- rip-up/reroute of low-priority/generated routes;
- push-and-shove only for generated, unlocked geometry; and
- glossing.

Do not use PCB autorouting directly. ArchiMate connector routing is a semantic
readability problem, not an electrical manufacturability problem.

## Validation handoff

After route assignment and glossing, run the source-geometry gate and
professional-readiness pass. Backend route metrics are useful diagnostics, but
only final OEF source geometry decides `diagram-readable` or `review-ready`.
