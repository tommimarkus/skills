# architecture-design fixtures

Small ArchiMate® OEF XML files exercising all seven supported §9 viewpoints at representative scale (7-15 elements, 6-20 relationships). Fixtures are regression targets for the backend-neutral layout policy, deterministic fallback, routing/glossing rules, packaged layout runtime, rendered PNG validation, and source-geometry gate: each OEF fixture carries a materialized view with nodes, relationships, bendpoints, and spacing that should render as a professional-quality diagram. The rendered PNG output is the validation artefact when Archi is available.

## How fixtures are used

1. Build mode invokes the skill with the fixture's element / relationship set as architect intent.
2. The layout strategy finds no prior view at the canonical path, so all elements get generated placement.
3. The matching viewpoint policy plus backend or deterministic fallback computes coordinates, then routing/glossing assigns ports and bendpoints. JSON layout contract fixtures exercise the same request/result shape through `../scripts/arch-layout.sh`.
4. The skill writes the resulting OEF, including `<node>` and `<connection>` geometry in the `<view>`.
5. The bundled `../scripts/archi-render.sh` renders the OEF to PNG when Archi
   and an X display are available.
6. `../scripts/arch-layout.sh validate-png` checks that every produced PNG is nonblank, not tiny, not cropped, and within any configured baseline-drift tolerance; visual inspection then checks that the PNG is spacious, consistently routed, and at the per-viewpoint acceptance bar (see spec §6.2 of `docs/superpowers/specs/2026-04-25-architecture-design-pro-quality-design.md`).

## Render

```bash
cd /path/to/skills
souroldgeezer-design/skills/architecture-design/references/scripts/archi-render.sh \
  --cache-root /tmp/archi-fixture-cache \
  --output-root /tmp/archi-fixture-views \
  souroldgeezer-design/skills/architecture-design/references/fixtures/<fixture>.oef.xml
ls /tmp/archi-fixture-views/<fixture>/
```

## Validate every available diagram

Every committed `*.oef.xml` in this directory must pass the render gate before
the fixture set is considered valid:

```bash
./validate-render-fixtures.sh \
  --render-script ../scripts/archi-render.sh \
  --render-cache-root /tmp/archi-fixture-cache \
  --render-output-root /tmp/archi-fixture-views
```

The gate discovers all OEF fixtures in this directory, passes explicit cache and
output roots through to `archi-render.sh`, verifies materialized view geometry,
runs [`../scripts/validate-oef-layout.sh`](../scripts/validate-oef-layout.sh)
for source-geometry `AD-L*` findings, renders every diagram, and fails if any
PNG is Archi's blank 100 x 100 placeholder. It also fails when the fixture set
does not cover all seven supported viewpoint values: Capability Map,
Application Cooperation, Service Realization, Technology Usage, Migration,
Motivation, and Business Process Cooperation. If no cache or output root is
supplied, the validator creates a temporary root under `${TMPDIR:-/tmp}`.

## Static render-quality gate

Run the source-geometry gate directly when a renderer is unavailable or before
rendering a project model:

```bash
../scripts/validate-oef-layout.sh /path/to/docs/architecture/<feature>.oef.xml
```

It emits Review-style findings with the view id, smell code, and affected
connection or node id, then exits nonzero when any `AD-L*` finding is present.
The negative fixtures under `render-quality-gate/` are well-formed OEF files
that can render as cropped PNGs but must fail from the source geometry:
`cropped-but-failing.oef.xml` fails `AD-L10` and `AD-L11`;
`bendpoint-origin-drift.oef.xml` fails `AD-L10` with the actual min x/y coming
from bendpoints rather than node boxes; `stacked-connector-lane.oef.xml` fails
`AD-L13`; `fanout-crisscross.oef.xml` fails `AD-L15`; and
`endpoint-bendpoint-inside.oef.xml` fails the endpoint-bendpoint `AD-L11`
subcase; and `hidden-realization-negative.oef.xml` fails `AD-L20` when a
Service Realization view hides a Realization spine whose endpoints are visible.

## Layout runtime fixtures

The JSON fixture directories exercise the packaged Java™ 21 layout runtime
without requiring Archi:

