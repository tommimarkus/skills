# Seed views for forward-only stubs

Procedure for making Extract's architect-owned stubs visible in OEF views. Invoked by Extract after forward-only Strategy / Motivation / Business Service stubs exist and before `layout-strategy.md` computes coordinates.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). Forward-only rules live in §7.2 / §7.3; view contracts live in §9.1 and §9.6.

## When to emit

Emit seed views only for stubs created or preserved by Extract:

| Stub set present | Seed view |
|---|---|
| One or more Strategy `Capability` stubs, optionally with forward-only Business Services and lifted Application Services | FORWARD-ONLY Capability Map seed view |
| One or more Motivation `Driver`, `Goal`, `Outcome`, `Principle`, `Requirement`, `Constraint`, or `Stakeholder` stubs | FORWARD-ONLY Motivation seed view |

Do not emit seed views for an architect-authored model that already contains a view with the same purpose. Preserve existing seed views by identifier on re-extract.

## Capability Map seed view

View attributes:

- `viewpoint="Capability Map"`
- `<name>` suffix: `FORWARD-ONLY seed`
- `<documentation>`: `Seed scaffold from Extract. Architect to validate/rename elements, refine the Realization chain, and add additional Strategy / Business elements as needed.`

Content:

- Strategy row: every forward-only Capability stub.
- Business row: every forward-only Business Service that Realizes a Capability.
- Application row: every lifted Application Service that Realizes a Business Service.
- Relationships: existing Realization edges only; do not invent missing chains.

Layout is delegated to `layout-strategy.md` §9.1. If the view would exceed `AD-L4`, split by Capability root.

## Motivation seed view

View attributes:

- `viewpoint="Motivation"`
- `<name>` suffix: `FORWARD-ONLY seed`
- `<documentation>`: `Seed scaffold from Extract. Architect to validate/rename Motivation elements, connect them to architecture decisions, and add missing stakeholders, drivers, outcomes, principles, requirements, or constraints.`

Content:

- Every forward-only Motivation stub.
- Existing Influence, Realization, Association, and Specialization relationships between those Motivation elements.
- Existing Realization relationships from architecture elements to Motivation elements when already present.

Layout is delegated to `layout-strategy.md` §9.6. Motivation nodes with no relationship are allowed in the seed view only when their documentation states that they are placeholders; otherwise Review reports `AD-Q7` or `AD-L12`.

## Organization

Place emitted seed views under an organization item labelled `Forward-only seed views`. This organization affects discoverability in tools; it is not a layer container and does not change model semantics.
