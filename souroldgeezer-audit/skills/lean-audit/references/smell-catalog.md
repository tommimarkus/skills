# Lean Audit Smell Catalog

Compact `LA-*` code index for `lean-audit`. The bundled engine
(`scripts/lean_engine.py`) emits the deterministic codes; the
`procedures/fuzzy-waste.md` layer adds the inference-only codes. Severity rates
the control weakness; risk tier (`../../../docs/audit-reference/materiality.md`)
is the orthogonal subject axis. Cite codes in output; do not restate this catalog.

## Duplication — Lean: inventory / over-processing
- `LA-DUP-1` — cross-file near-duplicate prose (shingle containment ≥ high band).
  Severity: block (high band) / info (advisory mid band). Source: engine.
- `LA-DUP-2` — content restated instead of citing its declared canonical home.
  Severity: block. Source: engine (registry-aware).

## Staleness — Lean: defects
- `LA-STALE-1` — broken reference: a link whose file target or `#anchor` does not
  resolve. Severity: warn. Source: engine.
- `LA-STALE-2` — prose describes a section / file / layout that no longer exists
  or was renamed. Severity: warn. Source: inference (`procedures/fuzzy-waste.md`);
  mark as requiring verification.

## Dead weight — Lean: overproduction
- `LA-DEAD-1` — a `references/` or `extensions/` file no other guarded file
  mentions. Severity: info. Source: engine.

## Context bloat — Lean: over-processing
- `LA-BLOAT-1` — `SKILL.md` body exceeds the line budget (frontmatter excluded).
  Severity: warn. Source: engine.
- `LA-BLOAT-2` — heavy reference material (rubric / table / taxonomy) inlined in
  always-loaded context that belongs behind a load condition. Severity: warn.
  Source: inference (`procedures/fuzzy-waste.md`).

Out of v1 scope: code (non-prose) duplication; the rest of the Lean waste
taxonomy (waiting, transport, motion, over-production beyond the above).
