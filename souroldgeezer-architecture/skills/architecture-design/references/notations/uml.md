# UML Notation

Load when a package uses `plugins.generic-graph.semantic_profile: "uml"`, any
UML view kind, UML/XMI export, or the user asks for UML design detail inside a
dediren architecture/design package.

UML elaborates one bounded part of an architecture concern for implementation
handoff. It is a modeling-notation layer: it documents how to model a concern in
a dediren package, not how to decide it. Delegate the underlying decisions to the
owning skill (see Delegation).

## Validation, Render, Export

A UML view is `source-valid` only with schema validation plus
`validate --plugin generic-graph --profile uml`. The render
(render-metadata → SVG) and `uml-xmi` export paths, and `properties.uml.*`
placement, are documented per kind — load the kind's file under `uml/`.

## Kind Index

Load the per-kind file under `uml/` only when that kind is in play.

| Kind | Concern | Load |
|---|---|---|
| `kind: "uml-class"` | class / interface / type structure | `uml/class.md` |
| `kind: "uml-data"` | data types and enumerations | `uml/data.md` |
| `kind: "uml-activity"` | control / object flow | `uml/activity.md` |
| `kind: "uml-sequence"` | one interaction over time | `uml/sequence.md` |
| `kind: "uml-state-machine"` | states and transitions of one element | `uml/state-machine.md` |
| `kind: "uml-use-case"` | actor goals and system scope | `uml/use-case.md` |
| `kind: "uml-component"` | implementation components and interfaces | `uml/component.md` |
| `kind: "uml-deployment"` | artifact-to-node deployment | `uml/deployment.md` |

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
- Verify referenced ArchiMate ids exist in the same package or cited evidence;
  broken links cap cross-notation readiness.
- Do not infer cross-notation links from matching labels alone; require source
  evidence or explicit architect/user intent.
- If UML detail contradicts linked ArchiMate intent, report a handoff
  inconsistency instead of silently letting UML override architecture.
