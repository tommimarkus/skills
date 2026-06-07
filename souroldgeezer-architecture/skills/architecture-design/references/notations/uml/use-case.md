# UML Use Case Views (`uml-use-case`)

Concern: actor goals and system scope for handoff. Delegate requirements and
motivation ownership to ArchiMate Motivation / requirements work.

## Source Contract

Use `kind: "uml-use-case"`. Primary node types: `Actor`, `UseCase`,
`ExtensionPoint`. Primary relationship types: `Association`, `Include`, `Extend`.
Use `fixtures/source/valid-uml-use-case-basic.json` in the selected Dediren
release bundle as the source reference. Full per-element guidance is a later
phase.

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
