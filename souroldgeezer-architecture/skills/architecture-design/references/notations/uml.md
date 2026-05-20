# UML Notation

Load when a package uses `plugins.generic-graph.semantic_profile: "uml"`, view
kinds `uml-class`, `uml-data`, or `uml-activity`, UML/XMI export, or the user
asks for UML design detail inside a dediren architecture/design package.

UML elaborates one bounded part of an architecture concern for implementation
handoff. It owns package, class, interface, data type, enumeration, and activity
detail when those facts are part of the dediren package. Delegate exact code
internals to `software-design`, HTTP contracts to `api-design`, UI behavior to
`app-design`, infrastructure topology to `infra-design`, security/CI/IaC risk
to `devsecops-audit`, and test design to `test-quality-audit`.

## Validation

- `source-valid` requires schema validation plus
  `validate --plugin generic-graph --profile uml`.
- Use `kind: "uml-class"`, `kind: "uml-data"`, or `kind: "uml-activity"` on
  UML views.
- Put UML-specific attributes, operations, multiplicities, guards, partitions,
  and package membership under `properties.uml`.
- Use `fixtures/source/valid-uml-complex.json` in the bundled Dediren guide as
  the current non-trivial source reference; recheck the live bundle before
  claiming full UML 2.5.1 coverage.
- UML/XMI compatibility export uses `uml-xmi` only when requested.

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
  element when it gives detailed design context for an ArchiMate element or
  view.
- Verify referenced ArchiMate ids exist in the same package or cited evidence;
  broken links cap cross-notation readiness.
- Do not infer cross-notation links from matching labels alone; require source
  evidence or explicit architect/user intent.
- If UML detail contradicts linked ArchiMate intent, report a handoff
  inconsistency instead of silently letting UML override architecture.
