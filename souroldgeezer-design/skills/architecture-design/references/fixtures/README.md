# architecture-design fixtures

Small ArchiMate® OEF XML files exercising all seven supported §9 viewpoints at representative scale (7-15 elements, 6-20 relationships). Fixtures are regression targets for the Sugiyama-v1 layout engine: each fixture carries a materialized view with nodes, relationships, bendpoints, and spacing that should render as a professional-quality diagram. The rendered PNG output is the validation artefact.

## How fixtures are used

1. Build mode invokes the skill with the fixture's element / relationship set as architect intent.
2. Tier 0 finds no prior view at the canonical path, so all elements get algorithmic placement.
3. Tier 1 (Phases 1-6) + Tier 2 (per-viewpoint specialisation) compute coordinates.
4. The skill writes the resulting OEF, including `<node>` and `<connection>` geometry in the `<view>`.
5. `archi-render.sh` (in a consuming project, dev-time only) renders the OEF to PNG.
6. Visual inspection checks that the PNG is nonblank, spacious, consistently routed, and at the per-viewpoint acceptance bar (see spec §6.2 of `docs/superpowers/specs/2026-04-25-architecture-design-pro-quality-design.md`).

## Render

```bash
# From a project with archi-render.sh installed (e.g. lfm-org/lfm)
cd /path/to/lfm
./scripts/archi-render.sh \
  --cache-root /tmp/archi-fixture-cache \
  --output-root /tmp/archi-fixture-views \
  /path/to/architecture-design/references/fixtures/<fixture>.oef.xml
ls /tmp/archi-fixture-views/<fixture>/
```

## Validate every available diagram

Every committed `*.oef.xml` in this directory must pass the render gate before
the fixture set is considered valid:

```bash
./validate-render-fixtures.sh \
  --render-script /path/to/lfm/scripts/archi-render.sh \
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
The negative fixture in `render-quality-gate/cropped-but-failing.oef.xml` is
well-formed OEF that can render as a cropped PNG but must fail `AD-L10` and
`AD-L11` from the source geometry.

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
| `../scripts/validate-oef-layout.sh` | Static layout gate | n/a | Emits Review-style `AD-L*` findings for source OEF geometry |
| `professional-quality-cases.md` | AD-Q expectations | n/a | Pressure cases for the professional-readiness pass: inventory views, thin process / service-realization views, orphaned decision context, and ambiguous labels |
| `layout-quality-cases.md` | AD-L expectations | n/a | Geometry cases for connector-through-node, allowed ancestor exits, long routes, stacked lanes, wide gaps, and fan-out crisscross |
| `lifting-quality-cases.md` | Extract expectations | n/a | Procedure cases for Bicep RBAC, deployment topology, forward-only seed views, and external trust boundaries |

## Acceptance bar

A fixture is "production-ready" when all three pass on the rendered PNG:

1. **Mechanical (auto-checkable):** PNG dimensions are larger than Archi's blank 100 x 100 placeholder; zero blocking AD-L11 findings; zero unresolved AD-L1 / L2 / L3 / L9 / L12 / L13 / L14 / L15 findings before claiming `diagram-readable`; AD-L4 within budget; AD-L5 within `n/6` crossings; AD-L8 grid-aligned; AD-L10 normalised origin within tolerance.
2. **Visual (human judgment):** matches the per-viewpoint idiom in `layout-strategy.md` Tier 2; routes use consistent orthogonal lanes; labels do not collide with routes or other labels; gutters leave the view readable rather than merely non-overlapping; reads at the quality bar of the [Hosiaisluoma ArchiMate examples gallery](https://www.hosiaisluoma.fi/blog/archimate-examples/).
3. **Deterministic:** re-running Build on the same input produces byte-identical OEF.
