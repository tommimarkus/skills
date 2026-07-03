# UML Activity Views (`uml-activity`)

Concern: control and object flow for a procedure or behavior, as handoff detail.
Delegate business-process ownership to ArchiMate Business Process Cooperation in
this skill, and code-level control flow to `software-design`.

## Source Contract

Use `kind: "uml-activity"`. Source reference: `fixtures/source/valid-uml-complex.json`
in the selected Dediren release bundle (activity nodes and flows live there).

Node types:

- `Activity` — the behavior container; `properties.uml.partitions` (array of
  swimlane label strings).
- `Action` — a step; `properties.uml`: `activity` (the Activity id), `partition`
  (swimlane label).
- `InitialNode` / `ActivityFinalNode` / `DecisionNode` — start / end / branch;
  each carries `properties.uml`: `activity` (the Activity id) and `partition`
  (swimlane label).
- `ForkNode` / `JoinNode` — concurrency; `ObjectNode` — data passed between
  actions (also carry `activity`/`partition` when present).

Relationship types:

- `ControlFlow` — sequencing; optional `properties.uml.guard`.
- `ObjectFlow` — object passing between an action and an `ObjectNode`.

## Worked Example

Synthetic `uml-activity` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.0"}],
  "nodes": [
    {"id": "act-return", "type": "Activity", "label": "Return Book", "properties": {"uml": {"partitions": ["Desk", "Stacks"]}}},
    {"id": "start", "type": "InitialNode", "label": "start", "properties": {"uml": {"activity": "act-return", "partition": "Desk"}}},
    {"id": "scan", "type": "Action", "label": "Scan Book", "properties": {"uml": {"activity": "act-return", "partition": "Desk"}}},
    {"id": "shelve", "type": "Action", "label": "Shelve Book", "properties": {"uml": {"activity": "act-return", "partition": "Stacks"}}},
    {"id": "done", "type": "ActivityFinalNode", "label": "done", "properties": {"uml": {"activity": "act-return", "partition": "Stacks"}}}
  ],
  "relationships": [
    {"id": "f1", "type": "ControlFlow", "source": "start", "target": "scan", "label": "", "properties": {}},
    {"id": "f2", "type": "ControlFlow", "source": "scan", "target": "shelve", "label": "", "properties": {}},
    {"id": "f3", "type": "ControlFlow", "source": "shelve", "target": "done", "label": "", "properties": {}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "return-activity-view", "label": "Return Activity View", "kind": "uml-activity", "nodes": ["act-return", "start", "scan", "shelve", "done"], "relationships": ["f1", "f2", "f3"]}]}}
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
