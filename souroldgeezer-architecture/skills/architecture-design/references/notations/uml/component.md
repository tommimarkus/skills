# UML Component Views (`uml-component`)

Concern: implementation components, their interfaces, and ports for handoff.
Delegate the structural decision to `software-design` plus ArchiMate Application
Cooperation (prefer ArchiMate for architecture-level structure).

## Source Contract

Use `kind: "uml-component"`. Primary node types: `Component`, `Interface`,
`Port`, `Class`, `Package`. Primary relationship types: `Realization`, `Usage`,
`Dependency`. Use
`fixtures/source/valid-uml-component-basic.json` in the selected Dediren release
bundle as the source reference. Full per-element guidance is a later phase.

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