```bash
../scripts/arch-layout.sh validate-request --request layout-contract/valid-service-realization.request.json
../scripts/arch-layout.sh layout-elk --request layout-elk-java/service-realization.request.json --result /tmp/service-realization.layout-result.json
../scripts/arch-layout.sh layout-elk --request layout-elk-realistic/application-cooperation-compound-trust-boundaries.request.json --result /tmp/application-cooperation.realistic.result.json
../scripts/arch-layout.sh route-repair --request route-repair/simple-obstacle.request.json --result /tmp/route-repair.layout-result.json
../scripts/arch-layout.sh global-polish --request global-polish/overlap-cluster.request.json --result /tmp/global-polish.layout-result.json
../scripts/arch-layout.sh materialize-oef --oef layout-elk-realistic/application-cooperation-compound-trust-boundaries.oef.xml --view id-view-realistic-application-cooperation --result /tmp/application-cooperation.realistic.result.json --out /tmp/application-cooperation.realistic.oef.xml --snap-grid 10 --run-source-gate
../scripts/arch-layout.sh materialize-oef --oef application-cooperation.oef.xml --view id-view-application-cooperation --result materialize-oef/layout-elk.result.json --out /tmp/application-cooperation.materialized.oef.xml --snap-grid 10 --run-source-gate
../scripts/arch-layout.sh validate-png --image rendered-png/valid-diagram.png --result /tmp/rendered-png-result.json
```

Runtime warning fixtures and tests assert machine-readable geometry evidence:
connector-node warnings name the edge, intersected node, route segment, node
bounds, and relationship; overlap warnings carry both node ids and rectangles;
containment warnings distinguish expected parent/child containment from
child-outside-parent defects and container-boundary connector crossings;
locked-node warnings carry requested and produced coordinates.

ImageMagick may be useful when manually creating or inspecting PNG fixtures,
but runtime acceptance uses Java™ ImageIO through `validate-png`.

## Fixtures

