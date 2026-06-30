# UML State Machine Views (`uml-state-machine`)

Concern: the states and transitions of one element's behavior, as handoff
detail. Delegate the behavior implementation to `software-design`.

## Source Contract

Use `kind: "uml-state-machine"`. Source reference:
`fixtures/source/valid-uml-state-machine-basic.json` in the selected Dediren
release bundle.

Node types:

- `StateMachine` — the behavior container; `properties.uml: {}`.
- `Region` — a region of the state machine; referenced by
  `properties.uml.region` on states and transitions.
  `properties.uml.state_machine` holds the owning `StateMachine` id.
- `State` — `properties.uml.region`.
- `Pseudostate` — `properties.uml`: `region`, `kind` (e.g. `initial`,
  `choice`).
- `FinalState` — terminal state; `properties.uml.region`.

Relationship types:

- `Transition` — `properties.uml`: `region`, `kind` (e.g. `external`),
  `trigger` (event), optional `guard` (condition).

`StateMachine` and `Region` nodes are structural containers — include them in
the model's `nodes` array but **not** in a view's `nodes` list. Only
`Pseudostate`, `State`, and `FinalState` appear in view nodes; `StateMachine`
and `Region` appear as `groups` with `role: "semantic-boundary"` and
`semantic_source_id` referencing their model ids.

## Worked Example

Synthetic `uml-state-machine` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.06.9"}],
  "nodes": [
    {"id": "sm-loan", "type": "StateMachine", "label": "Loan", "properties": {"uml": {}}},
    {"id": "r-main", "type": "Region", "label": "main", "properties": {"uml": {"state_machine": "sm-loan"}}},
    {"id": "init", "type": "Pseudostate", "label": "init", "properties": {"uml": {"region": "r-main", "kind": "initial"}}},
    {"id": "open", "type": "State", "label": "Open", "properties": {"uml": {"region": "r-main"}}},
    {"id": "returned", "type": "FinalState", "label": "Returned", "properties": {"uml": {"region": "r-main"}}}
  ],
  "relationships": [
    {"id": "t-borrow", "type": "Transition", "source": "init", "target": "open", "label": "borrow", "properties": {"uml": {"region": "r-main", "kind": "external", "trigger": "borrow"}}},
    {"id": "t-return", "type": "Transition", "source": "open", "target": "returned", "label": "return", "properties": {"uml": {"region": "r-main", "kind": "external", "trigger": "return", "guard": "notOverdue"}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "loan-state-view", "label": "Loan State View", "kind": "uml-state-machine", "nodes": ["init", "open", "returned"], "relationships": ["t-borrow", "t-return"]}]}}
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
