# Architecture Design Red Flags

Stop or lower the claimed readiness when any of these are true:

- `project.json` references a missing `model.json`, policy, metadata file,
  plugin, view id, or generated input.
- The model contains duplicate ids, dangling relationships, invalid
  source/target relationship types, or stale source evidence. Use
  `ARCH-M-*`.
- A view listed in `project.json` cannot be projected or omits the relationship
  that makes the view meaningful. Use `ARCH-V-*`.
- Layout fails, emits an error envelope, or validation reports overlap,
  connector-through-node, invalid route, or group-boundary warnings. Use
  `ARCH-L-*`.
- SVG rendering fails, produces a blank artifact, lacks dediren node/edge
  markers, or has an incoherent `viewBox`. Use `ARCH-R-*`.
- Extracted elements or relationships no longer match source, IaC, UI routes,
  APIs, or workflows. Use `ARCH-X-*`.
- OEF export was requested and fails, lacks a policy, or downstream validation
  evidence reports unresolved problems. Use `ARCH-E-*`.
- The package is presented as `review-ready` while any blocking finding remains,
  or the view is too dense or audience-incoherent. Use `ARCH-Q-*`.

Do not add placeholder views just to satisfy coverage expectations. List only
actual views in `project.json` and disclose missing diagram kinds in the footer.

Do not claim render quality from source inspection alone. Render-ready means the
SVG command ran for the relevant view and the artifact was inspected for
nonblank, framed, marker-rich output.
