# UML Class Views (`uml-class`)

Concern: package, class, interface, and type structure for implementation
handoff. Delegate exact code internals (method bodies, language idioms) to
`software-design`.

## Source Contract

Use `kind: "uml-class"`. Carry attributes, operations, multiplicities, and
package membership under `properties.uml`. Use
`fixtures/source/valid-uml-complex.json` in the selected Dediren release bundle
as the current non-trivial source reference; recheck the live release before
claiming full UML 2.5.1 coverage.

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
