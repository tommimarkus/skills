# UML Activity Views (`uml-activity`)

Concern: control and object flow for a procedure or behavior, as handoff detail.
Delegate business-process ownership to ArchiMate Business Process Cooperation in
this skill, and code-level control flow to `software-design`.

## Source contract

Use `kind: "uml-activity"`. Carry guards and partitions under `properties.uml`.
Use the UML source fixtures in the selected Dediren release bundle as the
reference.

## Validation, render, export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- SVG render uses generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub for the mapping).
