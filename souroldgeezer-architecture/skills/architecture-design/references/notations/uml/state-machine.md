# UML State Machine Views (`uml-state-machine`)

Concern: the states and transitions of one element's behavior, as handoff
detail. Delegate the behavior implementation to `software-design`.

## Source Contract

Use `kind: "uml-state-machine"`. Primary node types: `StateMachine`, `Region`,
`State`, `Pseudostate` (initial), `FinalState`. Primary relationship type:
`Transition`. Carry guards and effects under `properties.uml`. Use
`fixtures/source/valid-uml-state-machine-basic.json` in the selected Dediren
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
