# UML Sequence Views (`uml-sequence`)

Concern: one interaction (message exchange over time) between participants, as
implementation handoff detail inside a dediren package. Delegate the underlying
control-flow and code decisions to `software-design`, and HTTP call contracts to
`api-design`.

## Source Contract

Use `kind: "uml-sequence"`. Source references in the selected Dediren release
bundle: `fixtures/source/valid-uml-sequence-basic.json` (minimum) and
`fixtures/source/valid-uml-sequence-fragments.json` (with combined fragments).

Node types:

- `Interaction` — the interaction container; referenced by
  `properties.uml.interaction` on participants and messages.
- `Lifeline` — a participant; `properties.uml.interaction`.
- `CombinedFragment` — a structured region; `properties.uml`: `interaction`,
  `operator` (e.g. `alt`, `opt`, `loop`, `par`), `operands` (operand ids),
  `covered` (lifeline ids in scope).
- `InteractionOperand` — one branch of a fragment; `properties.uml`:
  `interaction`, `combined_fragment` (parent fragment id), `order` (operand
  order), `guard` (branch condition), `fragments` (message ids in the operand).

Relationship types:

- `Message` — `properties.uml`: `interaction`, `sequence` (integer order),
  `message_sort` (e.g. `synchCall`, `asynchCall`, `reply`).

Put message order in `properties.uml.sequence` and message category in
`message_sort`. Model alternatives/options/loops with a `CombinedFragment` plus
its `InteractionOperand` branches; place each branch's messages in the operand's
`fragments` list and the branch condition in the operand's `guard`.

## Worked Example

Synthetic `uml-sequence` source with an `alt` fragment (auth domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.17"}],
  "nodes": [
    {"id": "ix-login", "type": "Interaction", "label": "Login", "properties": {"uml": {}}},
    {"id": "user", "type": "Lifeline", "label": "User", "properties": {"uml": {"interaction": "ix-login"}}},
    {"id": "auth", "type": "Lifeline", "label": "Auth Service", "properties": {"uml": {"interaction": "ix-login"}}},
    {"id": "cf-result", "type": "CombinedFragment", "label": "result", "properties": {"uml": {"interaction": "ix-login", "operator": "alt", "operands": ["op-ok", "op-deny"], "covered": ["user", "auth"]}}},
    {"id": "op-ok", "type": "InteractionOperand", "label": "valid", "properties": {"uml": {"interaction": "ix-login", "combined_fragment": "cf-result", "order": 1, "guard": "valid", "fragments": ["m-grant"]}}},
    {"id": "op-deny", "type": "InteractionOperand", "label": "invalid", "properties": {"uml": {"interaction": "ix-login", "combined_fragment": "cf-result", "order": 2, "guard": "invalid", "fragments": ["m-deny"]}}}
  ],
  "relationships": [
    {"id": "m-login", "type": "Message", "source": "user", "target": "auth", "label": "login", "properties": {"uml": {"interaction": "ix-login", "sequence": 1, "message_sort": "synchCall"}}},
    {"id": "m-grant", "type": "Message", "source": "auth", "target": "user", "label": "token", "properties": {"uml": {"interaction": "ix-login", "sequence": 2, "message_sort": "reply"}}},
    {"id": "m-deny", "type": "Message", "source": "auth", "target": "user", "label": "denied", "properties": {"uml": {"interaction": "ix-login", "sequence": 3, "message_sort": "reply"}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "login-sequence-view", "label": "Login Sequence View", "kind": "uml-sequence", "nodes": ["ix-login", "user", "auth", "cf-result", "op-ok", "op-deny"], "relationships": ["m-login", "m-grant", "m-deny"]}]}}
}
```

## Validation, Render, Export

Shared contract: [uml.md §"Validation, Render, Export"](../uml.md#validation-render-export).
XMI-omitted here: interactions, lifelines, messages; keep sequence handoff to
the rendered SVG.

- SVG inspection (render-ready): confirm each `Lifeline` renders as its own
  column — a distinct head box and vertical stem — and that every `Message`
  spans the horizontal gap between its two lifelines. Two lifelines sharing a
  head position or stem, or a message drawn as a stub inside a merged box, is an
  `ARCH-R-*` defect; inspect the SVG structure independently, and cross-check the
  `validate-layout` verdict (envelope `status: warning` on dediren 2026.07.1+,
  and the `data.status` / `overlap_count` payload on any runtime) per
  [self-check](../../procedures/self-check.md) "Envelope handling".

## Findings

Reuse `ARCH-*` namespaces (see the hub).
