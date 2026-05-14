# Architecture Design Finding Catalog

Use one code and severity per finding. Cite a source path, id, command output,
artifact, or supplied downstream evidence. Prefer the narrowest code.

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-M-1` | block | Invalid relationship source/target types. |
| `ARCH-M-2` | block | Source-grounded element has missing or stale evidence. |
| `ARCH-M-3` | warn | Type, label, or layer contradicts documented role. |
| `ARCH-M-4` | warn | Architect-owned content is presented as extracted fact. |
| `ARCH-V-1` | block | `project.json` view cannot be projected. |
| `ARCH-V-2` | warn | View omits the primary relationship. |
| `ARCH-V-3` | warn | Viewpoint or diagram kind misses the audience concern. |
| `ARCH-V-4` | info | Supported diagram kind is absent; disclose, do not stub. |
| `ARCH-L-1` | block | Layout command fails or returns an error envelope. |
| `ARCH-L-2` | warn | Layout validation reports overlap, bad route, or group warnings. |
| `ARCH-L-3` | warn | Layout is too dense, tiny, or poorly framed. |
| `ARCH-L-4` | info | Layout policy weakens requested grouping, direction, or routing. |
| `ARCH-R-1` | block | SVG render fails or returns an error envelope. |
| `ARCH-R-2` | block | SVG is blank, missing markers, or has bad `viewBox`. |
| `ARCH-R-3` | warn | Labels, icons, or markers obscure the message. |
| `ARCH-R-4` | info | Render policy is usable but visually inconsistent. |
| `ARCH-X-1` | warn | Extracted model no longer matches source. |
| `ARCH-X-2` | warn | Lifted element lacks source evidence. |
| `ARCH-X-3` | info | Source label changed; architecture label may be intentional. |
| `ARCH-X-4` | warn | Source implies an omitted or reversed relationship. |
| `ARCH-E-1` | block | OEF export fails or returns an error envelope. |
| `ARCH-E-2` | warn | Supplied downstream OEF validation still fails. |
| `ARCH-E-3` | info | OEF requested but no export policy exists. |
| `ARCH-E-4` | warn | Export policy no longer matches `project.json`. |
| `ARCH-Q-1` | block | Blocking finding prevents review-ready. |
| `ARCH-Q-2` | warn | View is dense, audience-incoherent, or unclear. |
| `ARCH-Q-3` | warn | Quality claim exceeds dediren evidence. |
| `ARCH-Q-4` | info | Diagram-kind coverage is incomplete but disclosed. |

Severity: `block` for invalid source, failed projection/layout/render/export, or
unsupported claims; `warn` for quality defects, drift, incomplete realization,
and optional export problems; `info` for disclosed gaps, cosmetic issues, and
intentional choices.

Modeling-rule routing:

- `ARCH-M-1`: relationship endpoint combination fails ArchiMate semantic
  validation. Do not route accepted Component-to-Interface Realization here.
- `ARCH-M-3`: Application Component realizes Application Interface when the
  stated model claim is component-interface ownership.
- `ARCH-M-3`: API/GUI surface is typed or named as Application Service.
- `ARCH-M-3`: process sequencing evidence uses Serving instead of Triggering.
- `ARCH-Q-2`: view lacks a clear concern or mixes vocabularies.
