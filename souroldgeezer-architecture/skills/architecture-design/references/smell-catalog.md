# Architecture Design Finding Catalog

Use one narrow code/severity per finding and cite evidence.

Codes: `ARCH-M-1` `ARCH-M-2` `ARCH-M-3` `ARCH-M-4`; `ARCH-V-1`
`ARCH-V-2` `ARCH-V-3` `ARCH-V-4`; `ARCH-L-1` `ARCH-L-2` `ARCH-L-3`
`ARCH-L-4`; `ARCH-R-1` `ARCH-R-2` `ARCH-R-3` `ARCH-R-4` `ARCH-R-5`; `ARCH-X-1`
`ARCH-X-2` `ARCH-X-3` `ARCH-X-4` `ARCH-X-5` `ARCH-X-6`; `ARCH-E-1` `ARCH-E-2` `ARCH-E-3`
`ARCH-E-4`; `ARCH-Q-1` `ARCH-Q-2` `ARCH-Q-3` `ARCH-Q-4`.

Severity: `block` invalid source or failed projection/layout/render/export;
`warn` quality, drift, incomplete realization, optional export; `info` disclosed gap.

- `ARCH-Q-3`: implementation-readiness claim exceeds evidence.
- `ARCH-X-2`: required architecture evidence is absent.
- `ARCH-V-4`: supported implementation-handoff diagram kind is absent.
- `ARCH-M-4`: architect-owned content is presented as extracted fact.
- `ARCH-M-1`: endpoint combination fails ArchiMate semantic validation; accepted Component-to-Interface Realization is not this.
- `ARCH-M-3`: wrong relationship semantics: ownership as Realization, API/GUI as Application Service, process sequencing as Serving.
- `ARCH-Q-2`: unclear concern, hub fanout, mixed concerns, audience incoherence, or vocabulary mixing.
- `ARCH-L-3`: valid layout but hard to scan: density, route congestion, empty groups, long spans, extreme aspect ratio.
- `ARCH-R-3`: nonblank SVG but labels, icons, or markers obscure the message, or an edge label sits closer to a different edge than its own route.
- `ARCH-M-2`: package source fails schema validation (`dediren_validate` error envelope).
- `ARCH-V-1`: `package.json` declares a view with no model content or whose projection fails.
- `ARCH-L-2`: layout validation reports connector-through-node, invalid route, or group-boundary errors.
- `ARCH-L-4`: grouped layout regresses against its ungrouped rerun; fallback layout used as evidence.
- `ARCH-R-1`: SVG render fails, or produces blank content or an incoherent `viewBox`.
- `ARCH-R-2`: rendered SVG is missing expected `data-dediren-node-id` /
  `data-dediren-edge-id` markers, the `architecture.md` §9 post-render
  accessible-name markup (`role="img"`, nonempty `<title>`, visible title
  block), or authored UML association end adornments (roles/multiplicities)
  present in the view's render metadata (`architecture.md` §9 end-adornment
  coverage check); or a package gallery drifted from its SVGs. A `stale` verdict
  from `dediren_verify` on a rendered SVG or gallery artifact also backs this
  (`architecture.md` §9).
- `ARCH-R-4`: `plugins.generic-graph.semantic_profile`, the generated metadata profile, and the `render-policy.json` profile disagree.
- `ARCH-R-5`: emitted SVG is not static as required: a `<script>` element in the
  rendered artifact (renders are static-only — the runtime retired the
  interactive render policy), or a `Layout/render options` line that misreports
  what the artifact contains (`architecture.md` §9 render-mode check).
- `ARCH-E-4`: committed export output is stale against current package source or layout evidence; a `stale` verdict from `dediren_verify` on an OEF/XMI export artifact backs this (`architecture.md` §9).
- `ARCH-Q-1`: claimed quality level exceeds the validation stages actually proven.
- `ARCH-Q-4`: required output footer fields are missing or mutually inconsistent (a quality-level over-claim is `ARCH-Q-1`).

Remaining codes are defined where they are used: `ARCH-X-1`, `ARCH-X-3`,
`ARCH-X-4`, `ARCH-X-5`, `ARCH-X-6` in `procedures/drift-detection.md`; `ARCH-E-1`, `ARCH-E-2`,
`ARCH-E-3` in `procedures/external-validation-handoff.md`; `ARCH-V-2` in
`procedures/process-view-emission.md`; `ARCH-V-3` in
`procedures/implementation-readiness-review.md`; `ARCH-L-1` in
`../../../docs/architecture-reference/architecture.md` §9 and `procedures/architecture-operational-workflow.md`.
