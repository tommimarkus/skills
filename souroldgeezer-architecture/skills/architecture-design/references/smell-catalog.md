# Architecture Design Finding Catalog

Use one narrow code/severity per finding and cite evidence.

Codes: `ARCH-M-1` `ARCH-M-2` `ARCH-M-3` `ARCH-M-4`; `ARCH-V-1`
`ARCH-V-2` `ARCH-V-3` `ARCH-V-4`; `ARCH-L-1` `ARCH-L-2` `ARCH-L-3`
`ARCH-L-4`; `ARCH-R-1` `ARCH-R-2` `ARCH-R-3` `ARCH-R-4`; `ARCH-X-1`
`ARCH-X-2` `ARCH-X-3` `ARCH-X-4`; `ARCH-E-1` `ARCH-E-2` `ARCH-E-3`
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
- `ARCH-R-3`: nonblank SVG but labels, icons, or markers obscure the message.
