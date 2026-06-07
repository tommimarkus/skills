# UML Sequence Views (`uml-sequence`)

Concern: one interaction (message exchange over time) between participants, as
implementation handoff detail inside a dediren package. Delegate the underlying
control-flow and code decisions to `software-design`, and HTTP call contracts to
`api-design`.

## Source Contract

Use `kind: "uml-sequence"` with an `Interaction`, participating `Lifeline`
nodes, and `Message` relationships. Put ordering under `properties.uml.sequence`
and message category under `properties.uml.message_sort`. Use
`fixtures/source/valid-uml-sequence-basic.json` in the selected Dediren release
bundle as the minimum source reference.

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
