# Layout backend contract

Backend-neutral contract for architecture-design view geometry. This file
defines what a geometry backend or fallback procedure consumes and returns. The
packaged Java™ runtime validates this contract through Draft 2020-12 schemas at
`references/schemas/layout-request.schema.json` and
`references/schemas/layout-result.schema.json`.

The skill builds this request after it has selected ArchiMate® elements,
relationships, viewpoint, and curation policy. A backend may place nodes and
route edges, but it cannot change architecture semantics.

## Request fields

`layoutRequest` contains the fields encoded by
`layout-request.schema.json`:

- `schemaVersion`: contract version.
- `requestId`: stable run/request identifier for traceability.
- `archimateTarget`: notation version emitted by the skill, currently `3.2`.
- `mode`: `generated-layout`, `route-repair`, or `global-polish`.
- `view`: exact OEF view identity, `viewpoint=`, direction, and quality target.
- `preserveExistingGeometry`: whether prior architect geometry is authoritative.
- `nodes`: visible view-node candidates.
- `edges`: visible connection candidates.
- `containers`: parent/child hierarchy and grouping constraints.
- `locks`: authored or externally fixed geometry.
- `priorGeometry`: prior coordinates and bendpoints when available.
- `semanticBands`: viewpoint/layer/aspect bands the backend should respect.
- `constraints`: routing, obstacle, lane, and reflow limits.
- `constraints`: routing, obstacle, lane, and reflow limits.

Validate a request before backend execution:

```bash
references/scripts/arch-layout.sh validate-request --request <layout-request.json>
```

Generated-layout execution for eligible viewpoints:

```bash
references/scripts/arch-layout.sh layout-elk --request <layout-request.json> --result <layout-result.json>
```

`layout-elk` is the generated-layout command. `validate-request` and
`validate-result` are schema/contract gates. `validate-png` is a rendered-image
invariant gate and does not generate or repair OEF geometry.

## Node fields

Each node record includes:

- `id`: view-node identifier to emit in OEF.
- `elementRef`: model element identifier.
- `type`: ArchiMate element type.
- `semanticLayer`: Strategy, Business, Application, Technology, Physical,
  Motivation, or Implementation & Migration.
- `semanticAspect`: active structure, behaviour, passive structure, motivation,
  implementation/migration, or viewpoint-specific role.
- `size`: requested width and height.
- `label`: display label used for width heuristics.
- `generated`: whether the skill generated this placement in the current run.
- `locked`: whether the node placement is architect-authored or otherwise fixed.
- `prior`: prior `x`, `y`, `w`, and `h` when preservation applies.
- `parent`: containing view-node id when nested or grouped.
- `ports`: optional explicit candidate ports.

## Edge fields

Each edge record includes:

- `id`: view-connection identifier to emit in OEF.
- `relationshipRef`: model relationship identifier.
- `type`: ArchiMate relationship type.
- `source`: source view-node identifier.
- `target`: target view-node identifier.
- `priority`: route priority, where the main viewpoint story gets the highest
  value.
- `visible`: whether this relationship should become a visible OEF connection.
- `generated`: whether the route is generated in the current run.
- `locked`: whether existing bendpoints are architect-authored and must be
  preserved unless they fail validation.
- `preferredSourcePorts` / `preferredTargetPorts`: ordered port candidates.
- `priorBendpoints`: prior bendpoints when route preservation applies.
- `curationReason`: reason for omission or hiding when `visible=false`.

## Containers and hierarchy

Containers describe visual containment separately from model relationships:

- `parent`: view-node id.
- `children`: contained view-node ids.
- `relationshipRef`: model relationship that justifies containment, when any.
- `relationshipType`: Composition, Aggregation, Assignment, or another
  viewpoint-specific containment relationship.
- `maxDepth`: maximum supported depth for the current view.
- `mayHideEdge`: whether the relationship may be represented by nesting instead
  of a visible connection.

Containment does not grant permission to hide the main Realization spine.

## Ports

Ports are named candidate points on node sides. A backend may produce exact
coordinates, but it should preserve the semantic side when possible:

- `north`, `south`, `east`, `west`;
- indexed side ports such as `east-1`, `east-2`, `south-1`; and
- generated coordinates `{ side, offset, x, y }` for high-density routing.

Port scoring uses viewpoint, relationship type, semantic direction, edge
priority, congestion, and prior lane preservation.

## Locks and prior coordinates

Locks protect architect-authored geometry:

- `locked=true` nodes are not moved unless the user explicitly requested global
  reflow or the existing placement violates a blocking rule.
- locked bendpoints are preserved only when relationship id, source, target,
  and `AD-L11` route validation still pass.
- generated nodes may move during local reflow.
- generated routes may be ripped up and rerouted before locked nodes are moved.

