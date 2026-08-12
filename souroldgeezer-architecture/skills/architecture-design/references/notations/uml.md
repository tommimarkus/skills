# UML Notation

Load when a package uses `plugins.generic-graph.semantic_profile: "uml"`, any
UML view kind, UML/XMI export, or the user asks for UML design detail inside a
dediren architecture/design package.

UML elaborates one bounded part of an architecture concern for implementation
handoff. It is a modeling-notation layer: it documents how to model a concern in
a dediren package, not how to decide it. Delegate the underlying decisions to the
owning skill (see Delegation).

## Validation, Render, Export

Shared contract for every UML view kind; the per-kind files under `uml/` add
only their deltas to it.

- A UML view is `source-valid` only with schema validation plus
  `dediren_validate {workspaceRoot, profile: "uml"}`.
- The SVG render path needs generated render metadata, which `dediren_build`
  produces (mapped to `generated/render-metadata/<view>.json`).
- UML/XMI compatibility export (`uml-xmi`) runs only when requested. Per-view
  XMI covers advertised kinds according to actual diagnostics — class, data,
  activity, sequence, state-machine, use-case, component, and deployment — and
  its validation level must be disclosed as `XMI envelope only`,
  `UML-content schema`, or `importer validated`; envelope-only validation does
  not establish conformant UML abstract syntax. When an exported view holds content
  outside it, or in-view content the mapping cannot yet represent, the runtime
  declares it — never dropped silently — with `info` diagnostics
  `DEDIREN_XMI_ELEMENTS_OMITTED` / `DEDIREN_XMI_RELATIONSHIPS_OMITTED` (the
  message states which case) while the envelope `status` stays `ok`; read
  `.diagnostics[]` and qualify readiness from what they report per
  [external-validation-handoff](../procedures/external-validation-handoff.md).
- Beyond that per-view `uml-xmi` export, a build with an `xmi_policy` also emits
  one whole-model `model.uml.xml` interchange document (one `uml:Model` plus OMG
  UMLDI diagrams), complete across the built views. Its UMLDI diagram content is
  **provisional** — classifier-diagram views only (`uml-class` / `uml-data`),
  unverified against real UML importers — so keep the per-view `uml-xmi` export
  best-effort evidence (architecture.md §10).

`uml-data` is a Dediren-local classifier-structure view, not a UML Annex A
diagram kind. Local view-family names are package/runtime vocabulary; standard
UML diagram kinds remain a separate notation question.

`properties.uml.*` placement is documented per kind — load the kind's file
under `uml/`.

## Kind Index

Load the per-kind file under `uml/` only when that kind is in play.

| Kind | Concern | Load |
|---|---|---|
| `kind: "uml-class"` | class / interface / type structure | [`uml/class.md`](uml/class.md) |
| `kind: "uml-data"` | data types and enumerations | [`uml/data.md`](uml/data.md) |
| `kind: "uml-activity"` | control / object flow | [`uml/activity.md`](uml/activity.md) |
| `kind: "uml-sequence"` | one interaction over time | [`uml/sequence.md`](uml/sequence.md) |
| `kind: "uml-state-machine"` | states and transitions of one element | [`uml/state-machine.md`](uml/state-machine.md) |
| `kind: "uml-use-case"` | actor goals and system scope | [`uml/use-case.md`](uml/use-case.md) |
| `kind: "uml-component"` | implementation components and interfaces | [`uml/component.md`](uml/component.md) |
| `kind: "uml-deployment"` | artifact-to-node deployment | [`uml/deployment.md`](uml/deployment.md) |

## Delegation

UML models the artifact; the named skill owns the decision.

- `uml-class`, `uml-data` → `software-design` (code / module / type internals).
- `uml-component` → `software-design` plus ArchiMate Application Cooperation.
- `uml-deployment` → `infra-design` plus ArchiMate Technology Usage.
- `uml-activity` → business process / ArchiMate Business Process Cooperation.
- `uml-use-case` → motivation / requirements.
- `uml-sequence` → interaction handoff owned here; delegate code decisions to
  `software-design` and HTTP call contracts to `api-design`.

Also delegate UI behavior to `app-design`, security / CI / IaC risk to
`devsecops-audit`, and test design to `test-quality-audit`.

## ArchiMate vs UML Inside This Skill

Prefer ArchiMate Application Cooperation / Technology Usage for
architecture-level structure and hosting. Reach for `uml-component` /
`uml-deployment` only when implementation-level handoff detail (ports, artifacts,
deployment specs) is the point.

## Findings

Reuse the skill's `ARCH-*` namespaces for every UML kind: source invalidity →
`ARCH-M-*`; view readability → `ARCH-V-*` / `ARCH-L-*` / `ARCH-R-*`; export →
`ARCH-X-*` / `ARCH-E-*`; quality → `ARCH-Q-*`.

## ArchiMate Handoff Links

Dediren supports optional cross-notation context through
`properties.uml.architecture_context`. Treat these as package handoff evidence,
not mandatory two-way traceability and not a substitute for semantic validation.

```json
{
  "properties": {
    "uml": {
      "architecture_context": {
        "profile": "archimate",
        "element_id": "application-component-billing",
        "relationship": "elaborates"
      }
    }
  }
}
```

Contract:

- Default direction: UML elaborates ArchiMate; relationship: elaborates.
- Attach links to a UML package, view-level source record, or high-level UML
  element when it gives detailed design context for an ArchiMate element or view.
- Verify referenced ArchiMate ids exist in the package's ArchiMate model (the
  `archimate` entry in a `package.json` `models[]`; architecture.md §3
  mixed-notation packages) or cited evidence; broken links cap cross-notation
  readiness.
- Do not infer cross-notation links from matching labels alone; require source
  evidence or explicit architect/user intent.
- If UML detail contradicts linked ArchiMate intent, report a handoff
  inconsistency instead of silently letting UML override architecture.
