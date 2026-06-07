# UML Data Views (`uml-data`)

Concern: data-type and enumeration structure for implementation handoff.
Delegate persistence and storage decisions to `software-design` (and
`infra-design` for managed data infrastructure).

## Source Contract

Use `kind: "uml-data"`. Source reference: `fixtures/source/valid-uml-complex.json`
(the data types and enumerations live there alongside the class content).

Node types:

- `DataType` — value type; `properties.uml.attributes` (array of
  `{name, type, visibility, multiplicity}`).
- `Enumeration` — `properties.uml.literals` (array of strings).
- `Package` — optional grouping via `properties.uml.package`.

Relationship types:

- `Dependency` — a data type depends on another type.

## Worked Example

Synthetic `uml-data` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.06.0"}],
  "nodes": [
    {"id": "dt-isbn", "type": "DataType", "label": "Isbn", "properties": {"uml": {"attributes": [{"name": "value", "type": "String", "visibility": "public", "multiplicity": "1"}]}}},
    {"id": "enum-loan-state", "type": "Enumeration", "label": "LoanState", "properties": {"uml": {"literals": ["Open", "Returned", "Overdue"]}}}
  ],
  "relationships": [],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "lending-data-view", "label": "Lending Data View", "kind": "uml-data", "nodes": ["dt-isbn", "enum-loan-state"], "relationships": []}]}}
}
```

## Validation, Render, Export

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- The SVG render path needs generated render metadata from
  `dediren project --target render-metadata --plugin generic-graph`.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
