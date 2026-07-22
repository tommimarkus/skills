# API Architecture Pairing

Load when a paired ArchiMate dediren package exists or the user asks to update
architecture after API work.

The shared pairing mechanics — package detection, Review drift dispatch,
Extract/Build opt-in, the no-direct-ArchiMate-edits rule, and the footer-field
vocabulary — are canonical in
[`../../../../docs/design-reference/architecture-pairing-core.md`](../../../../docs/design-reference/architecture-pairing-core.md).
Apply them with this skill's mappings below.

## API Mapping

- API runtime projects become Application Components. Routes become Application
  Interfaces. Runtime/data/storage extensions may contribute Technology Layer
  relationships only when source evidence supports them.
