# UML Data Views (`uml-data`)

Concern: data-type and enumeration structure for implementation handoff.
Delegate persistence and storage decisions to `software-design` (and
`infra-design` for managed data infrastructure).

## Source Contract

Use `kind: "uml-data"`. Carry data-type attributes, enumeration literals, and
multiplicities under `properties.uml`. Use the UML source fixtures in the
selected Dediren release bundle as the reference.

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
