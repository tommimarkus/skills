# Layout strategy - viewpoint-constrained OEF geometry policy

Procedure for producing `<view>` node placements that are readable,
diff-stable, and round-trippable through ArchiMate® conformant tools. Invoked
by Build and Extract after the semantic model is known. Review uses the same
contract, restated as `AD-L*` and `AD-Q*` checks, to judge final OEF quality.

The reference is
[../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md).
The structural rules this procedure operationalises live in §6.4a *Layout
strategy*. Layout smell codes are defined in
[../smell-catalog.md](../smell-catalog.md).

## Purpose

The skill produces a semantic layout request. A backend, existing
architect-authored geometry, or the bundled fallback procedure produces
coordinates and bendpoints. The skill then validates and serialises the final
geometry as OEF XML.

Professional readiness is based on the final OEF materialisation and
visual/semantic quality, not on which backend produced the geometry.

## Non-goals

- Do not make one concrete graph-layout algorithm the theory of the skill.
- Do not make the bundled Java™ generated-layout path, route-repair path, global-polish path,
  libavoid, Graphviz, maxGraph, yFiles, PCB routers, or any other runtime
  dependency a semantic authority.
- Do not weaken the materialized-view contract when a backend is unavailable.
- Do not use a geometry backend to invent ArchiMate model elements, remove
  relationships, change relationship direction, or reinterpret viewpoint
  semantics.
- Do not use PCB or diagram-editor routing tools directly as an ArchiMate
  semantic authority. Their concepts can inspire route repair; the OEF quality
  gate remains the authority.

## Materialized view contract

Every generated `<view>` must contain:

- at least one non-legend `<node xsi:type="Element">` with `elementRef`, `x`,
  `y`, `w`, and `h`;
- a `<connection xsi:type="Relationship">` for each relationship that carries
  the view's visual story, with `source` and `target` pointing at view-node
  identifiers;
- bendpoints on long or non-aligned routes, rather than diagonal shortcuts; and
- identifiers that are unique across the entire OEF file, including model
  elements, relationships, views, view nodes, and view connections.

An OEF file with valid `<elements>` and `<relationships>` but empty views is a
model inventory. It may import, but it fails the layout contract and cannot be
classified above `model-valid`.

## Core principle: semantic policy, backend-neutral geometry

The architecture-design skill owns semantic policy:

- supported ArchiMate® 3.2 viewpoints and layer/aspect discipline;
- which visual grammar fits each viewpoint;
- which relationships must remain visible;
- which curation/hiding choices are semantically safe;
- which geometry is locked because an architect authored it; and
- which `AD-L*`, `AD-Q*`, and OEF checks decide readiness.

Geometry backends own placement and routing mechanics only. A backend consumes
the normalized request described in
[layout-backend-contract.md](layout-backend-contract.md) and returns node
coordinates, ports, bendpoints, and metrics. Backend output is never trusted
without the final validation handoff.

## Pipeline

1. **Preserve existing architect-authored geometry.** Reuse prior `<node>`
   placements matched by `elementRef` unless the user explicitly requests global
   reflow. Reuse prior bendpoints only when the relationship reference,
   source node, target node, and `AD-L11` route validation still pass.
2. **Build the normalized layout request.** Include nodes, edges, hierarchy,
   prior coordinates, locks, viewpoint, semantic bands, edge priority, route
   constraints, and generated-vs-authored flags per
   [layout-backend-contract.md](layout-backend-contract.md).
3. **Choose the viewpoint-specific layout policy.** Dispatch by the OEF
   `viewpoint=` value and apply the visual grammar in
   [layout-policies-by-viewpoint.md](layout-policies-by-viewpoint.md).
4. **Select a layout backend or fallback and record the decision.** For
   `generated-layout-recreate` on Application Cooperation, Service Realization,
   and Technology Usage views, build the normalized request, run
   `arch-layout.sh validate-request`, run `arch-layout.sh layout-elk`, run
   `arch-layout.sh validate-result`, and run `arch-layout.sh materialize-oef`
   unless a command is unavailable, validation fails, or the view has explicit
   locked geometry. For unsupported viewpoints, do not silently hand-author geometry as
   if a backend ran; select the viewpoint-specific policy or fallback and record
   the fallback reason. For architect-edited diagrams under
   `preserve-authored`, prefer `route-repair`; when route-only repair cannot
   clean the view without damaging the mental map, use `global-polish`.
5. **Assign ports and route edges.** Apply
   [routing-and-glossing.md](routing-and-glossing.md): assign candidate ports,
   reserve lanes for high-priority edges, route high-priority paths first, and
   repair routes without moving locked nodes.
6. **Gloss routes.** Remove redundant bendpoints, simplify tiny zigzags, align
   parallel lanes, separate coincident lanes, and rerun post-route validation.
7. **Normalize generated or mixed views.** Shift new and mixed generated views
   to the `(40, 40)` used-region origin. Do not shift a fully preserved
   architect-authored view solely for cosmetic origin alignment.
8. **Validate with `AD-L*` checks.** Run the source-geometry gate when a local
   OEF path exists. A backend result that fails `AD-L*` is not
   `diagram-readable`.

## Layout decision record

Every Build / Extract run that emits or changes view geometry records one row
per view before final delivery:

