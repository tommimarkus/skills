# UML Deployment Views (`uml-deployment`)

Concern: artifact-to-node deployment for handoff. Delegate topology and hosting
decisions to `infra-design` plus ArchiMate Technology Usage (prefer ArchiMate /
infra-design for architecture-level hosting).

## Source Contract

Use `kind: "uml-deployment"`. Primary node types: `Node`, `Device`,
`ExecutionEnvironment`, `Artifact`, `DeploymentSpecification`. Primary
relationship types: `CommunicationPath`, `Deployment`, `Manifestation`. Use
`fixtures/source/valid-uml-deployment-basic.json` in the selected Dediren
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
