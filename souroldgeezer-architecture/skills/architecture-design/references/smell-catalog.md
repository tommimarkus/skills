# Architecture Design Finding Catalog

Use one code/severity per finding. Cite path, id, command output, artifact, or
downstream evidence. Prefer the narrowest code.

Codes:

- Model: `ARCH-M-1` block invalid relationship source/target; `ARCH-M-2` block
  missing/stale evidence; `ARCH-M-3` warn role mismatch; `ARCH-M-4` warn
  architect-owned content as extracted fact.
- View/layout/render: `ARCH-V-1` block unprojectable view; `ARCH-V-2` warn
  omitted primary relation; `ARCH-V-3` warn concern mismatch; `ARCH-V-4` info
  absent supported kind. `ARCH-L-1` block layout error; `ARCH-L-2` warn
  overlap/route/group warnings; `ARCH-L-3` warn dense/tiny/framing; `ARCH-L-4`
  info weakened policy. `ARCH-R-1` block render error; `ARCH-R-2` block bad SVG;
  `ARCH-R-3` warn obstruction; `ARCH-R-4` info inconsistency.
- Drift/export/quality: `ARCH-X-1` warn drift; `ARCH-X-2` warn no evidence;
  `ARCH-X-3` info label changed; `ARCH-X-4` warn omitted/reversed relation.
  `ARCH-E-1` block export error; `ARCH-E-2` warn downstream failure;
  `ARCH-E-3` info missing policy; `ARCH-E-4` warn policy mismatch.
  `ARCH-Q-1` block no review-ready; `ARCH-Q-2` warn dense/incoherent/unclear;
  `ARCH-Q-3` warn claim exceeds evidence; `ARCH-Q-4` info coverage disclosed.

Severity: `block` invalid source, failed projection/layout/render/export, or
unsupported claims; `warn` quality/drift/incomplete realization/optional export;
`info` disclosed gaps and intentional choices.

Routing:

- `ARCH-M-1`: endpoint combination fails ArchiMate semantic validation. Do not
  route accepted Component-to-Interface Realization here.
- `ARCH-M-3`: Realization used for component-interface ownership, API/GUI typed
  as Application Service, or process sequencing modeled with Serving.
- `ARCH-Q-2`: view lacks a clear concern, mixes vocabularies, is hub-heavy, has
  hub fanout, is audience-incoherent, or mixes multiple viewpoint concerns.
- `ARCH-L-3`: layout validates but density, long spans, extreme aspect ratio,
  empty groups, or route congestion make it hard to scan.
- `ARCH-R-3`: SVG is nonblank but labels, icons, or markers obscure the message.
