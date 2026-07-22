# Software Architecture Pairing

Load when a paired ArchiMate dediren package exists or the user asks to update
architecture after module/boundary work.

The shared pairing mechanics — package detection, Review drift dispatch,
Extract/Build opt-in, the no-direct-ArchiMate-edits rule, and the footer-field
vocabulary — are canonical in
[`../../../../docs/design-reference/architecture-pairing-core.md`](../../../../docs/design-reference/architecture-pairing-core.md).
Apply them with this skill's narrowing and mappings below.

## Software Mapping

- Narrow the Review drift dispatch to changes that restructure modules,
  boundaries, or dependency direction that a code-lifted view may reflect.
- Modules, packages, and libraries become Application Components. Owned public
  module APIs become Application Interfaces. Dependency direction may
  contribute serving relationships only when source evidence supports it.
