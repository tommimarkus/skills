# UML Deployment Views (`uml-deployment`)

Concern: artifact-to-node deployment for handoff. Delegate topology and hosting
decisions to `infra-design` plus ArchiMate Technology Usage (prefer ArchiMate /
infra-design for architecture-level hosting).

## Source Contract

Use `kind: "uml-deployment"`. Source reference:
`fixtures/source/valid-uml-deployment-basic.json` in the selected Dediren
release bundle.

Node types:

- `Device` — a physical or virtual host; `properties.uml.kind: "device"`.
- `ExecutionEnvironment` — a runtime container on a device;
  `properties.uml.node` (owning device/node id).
- `Node` — a generic runtime node; `properties.uml: {}`.
- `Artifact` — a deployable unit (e.g. JAR, image); `properties.uml: {}`.
- `DeploymentSpecification` — deployment configuration (e.g. YAML);
  `properties.uml: {}`.
- `Component` — the logical component an artifact manifests;
  `properties.uml: {}`.

Relationship types:

- `Deployment` — an artifact (or spec) is deployed onto a node/environment;
  `properties.uml: {}`.
- `Manifestation` — an artifact manifests a component; `properties.uml: {}`.
- `CommunicationPath` — a link between nodes/environments;
  `properties.uml: {}`.

`properties.uml.node` records ownership but does not nest the rendered boxes:
a view listing an owning `Device`/`Node` and its `ExecutionEnvironment` as
plain view nodes renders them as disjoint peers. Make ownership visible the
way `uml-state-machine` shows containers: model each owning deployment target
as a view group with `role: "semantic-boundary"` and `semantic_source_id`
referencing its model id, list the owned environments plus the artifacts and
specifications deployed onto them as `members`, and leave the owning node out
of the view's `nodes` list. Keep it in `nodes` only when a view relationship
(e.g. a `CommunicationPath`) attaches to it directly — a group-only endpoint
fails validation with
`DEDIREN_GENERIC_GRAPH_RELATIONSHIP_ENDPOINT_OUTSIDE_VIEW` — and disclose in
the output footer that it then also renders as a separate box outside its own
boundary.

## Worked Example

Synthetic `uml-deployment` source (lending domain):

```json
{
  "model_schema_version": "model.schema.v1",
  "required_plugins": [{"id": "generic-graph", "version": "2026.07.29"}],
  "nodes": [
    {"id": "node-app", "type": "Device", "label": "App Host", "properties": {"uml": {"kind": "device"}}},
    {"id": "env-jvm", "type": "ExecutionEnvironment", "label": "JVM", "properties": {"uml": {"node": "node-app"}}},
    {"id": "art-loans", "type": "Artifact", "label": "loans.jar", "properties": {"uml": {}}},
    {"id": "spec-loans", "type": "DeploymentSpecification", "label": "loans-deploy.yaml", "properties": {"uml": {}}},
    {"id": "comp-loans", "type": "Component", "label": "Loans Service", "properties": {"uml": {}}},
    {"id": "node-db", "type": "Node", "label": "DB Host", "properties": {"uml": {}}}
  ],
  "relationships": [
    {"id": "dep-loans", "type": "Deployment", "source": "art-loans", "target": "env-jvm", "label": "deploys", "properties": {"uml": {}}},
    {"id": "dep-spec", "type": "Deployment", "source": "spec-loans", "target": "env-jvm", "label": "applies", "properties": {"uml": {}}},
    {"id": "man-loans", "type": "Manifestation", "source": "art-loans", "target": "comp-loans", "label": "manifests", "properties": {"uml": {}}},
    {"id": "cp-app-db", "type": "CommunicationPath", "source": "env-jvm", "target": "node-db", "label": "jdbc", "properties": {"uml": {}}}
  ],
  "plugins": {"generic-graph": {"semantic_profile": "uml", "views": [{"id": "loans-deployment-view", "label": "Loans Deployment View", "kind": "uml-deployment", "nodes": ["env-jvm", "art-loans", "spec-loans", "comp-loans", "node-db"], "relationships": ["dep-loans", "dep-spec", "man-loans", "cp-app-db"], "groups": [{"id": "grp-node-app", "label": "App Host", "role": "semantic-boundary", "semantic_source_id": "node-app", "members": ["env-jvm", "art-loans", "spec-loans"]}]}]}}
}
```

## Validation, Render, Export

Shared UML contract — validation, render metadata, on-request XMI export:
[uml.md §"Validation, Render, Export"](../uml.md#validation-render-export).
No `uml-deployment`-specific deltas: the `uml-xmi` export emits the full
deployment abstract syntax above (the node and relationship types this file
lists) with no `DEDIREN_XMI_*_OMITTED` diagnostic. Verified on the pinned bundle
by `test_release_uml_deployment_worked_example_xmi_full_pipeline`, which exports
this file's own Worked Example.

## Findings

Reuse `ARCH-*` namespaces (see the hub).