| Fixture | Viewpoint | Elements | Why |
|---|---|---|---|
| `capability-map.oef.xml` | §9.1 Capability Map | ~9 | Strategy tile grid with sub-Capability nesting and Business Function / Business Service realization |
| `application-cooperation.oef.xml` | §9.2 Application Cooperation | ~8 | Hub-and-spoke Application Cooperation view with Collaboration boundary, Service, Interface, and cooperating Components |
| `service-realization.oef.xml` | §9.3 Service Realization | ~7 | Process-rooted modality (user-driven): Business Actor → Process → App Service → UI App Component + Interface, with backend App Component on a Tech Node |
| `technology-usage.oef.xml` | §9.4 Technology Usage | ~11 | Hosting-tower view with Application Components above Nodes, Function runtime / artifact nesting, and data-plane dependencies |
| `migration.oef.xml` | §9.5 Migration | ~8 | True migration timeline with Baseline / Target Plateaus, Gap, cutover Event, Work Packages, and Deliverables |
| `motivation.oef.xml` | §9.6 Motivation | ~8 | Stakeholder → Driver → Goal → Outcome → Requirement → Constraint tree |
| `business-process-cooperation.oef.xml` | §9.7 Business Process Cooperation | ~8 | Lane-based process flow with Triggering chain |
| `validate-render-fixtures.sh` | Render gate | n/a | Discovers and validates every committed OEF fixture in this directory |
| `render-quality-gate/cropped-but-failing.oef.xml` | Negative render-quality fixture | n/a | Cropped-render case that fails source-geometry `AD-L10` / `AD-L11` |
| `render-quality-gate/bendpoint-origin-drift.oef.xml` | Negative render-quality fixture | n/a | Cropped-render case proving `AD-L10` bounds include bendpoints |
| `render-quality-gate/stacked-connector-lane.oef.xml` | Negative render-quality fixture | n/a | Explicit endpoint-lane case that fails source-geometry `AD-L13` |
| `render-quality-gate/fanout-crisscross.oef.xml` | Negative render-quality fixture | n/a | Local fan-out crossing case that fails source-geometry `AD-L15` |
| `render-quality-gate/endpoint-bendpoint-inside.oef.xml` | Negative render-quality fixture | n/a | Process-view route case that fails endpoint-bendpoint `AD-L11` |
| `render-quality-gate/hidden-realization-negative.oef.xml` | Negative render-quality fixture | n/a | Service Realization case that fails hidden-spine `AD-L20` |
| `layout-backend-contract/service-realization-request.yml` | Backend contract fixture | n/a | Normalized request with locked architect geometry and visible Realization spine constraints |
| `layout-backend-contract/service-realization-result.yml` | Backend contract fixture | n/a | Expected backend/fallback result preserving locked geometry and reporting zero moved locked nodes |
| `layout-backend-contract/locked-node-route-repair-request.yml` | Backend contract fixture | n/a | Route-only repair request with locked nodes and stale bendpoints crossing an obstacle |
| `layout-backend-contract/locked-node-route-repair-result.yml` | Backend contract fixture | n/a | Expected repair result rerouting the edge while preserving all locked node coordinates |
| `layout-contract/*.json` | Layout schema fixtures | n/a | Positive and negative request/result cases for `validate-request` and `validate-result`, including rich request fields plus parent, lock, and route-lock contradiction checks |
| `layout-elk-java/*.json` | Generated-layout runtime fixtures | n/a | Directed-view requests for `layout-elk`, including nested, locked-node, and unsupported-viewpoint cases |
| `layout-elk-realistic/*.{request.json,oef.xml}` | Generated-layout materialization fixtures | n/a | Larger nested OEF contexts for Application Cooperation trust boundaries, Technology Usage hosting stack, and Service Realization UI container; each request locks the existing OEF geometry, runs through `layout-elk`, materializes the result with `--snap-grid 10 --run-source-gate`, and preserves nested OEF node structure |
| `route-repair/*.json` | Route repair fixtures | n/a | Obstacle, parallel-edge, route-locked, impossible-route, and container-crossing repair cases |
| `global-polish/*.json` | Global polish fixtures | n/a | Overlap, connector-through-node, locked mental-map, and no-improvement cases |
| `materialize-oef/*.json` | OEF materialization fixtures | n/a | Layout-result handoff cases for `layout-elk`, `route-repair`, and `global-polish`, plus warning and source-gate failure paths |
| `rendered-png/*.png` | Rendered PNG validation fixtures | n/a | Blank, tiny, cropped, valid, and baseline-drift cases for `validate-png` |
| `../scripts/validate-oef-layout.sh` | Static layout gate | n/a | Emits Review-style `AD-L*` findings for source OEF geometry |
| `professional-quality-cases.md` | AD-Q expectations | n/a | Pressure cases for the professional-readiness pass: inventory views, thin process / service-realization views, orphaned decision context, and ambiguous labels |
| `layout-quality-cases.md` | AD-L expectations | n/a | Geometry cases for connector-through-node, allowed ancestor exits, long routes, stacked lanes, wide gaps, and fan-out crisscross |
| `lifting-quality-cases.md` | Extract expectations | n/a | Procedure cases for Bicep RBAC, deployment topology, forward-only seed views, and external trust boundaries |

## Acceptance bar

A fixture is "production-ready" when the relevant checks pass on the generated
layout result and rendered PNG:

1. **Mechanical (auto-checkable):** PNG dimensions are larger than Archi's blank 100 x 100 placeholder; zero blocking AD-L11 findings; zero unresolved AD-L1 / L2 / L3 / L9 / L12 / L13 / L14 / L15 findings before claiming `diagram-readable`; AD-L4 within budget; AD-L5 within `n/6` crossings; AD-L8 grid-aligned; AD-L10 normalised origin within tolerance.
2. **Visual (human judgment):** matches the per-viewpoint idiom in `layout-policies-by-viewpoint.md`; routes use consistent orthogonal lanes, ports, and lane spacing; labels do not collide with routes or other labels; gutters leave the view readable rather than merely non-overlapping; reads at the quality bar of the [Hosiaisluoma ArchiMate examples gallery](https://www.hosiaisluoma.fi/blog/archimate-examples/).
3. **Runtime contract:** JSON request/result fixtures validate against the shipped schemas; `layout-elk`, `route-repair`, and `global-polish` results remain deterministic, preserve locked geometry as declared, and can be materialized into OEF without custom glue.
4. **Deterministic:** re-running Build on the same input produces byte-identical OEF.
