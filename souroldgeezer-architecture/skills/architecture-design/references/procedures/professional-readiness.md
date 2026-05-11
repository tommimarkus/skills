# Professional Readiness

Use these levels in Build, Extract, and Review.

## Levels

- `source-valid`: `model.json` validates, ids are unique, relationships resolve,
  and relationship types are legal for their source/target element types.
- `view-readable`: source-valid plus each actual view in `project.json` can be
  projected, laid out, and layout-validated.
- `render-ready`: view-readable plus SVG render evidence exists for changed or
  requested views and the SVG is nonblank, framed, and marker-rich.
- `review-ready`: render-ready plus no blocking `ARCH-*` finding remains for
  the intended audience and diagram kind.

The package rollup is the weakest applicable level across actual views.

## Authority

Default authority is `lifted-from-source` when every visible claim has current
source evidence. Use `forward-only-or-inferred` when architect intent, future
state, or unconfirmed process candidates are present. Use
`architect-approved` or `stakeholder-validated` only when the user supplies that
status.

Contradictory authority claims are `ARCH-Q-3`.

## Coverage

Supported diagram kinds are Capability Map, Application Cooperation, Service
Realization, Technology Usage, Migration, Motivation, and Business Process
Cooperation. Missing kinds are a footer disclosure, not placeholder entries in
`project.json`.
