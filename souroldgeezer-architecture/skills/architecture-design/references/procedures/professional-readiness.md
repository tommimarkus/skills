# Professional Readiness

Use these levels in Build, Extract, and Review.

- `source-valid`: source validates; ids and relationships resolve.
- `view-readable`: source-valid plus actual views project, layout, validate.
  This is layout-valid evidence, not a visually clean claim.
- `render-ready`: view-readable plus inspected nonblank marker-rich SVG and a
  visual-readiness pass for density, framing, label risk, and audience fit.
- `review-ready`: render-ready plus no blocking `ARCH-*` finding.

The package rollup is the weakest applicable level across actual views.

Authority: `lifted-from-source` only when every visible claim has current
evidence; `forward-only-or-inferred` for intent/future/process candidates;
`architect-approved` or `stakeholder-validated` only when supplied.
Contradictory authority claims are `ARCH-Q-3`.

Supported kinds: Capability Map, Application Cooperation, Service Realization,
Technology Usage, Migration, Motivation, Business Process Cooperation. Missing
kinds are footer disclosure, not placeholder views.

Valid layout can still be hard to read. Emit `ARCH-L-3`, `ARCH-R-3`, or
`ARCH-Q-2` when a view is dense, hub-heavy, label-obscured, route-congested,
too wide/tall, group-imbalanced, or mixes concerns from multiple audiences.
When a process, realization, technology-usage, or migration view becomes hard
to scan, prefer splitting the concern over accepting the first valid render.

## Valid But Not Useful

layout-valid evidence can still fail the audience. Do not claim
`render-ready` or `review-ready` when a valid rendered view is too dense,
mixes unrelated concerns, hides the primary relationship, or needs source code
inspection to understand the message.

Examples:

- Application Cooperation view includes every component, route, DTO, cloud
  resource, and workflow in one graph: report `ARCH-Q-2` and split by concern.
- Technology Usage view mixes hosting, data, identity/security, and
  observability: report `ARCH-Q-2` or `ARCH-L-3` and split the view.
- Service Realization view hides the realization path behind unrelated
  dependencies: report `ARCH-V-2`.
