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
  optional `trigger` (event), optional `guard` (condition). The outgoing
  transition of an `initial` Pseudostate carries no `trigger` and no `guard`
  (UML 2.5.1); model events as triggers on State-to-State transitions. The
  `uml` profile validator does not flag violations (verified on dediren
  2026.07.1), so `source-valid` alone does not prove this rule holds — apply
  it when authoring.

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
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.6"}],
  "nodes": [
    {"id": "sm-loan", "type": "StateMachine", "label": "Loan", "properties": {"uml": {}}},
    {"id": "r-main", "type": "Region", "label": "main", "properties": {"uml": {"state_machine": "sm-loan"}}},
    {"id": "init", "type": "Pseudostate", "label": "init", "properties": {"uml": {"region": "r-main", "kind": "initial"}}},
    {"id": "available", "type": "State", "label": "Available", "properties": {"uml": {"region": "r-main"}}},
    {"id": "open", "type": "State", "label": "Open", "properties": {"uml": {"region": "r-main"}}},
    {"id": "returned", "type": "FinalState", "label": "Returned", "properties": {"uml": {"region": "r-main"}}}
  ],
  "relationships": [
    {"id": "t-init", "type": "Transition", "source": "init", "target": "available", "label": "", "properties": {"uml": {"region": "r-main", "kind": "external"}}},
    {"id": "t-borrow", "type": "Transition", "source": "available", "target": "open", "label": "borrow", "properties": {"uml": {"region": "r-main", "kind": "external", "trigger": "borrow"}}},
    {"id": "t-return", "type": "Transition", "source": "open", "target": "returned", "label": "return", "properties": {"uml": {"region": "r-main", "kind": "external", "trigger": "return", "guard": "notOverdue"}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "loan-state-view", "label": "Loan State View", "kind": "uml-state-machine", "nodes": ["init", "available", "open", "returned"], "relationships": ["t-init", "t-borrow", "t-return"]}]}}
}
```

## Validation, Render, Export

Shared UML contract — validation, render metadata, on-request XMI export:
[uml.md §"Validation, Render, Export"](../uml.md#validation-render-export).
No `uml-state-machine`-specific deltas.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
