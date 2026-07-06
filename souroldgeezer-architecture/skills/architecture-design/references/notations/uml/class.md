# UML Class Views (`uml-class`)

Concern: package, class, interface, and type structure for implementation
handoff. Delegate exact code internals (method bodies, language idioms) to
`software-design`.

## Source Contract

Use `kind: "uml-class"`. Source reference: `fixtures/source/valid-uml-complex.json`
in the selected Dediren release bundle.

Node types:

- `Package` — namespace grouping; referenced by `properties.uml.package` on members.
- `Class` — `properties.uml`: `package` (package id), `attributes` (array of
  `{name, type, visibility, multiplicity}`), `operations` (array of
  `{name, visibility, parameters: [{name, type}], return_type}`).
- `Interface` — same `operations` shape as `Class`; MAY also carry
  `properties.uml.package`; no stored state.
- `DataType` — value type; `attributes` shape as `Class`.
- `Enumeration` — `properties.uml.literals` (array of strings).

Relationship types (carry roles/multiplicity under `properties.uml`):

- `Association` / `Aggregation` / `Composition` — `{source_role, target_role,
  source_multiplicity, target_multiplicity}`.
- `Dependency` — uses/needs link; no required `properties.uml`.
- `Realization` — a `Class` realizes an `Interface`.

## Worked Example

Synthetic `uml-class` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.4"}],
  "nodes": [
    {"id": "pkg-lending", "type": "Package", "label": "Lending", "properties": {}},
    {"id": "class-member", "type": "Class", "label": "Member", "properties": {"uml": {"package": "pkg-lending", "attributes": [{"name": "id", "type": "MemberId", "visibility": "public", "multiplicity": "1"}], "operations": [{"name": "borrow", "visibility": "public", "parameters": [{"name": "book", "type": "Book"}], "return_type": "Loan"}]}}},
    {"id": "class-book", "type": "Class", "label": "Book", "properties": {"uml": {"package": "pkg-lending", "attributes": [{"name": "isbn", "type": "Isbn", "visibility": "public", "multiplicity": "1"}]}}},
    {"id": "iface-catalog", "type": "Interface", "label": "Catalog", "properties": {"uml": {"operations": [{"name": "find", "visibility": "public", "parameters": [{"name": "isbn", "type": "Isbn"}], "return_type": "Book"}]}}}
  ],
  "relationships": [
    {"id": "member-borrows-book", "type": "Association", "source": "class-member", "target": "class-book", "label": "borrows", "properties": {"uml": {"source_role": "borrower", "target_role": "onLoan", "source_multiplicity": "0..1", "target_multiplicity": "0..*"}}},
    {"id": "book-realizes-catalog", "type": "Realization", "source": "class-book", "target": "iface-catalog", "label": "via", "properties": {}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "lending-class-view", "label": "Lending Class View", "kind": "uml-class", "nodes": ["pkg-lending", "class-member", "class-book", "iface-catalog"], "relationships": ["member-borrows-book", "book-realizes-catalog"]}]}}
}
```

## Validation, Render, Export

Shared UML contract — validation, render metadata, on-request XMI export:
[uml.md §"Validation, Render, Export"](../uml.md#validation-render-export).
No `uml-class`-specific deltas.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