| Field | Required value |
|---|---|
| View id | OEF `<view identifier>` |
| Viewpoint | Exact OEF `viewpoint=` value |
| Layout intent | `preserve-authored`, `route-repair-only`, `generated-layout-recreate`, or `global-reflow` |
| Eligibility | `layout-elk eligible`, `route-repair eligible`, `global-polish eligible`, `viewpoint-policy only`, or `blocked` |
| Selected geometry path | `layout-elk`, `route-repair`, `global-polish`, `deterministic-fallback`, `viewpoint-policy`, or `preserved-authored` |
| Request validation | `passed`, `failed`, or `not run` with reason |
| Result validation | `passed`, `failed`, or `not run` with reason |
| OEF materialization | `materialized`, `not changed`, or `blocked` |
| PNG validation | `not requested`, `validate-png passed`, `validate-png failed`, or `not run` with reason |
| Notes | Exact blocker, fallback reason, locked-geometry reason, or unsupported-viewpoint policy |

This record distinguishes layout generation from render validation.
`arch-layout.sh validate-png` validates rendered PNG invariants only; it is
never evidence that `arch-layout.sh layout-elk`, `route-repair`, or
`global-polish` generated OEF geometry, or that `materialize-oef` applied the
result to the source OEF.

## Backend selection

| Situation | Preferred policy |
|---|---|
| New generated Service Realization view | Packaged Java™ `layout-elk` layered/orthogonal backend when appropriate; fallback deterministic layered layout otherwise |
| Existing architect-edited view | Preserve node geometry; packaged Java™ `route-repair` for invalid generated/stale routes; gloss generated or invalid routes |
| Capability Map | Capability tile/decomposition map; never generic layered layout as the primary policy |
| Application Cooperation | Clustered dependency/integration layout; hub-and-spoke only when a hub criterion is met |
| Service Realization | Layered realization spine with the main Realization chain visible |
| Technology Usage | Hosting/deployment stack with applications aligned over hosts |
| Migration | Plateau/timeline layout; do not infer migration from ordinary dev/stage/prod deployment |
| Motivation | Influence/traceability tree |
| Business Process Cooperation | Flow, swimlane, and handoff layout |
| Existing view needing bounded local movement | Packaged Java™ `global-polish` only when route-only repair is insufficient and locked geometry remains fixed |
| Small generic directed view with no better policy | Fallback deterministic layered layout |

Future backlog remains explicit: interactive layout debugger export,
relationship-matrix source provenance, mainstream tool compatibility execution,
and multi-evidence recovery are not shipped by this runtime.

## Fallback

The bundled fallback is
[fallback deterministic layered layout](layout-fallback.md). It preserves the
deterministic conventions introduced in the earlier layered-layout procedure:
architect-position preservation, ArchiMate layer/aspect bands, 4-pass
barycentric ordering, median coordinate assignment, deterministic tiebreaks,
10-px grid, default element sizes, bounding-box normalization, and post-layout
`AD-L*` checks.

The fallback is adequate for small generated directed views. It is not a full
modern graph-layout engine. When a supported backend is available, prefer that
backend for complex generated views and preserve/repair mode for
architect-edited views.

## Relationship curation and hiding

Relationship curation is a view concern, not a model change. A relationship may
be omitted or hidden in one view only when the model relationship remains and
the view documentation or final summary names the relationship id and reason.

Default hide-by-nesting is limited to:

- `Composition`; and
- `Aggregation`, when the part-whole semantics are clear.

`Assignment` may be represented through nesting only in viewpoint-specific
cases where the visual grammar supports it, such as hosting or internal
behaviour ownership.

Do not use nesting or redundancy rules to replace:

- `Serving`;
- `Access`;
- `Flow`;
- `Triggering`; or
- the main `Realization` spine in Service Realization or realization-chain
  views.

`Realization` often carries the architectural argument. Keep it visible by
default. Hide it only when a viewpoint policy explicitly marks the specific
relationship as non-spine redundancy and the view remains auditable without
verbal explanation.

## Readiness impact

Readiness follows the final OEF, not the backend name.

- Missing materialized node or relationship geometry caps the affected view at
  `model-valid`.
- Unresolved connector-through-node (`AD-L11`) caps the affected view at
  `model-valid`.
- Invalid nesting/hiding, hidden main Realization spines, route congestion,
  wide gaps, fan-out crisscross, duplicate visible story paths, or misleading
  boundaries cap the view at `diagram-readable` or `model-valid` per
  [professional-readiness.md](professional-readiness.md).
- Backend output accepted without the OEF/source-geometry validation handoff is
  itself a review finding.

## Compatibility with existing validation smells

This refactor keeps the existing `AD-L*` contract and makes it backend-neutral:

- `AD-L1` through `AD-L6` still cover layer ordering, overlap, sizing,
  density, crossings, and orthogonality.
- `AD-L7` still catches double representation through nesting plus visible
  edge, but hide-by-nesting no longer applies to the main Realization spine by
  default.
- `AD-L8` through `AD-L11` still cover grid, hierarchy, origin, and
  connector-through-node failures.
- `AD-L12` through `AD-L19` still cover orphan nodes, stacked lanes, gaps,
  fan-out crisscross, long routes, duplicate story paths, misleading boundary
  crossings, and unsupported nesting.
- `AD-L20` covers hidden Service Realization spine edges when a visible
  Realization chain is required.

The fallback, any future backend, and hand-authored geometry all pass through
the same final checks.
