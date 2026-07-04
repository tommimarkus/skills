# Professional Readiness

Use these levels in Build, Extract, and Review.

- `source-valid`: source validates; ids and relationships resolve.
- `view-readable`: source-valid plus actual views project, layout, validate.
  This is layout-valid evidence, not a visually clean claim.
- `render-ready`: view-readable plus inspected nonblank marker-rich SVG
  carrying the `architecture.md` §9 accessible-name markup and visible title
  (post-render step; missing is `ARCH-R-2`), a visual-readiness pass for
  density, framing, label risk — including the label-to-own-edge distance
  check (`architecture.md` §7) — and audience fit, and, for UML views with
  authored association end adornments, the `architecture.md` §9
  end-adornment coverage check with its quality-level coverage qualifier.
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
`ARCH-Q-2` when a view is dense, hub-heavy, label-obscured, label-dissociated,
route-congested, too wide/tall, group-imbalanced, or mixes concerns from
multiple audiences.
For density, routing, or framing problems, tune the dediren layout
(`architecture.md` §9 `layout_preferences`) and re-validate before reporting;
reserve splitting the concern (§7) for genuinely mixed audiences, an inventory
view, or a view that layout tuning cannot make scannable.

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
