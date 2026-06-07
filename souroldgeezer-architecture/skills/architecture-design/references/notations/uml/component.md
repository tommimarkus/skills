# UML Component Views (`uml-component`)

Concern: implementation components, their interfaces, and ports for handoff.
Delegate the structural decision to `software-design` plus ArchiMate Application
Cooperation (prefer ArchiMate for architecture-level structure).

## Source Contract

Use `kind: "uml-component"`. Source reference:
`fixtures/source/valid-uml-component-basic.json`.

Node types:

- `Package` — namespace grouping; `properties.uml.kind: "package"`. **View
  constraint:** `Package` nodes may not appear in the view `nodes` list — they
  render as semantic-boundary groups via `semantic_source_id`. Keep `Package`
  in the top-level `nodes` array only.
- `Component` — `properties.uml.package` (owning package id).
- `Interface` — `properties.uml.operations` (array of
  `{name, visibility, parameters: [{name, type}], return_type}`).
- `Port` — `properties.uml`: `component` (owning component id), `provided`
  (array of interface ids), `required` (array of interface ids; omit if empty).
- `Class` — `properties.uml`: `attributes` (array of
  `{name, type, visibility, multiplicity}`), `operations` (array of
  `{name, visibility, parameters: [{name, type}], return_type}`).

Relationship types:

- `Realization` — a component realizes an interface; `properties.uml: {}`.
- `Usage` — a component uses a required interface; `properties.uml: {}`.
- `Dependency` — general dependency; `properties.uml: {}`.

## Worked Example

Synthetic `uml-component` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.06.0"}],
  "nodes": [
    {"id": "pkg-svc", "type": "Package", "label": "Services", "properties": {"uml": {"kind": "package"}}},
    {"id": "comp-loans", "type": "Component", "label": "Loans Service", "properties": {"uml": {"package": "pkg-svc"}}},
    {"id": "if-loans", "type": "Interface", "label": "LoansApi", "properties": {"uml": {"operations": [{"name": "borrow", "visibility": "public", "parameters": [{"name": "isbn", "type": "Isbn"}], "return_type": "Loan"}]}}},
    {"id": "if-catalog", "type": "Interface", "label": "CatalogApi", "properties": {"uml": {"operations": [{"name": "findByIsbn", "visibility": "public", "parameters": [{"name": "isbn", "type": "Isbn"}], "return_type": "CatalogEntry"}]}}},
    {"id": "port-loans", "type": "Port", "label": "api", "properties": {"uml": {"component": "comp-loans", "provided": ["if-loans"], "required": ["if-catalog"]}}},
    {"id": "cls-loan-ctrl", "type": "Class", "label": "LoanController", "properties": {"uml": {"attributes": [], "operations": [{"name": "submit", "visibility": "public", "parameters": [], "return_type": "Loan"}]}}}
  ],
  "relationships": [
    {"id": "r-provides", "type": "Realization", "source": "comp-loans", "target": "if-loans", "label": "provides", "properties": {"uml": {}}},
    {"id": "u-uses", "type": "Usage", "source": "comp-loans", "target": "if-catalog", "label": "uses", "properties": {"uml": {}}},
    {"id": "d-ctrl", "type": "Dependency", "source": "comp-loans", "target": "cls-loan-ctrl", "label": "uses", "properties": {"uml": {}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "loans-component-view", "label": "Loans Component View", "kind": "uml-component", "nodes": ["comp-loans", "port-loans", "if-loans", "if-catalog", "cls-loan-ctrl"], "relationships": ["r-provides", "u-uses", "d-ctrl"]}]}}
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
