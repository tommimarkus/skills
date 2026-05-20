# ArchiMate Notation

Load when a package uses `plugins.generic-graph.semantic_profile: "archimate"`,
an ArchiMate view kind, OEF export, or an architecture-level modeling request.

ArchiMate frames the architectural concern: stakeholder-facing enterprise,
business, application, technology, motivation, migration, and cross-system
meaning. Use UML only to elaborate a bounded part when implementation handoff
needs class, data, package, or activity detail.

## Validation

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile archimate`.
- Generated SVG metadata uses `plugins.generic-graph.semantic_profile:
  "archimate"`.
- OEF compatibility export uses `archimate-oef` only when requested or when
  downstream validation evidence is supplied.
- relationship connectors and junctions unsupported in dediren package source;
  report them instead of inventing silent replacements.

## Boundary

- ArchiMate owns capabilities, services, components, interfaces, business
  processes, data objects, technology nodes, deployment context, motivation,
  migration, and dependencies between bounded systems.
- ArchiMate may reference UML elaboration through explicit package metadata,
  but does not carry detailed class attributes, operations, multiplicities,
  guards, or partitions by default.
- If linked UML contradicts the ArchiMate intent, report a handoff
  inconsistency and preserve the ArchiMate architecture decision until the user
  or architect changes it.