## Semantic bands

Semantic bands are hints, not absolute pixels:

- ArchiMate layer order for generic directed views;
- aspect columns for layer/aspect grid fallback;
- capability tile rows;
- migration plateau/timeline columns;
- technology hosting stacks;
- process lanes and handoff bands; and
- motivation traceability depths.

Backend coordinates can vary, but final OEF must satisfy the viewpoint policy
and `AD-L*` checks.

## Backend result fields

`layoutResult` returns the fields encoded by
`layout-result.schema.json`:

- `backend`: backend name, version, mode, and deterministic flag.
- `nodeGeometry`: node id plus `x`, `y`, `w`, and `h`.
- `edges`: connection id plus `sourcePort`, `targetPort`, `bendpoints`, and
  route status.
- `hiddenEdges`: relationship ids omitted or hidden from the view and the
  policy reason.
- `metrics`: node overlaps, connector-node intersections, crossing count,
  route count, max bends, average bends, moved locked nodes, and displaced
  generated nodes.
- `warnings`: backend limits, degraded fallback decisions, or constraints the
  backend could not satisfy.

Validate a result before OEF materialization:

```bash
references/scripts/arch-layout.sh validate-result --result <layout-result.json>
```

Materialize a validated result into a specific OEF view:

```bash
references/scripts/arch-layout.sh materialize-oef \
  --oef <source.oef.xml> \
  --view <view-id> \
  --result <layout-result.json> \
  --out <materialized.oef.xml> \
  --snap-grid 10 \
  --run-source-gate
```

`materialize-oef` applies matching `nodeGeometry` records to OEF `<node>`
`x` / `y` / `w` / `h` attributes and matching `edges` records to OEF
`<connection>` bendpoints. It preserves model elements, model relationships,
view-node ids, connection ids, XML nesting, `elementRef`, `relationshipRef`,
`source`, and `target` attributes. Result coordinates are treated as absolute
OEF coordinates; nested nodes stay nested, but their coordinates are not made
parent-relative. Use `--fail-on-warning` when warning-state results must not be
materialized, `--preserve-locked-nodes` when locked result nodes should leave
existing OEF geometry unchanged, and `--run-source-gate` to fail if
`validate-oef-layout.sh` rejects the materialized file.

## Validation handoff

Backend output is always validated by the skill before OEF serialization:

- no invented or removed ArchiMate model elements;
- no changed relationship type or direction;
- all visible nodes materialized with geometry;
- all visible relationships materialized as OEF connections;
- hidden relationships allowed only by semantic policy;
- locked geometry preserved unless explicitly reflowed or invalid;
- `AD-L*` source-geometry checks pass for the requested readiness level; and
- professional readiness is derived from final OEF quality.

## Determinism requirements

Given the same request, backend, fallback options, and prior geometry, the
result should be stable:

- deterministic tiebreaks use identifiers ascending;
- generated ids are supplied by the skill, not the backend;
- stochastic layout modes are disabled or seeded;
- optional backends disclose version/configuration in the run summary when they
  influence output; and
- fallback output must be byte-stable for the same input.

## Compact example

```yaml
layoutRequest:
  archimateTarget: "3.2"
  viewpoint: "Service Realization"
  direction: "top-down"
  preserveExistingGeometry: true

  nodes:
    - id: "view-node-app-component-payments"
      elementRef: "app-component-payments"
      type: "ApplicationComponent"
      semanticLayer: "Application"
      semanticAspect: "ActiveStructure"
      size: { width: 160, height: 64 }
      locked: false
      generated: true

  edges:
    - id: "view-connection-realizes-payments"
      relationshipRef: "rel-realizes-payments"
      type: "Realization"
      source: "view-node-app-component-payments"
      target: "view-node-app-service-payments"
      priority: 100
      visible: true

  constraints:
    avoidNodeBodies: true
    orthogonalRouting: true
    preserveLockedNodes: true
    routeOnlyRepair: false
    separateParallelEdges: true
    keepRealizationSpineVisible: true
```

```yaml
layoutResult:
  nodes:
    - id: "view-node-app-component-payments"
      x: 420
      y: 220
      width: 160
      height: 64

  edges:
    - id: "view-connection-realizes-payments"
      sourcePort: "south"
      targetPort: "north"
      bendpoints:
        - { x: 500, y: 320 }
        - { x: 500, y: 360 }

  metrics:
    nodeOverlaps: 0
    connectorNodeIntersections: 0
    crossings: 2
    maxBends: 3
```

## Optional future backends

Potential future backends include ELK/elkjs for layered/port-aware layout,
libavoid-style routers for object-avoiding connector repair, Graphviz `dot` for
simple directed fallback, and maxGraph for interactive-editor integration. They
are optional implementation candidates, not required dependencies.
