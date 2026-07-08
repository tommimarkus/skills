# UML Use Case Views (`uml-use-case`)

Concern: actor goals and system scope for handoff. Delegate requirements and
motivation ownership to ArchiMate Motivation / requirements work.

## Source Contract

Use `kind: "uml-use-case"`. Source reference:
`fixtures/source/valid-uml-use-case-basic.json` in the selected Dediren
release bundle.

Node types:

- `Actor` — an external role; `properties.uml: {}`.
- `UseCase` — `properties.uml.subject` (the owning system/subject id).
- `ExtensionPoint` — a named point a `UseCase` can be extended at;
  `properties.uml.use_case` holds the owning `UseCase` id.
- `Class` — used as the subject/system boundary element;
  `properties.uml.use_case_subject: true`. Include in the model's `nodes`
  array but **not** in a view's `nodes` list — it appears as a `group` with
  `role: "semantic-boundary"` and `semantic_source_id`.

Relationship types:

- `Association` — actor participates in a use case; `properties.uml: {}`.
- `Include` — a use case always includes another; `properties.uml: {}`.
- `Extend` — a use case conditionally extends another;
  `properties.uml.extension_point` holds the `ExtensionPoint` id.

## Worked Example

Synthetic `uml-use-case` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.13"}],
  "nodes": [
    {"id": "system-lms", "type": "Class", "label": "Library System", "properties": {"uml": {"use_case_subject": true}}},
    {"id": "member", "type": "Actor", "label": "Member", "properties": {"uml": {}}},
    {"id": "uc-borrow", "type": "UseCase", "label": "Borrow Book", "properties": {"uml": {"subject": "system-lms"}}},
    {"id": "uc-notify", "type": "UseCase", "label": "Notify Overdue", "properties": {"uml": {"subject": "system-lms"}}},
    {"id": "uc-verify", "type": "UseCase", "label": "Verify Membership", "properties": {"uml": {"subject": "system-lms"}}},
    {"id": "ep-overdue", "type": "ExtensionPoint", "label": "overdue", "properties": {"uml": {"use_case": "uc-borrow"}}}
  ],
  "relationships": [
    {"id": "a-member-borrow", "type": "Association", "source": "member", "target": "uc-borrow", "label": "", "properties": {"uml": {}}},
    {"id": "inc-verify", "type": "Include", "source": "uc-borrow", "target": "uc-verify", "label": "includes", "properties": {"uml": {}}},
    {"id": "x-notify", "type": "Extend", "source": "uc-notify", "target": "uc-borrow", "label": "extends", "properties": {"uml": {"extension_point": "ep-overdue"}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "lending-usecase-view", "label": "Lending Use Case View", "kind": "uml-use-case", "nodes": ["member", "uc-borrow", "uc-verify", "uc-notify", "ep-overdue"], "relationships": ["a-member-borrow", "inc-verify", "x-notify"]}]}}
}
```

## Validation, Render, Export

Shared UML contract — validation, render metadata, on-request XMI export:
[uml.md §"Validation, Render, Export"](../uml.md#validation-render-export).
No `uml-use-case`-specific deltas.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
