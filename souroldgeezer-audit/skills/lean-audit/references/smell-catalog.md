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

## Code duplication — Lean: inventory / over-processing (source surfaces)
- `LA-CODE-DUP-1` — mechanical copy-paste clone in source code at or above the
  block band (token-window match ≥ 2× min-tokens; comments and string/number
  literals normalized). Severity: block. Source: engine (`code_lens.py`).
- `LA-CODE-DUP-2` — a shorter source clone in the advisory band
  (min-tokens ≤ length < 2× min-tokens). Severity: info. Source: engine
  (`code_lens.py`).

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

## Platform redundancy — Lean: over-production (reinventing the platform)
- `LA-NAT-1` — a custom artifact (hook/script, guidance-prose instruction,
  skill/command/agent, or MCP server) reproduces a capability Claude Code now
  provides natively, confirmed by a cited live `claude-code-guide` check.
  Confidence field: `HIGH` (drop-in native equivalent) or `MEDIUM` (native covers
  the core with caveats / required config). Severity: info (advisory).
  Source: inference + live agent verification (`procedures/platform-redundancy.md`).
  Opt-in lens only.
- `LA-NAT-2` — a reinvention candidate the pattern catalog raised that the live
  check could NOT confirm as native (uncertain, no citation, or the live check was
  unavailable). Confidence: `LOW`. Surfaced as a review item, never as confirmed
  redundancy. Severity: info. Source: inference (`procedures/platform-redundancy.md`).
  Opt-in lens only.

## Per-use cost — Lean: over-processing
- `LA-PUC-1` — a mode loads a closure file it does not need (mode-exclusive
  elsewhere, or detection-loaded regardless of mode); fix: Load-Map mode-gating
  (structural-safe). Severity: warn. Source: inference
  (`procedures/per-use-cost.md`).
- `LA-PUC-2` — a multi-mode/always-loaded closure file carries content exclusive
  to one rarer mode; split it out (structural-safe on a clean header boundary;
  needs-adversarial-review if prose moves under a shared header). Severity: warn.
  Source: inference (`procedures/per-use-cost.md`).
- `LA-PUC-3` — a single-file extension/reference loaded whole when each mode
  needs only a slice; partition into core + per-mode slices
  (needs-adversarial-review — cross-references). Severity: warn. Source:
  inference (`procedures/per-use-cost.md`).

Note: always-loaded `SKILL.md`-body bloat is covered by `LA-BLOAT`; not
duplicated here.

Out of v1 scope: source-level *dead code* (tracked for v1.1); *semantic* code
duplication / DRY ownership (owned by `software-design`, `SD-S-2`); the rest of
the Lean waste taxonomy (waiting, transport, motion, over-production beyond the
above). Mechanical source *duplication* is now in scope via `LA-CODE-DUP-*`.

Platform-redundancy (`LA-NAT-*`) is an opt-in lens: it is silent unless the request
explicitly asks whether custom artifacts reinvent a native Claude Code capability.
