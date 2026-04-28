# Layout quality cases

Regression cases for Review-mode `AD-L*` geometry checks. These are small source-shape descriptions rather than full OEF documents so they can be reused with Build, Extract, or hand-authored fixture files.

## AD-L11 connector through unrelated node

- View: Technology Usage.
- Nodes: source Function App at `(40, 40, 160, 64)`, unrelated Runtime child at `(240, 40, 160, 64)`, target Application Insights at `(440, 40, 160, 64)`.
- Connection: source → target with a straight segment from source right midpoint to target left midpoint.
- Expected: `AD-L11 block`; readiness max `model-valid`.

Executable regressions: `render-quality-gate/cropped-but-failing.oef.xml` is a
well-formed OEF whose PNG can be cropped to plausible bounds while the source
still fails `AD-L10` and `AD-L11`; `render-quality-gate/bendpoint-origin-drift.oef.xml`
proves `AD-L10` computes the used-region origin from nodes and bendpoints
together; `render-quality-gate/stacked-connector-lane.oef.xml` proves
`AD-L13`; `render-quality-gate/fanout-crisscross.oef.xml` proves `AD-L15`;
and `render-quality-gate/endpoint-bendpoint-inside.oef.xml` proves the
endpoint-bendpoint `AD-L11` subcase.
Run `render-quality-gate/test-render-quality-gate.sh`; it must emit the
expected view id, connection id, node id, endpoint-lane, crossing, and actual
min x/y evidence.

## Materialized view geometry

- View: any fixture intended for render validation.
- Nodes: at least one non-legend `<node xsi:type="Element">` with `elementRef`, `x`, `y`, `w`, and `h`.
- Connections: each relationship that is part of the fixture's visual story has a `<connection xsi:type="Relationship">`; long or non-aligned routes use bendpoints instead of diagonal shortcuts.
- Expected: Archi renders a nonblank PNG larger than the 100 x 100 empty-view placeholder; missing view geometry is a fixture defect, not an acceptable generated test diagram.

## Supported viewpoint coverage

- View: committed `*.oef.xml` fixture set.
- Viewpoints: Capability Map, Application Cooperation, Service Realization, Technology Usage, Migration, Motivation, and Business Process Cooperation.
- Expected: the render gate fails when any supported §9 viewpoint is missing from the fixture corpus.

## Allowed ancestor-container exit

- View: Service Realization.
- Nodes: parent Function App container, nested source Function runtime, target Application Insights outside the parent.
- Connection: nested source exits through its own parent boundary without crossing sibling nodes.
- Expected: no `AD-L11`; parent intersection is allowed only because it is an ancestor of the source.

## Business Process Cooperation long route

- View: Business Process Cooperation.
- Nodes: Active lane Actor, Behaviour lane five-step Triggering chain, Passive lane Business Object.
- Connection: Actor Assignment to final process must route around intermediate Behaviour nodes.
- Expected: no `AD-L11`; if the line crosses an intermediate process, `AD-L11 block`.

## Migration / Deployment Topology long route

- View: Migration.
- Nodes: sibling Development, Staging, Production Plateaus and one deploy Work Package below.
- Connections: Work Package Realization to each Plateau.
- Expected: no Plateau-to-Plateau Triggering (`AD-20` if present); Realization lanes do not cross sibling Plateaus (`AD-L11` if they do).

## Technology Security-style route

- View: Technology Usage.
- Nodes: Function App, Managed Identity Technology Service, Cosmos account, Storage account, Key Vault, Log Analytics.
- Connections: Managed Identity Access edges and diagnostic Flow edges.
- Expected: Access/Flow edges use separate lanes; no stacked target arrowheads (`AD-L13`) and no connector crossing resource nodes (`AD-L11`).

## Stale bendpoint reuse after relationship replacement

- View: Technology Usage or Technology Security.
- Prior route: Function App -> Application Insights Flow, with bendpoints chosen for that source/target direction.
- Refresh: relationship is replaced with Application Insights -> Function App Serving, or MI Access edges are replaced by resource -> Function App Serving edges.
- Expected: old bendpoints are discarded unless the new route still clears every unrelated and nested child node rectangle. If the preserved route crosses Cosmos, Storage, Key Vault, managed identity, or runtime child boxes, report `AD-L11 block` and readiness max `model-valid`.

## Endpoint bendpoint inside endpoint box

- View: Business Process Cooperation or Service Realization.
- Nodes: Actor / Process / Application Service route with no unrelated-node crossing.
- Connection: the first bendpoint is inside the source box, or the last bendpoint is inside the target box.
- Expected: `AD-L11 block` with view id, connection id, endpoint node id, offending bendpoint coordinates, and endpoint bounding box; readiness max `model-valid`.

## AD-L12 through AD-L15 readability checks

- `AD-L12`: any non-legend node with zero same-view connections.
- `AD-L13`: three resource Nodes all entering the same target midpoint with overlapping arrowheads.
- `AD-L14`: occupied layer rows separated by more than 100 px of unused vertical space without documentation.
- `AD-L15`: three or more fan-out edges from one source crossing each other or a non-endpoint sibling.
