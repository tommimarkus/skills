# Lean Audit Smell Catalog

Compact core-waste code index for `lean-audit`. The bundled engine
(`scripts/lean_engine.py`) emits the deterministic codes; the
`procedures/fuzzy-waste.md` layer adds the inference-only codes. Severity rates
the control weakness; risk tier (`../../../docs/audit-reference/materiality.md`)
is the orthogonal subject axis. Conditional lenses define their codes in their
own procedures so ordinary audits do not load rare-mode taxonomy. Cite codes in
output; do not restate this catalog.

## Duplication — Lean: inventory / over-processing
- `LA-DUP-1` — cross-file near-duplicate prose (shingle containment ≥ high band).
  Severity: block (high band) / info (advisory mid band). Source: engine.
- `LA-DUP-2` — content restated instead of citing its declared canonical home.
  Severity: block. Source: engine (registry-aware).

## Code duplication — Lean: inventory / over-processing (source surfaces)
- `LA-CODE-DUP-1` — mechanical copy-paste clone in source code at or above the
  block band (token-window match ≥ 2× min-tokens; comments and string/number
  literals normalized; windows without minimum identifier diversity are skipped
  as declarative data). Severity: block. Source: engine (`code_lens.py`).
- `LA-CODE-DUP-2` — a shorter source clone in the advisory band
  (min-tokens ≤ length < 2× min-tokens). Severity: info. Source: engine
  (`code_lens.py`).

Declaring a `LA-CODE-DUP-*` clone intentional takes a **line comment** of the
file's own language (`#`, `//`) — the marker in a string literal is not a
declaration. Two scopes:
- `lean-audit:dup-intentional — <rationale>` anywhere in a file exempts the
  **whole file** (its every clone, present and future);
- `lean-audit:dup-intentional:begin` … `lean-audit:dup-intentional:end` exempts
  only the clones **fully contained** in that span — the scope to use on a logic
  module, where a whole-file marker would blanket unrelated code.

Either side of a clone pair may carry the declaration. A clone that only
partly overlaps a region is still reported; nesting is depth-counted (an inner
pair does not close the outer region); an unclosed `:begin` runs to end of file.

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

## Verbosity — Lean: over-processing (intra-passage)
- `LA-VERBOSE-1` — statistical verbosity candidate: a section at or above the
  token floor tripping ≥ 2 deterministic wordiness signals (filler / hedge
  density, meta-discourse scaffolding, intra-section repetition). A NOMINATION,
  not a verdict — confirm or clear via `procedures/fuzzy-waste.md` before acting.
  Frontmatter and code fences are excluded; path exemptions and a
  `<!-- lean-audit:verbose-intentional: … -->` marker suppress; the `[verbosity]`
  table in `.lean-audit.toml` tunes the thresholds or disables the lens. The
  composite ≥ 2-signal gate is the precision mechanism (a single signal — e.g. a
  naturally repetitive anchor list — never nominates). The filler / scaffold
  signals are English-only; the repetition signal is language-neutral (a disclosed
  evidence limit). Severity: info. Source: engine.
- `LA-VERBOSE-2` — confirmed wasteful verbosity: a nominated (or explicitly
  user-named) passage judgment confirms is faithfully reducible — materially
  fewer tokens with every obligation, qualifier, threshold, negation, and
  enumerated item preserved, and the wordiness not load-bearing (pedagogy,
  calibrated hedging, normative precision). Severity: warn. Source: inference
  (`procedures/fuzzy-waste.md`); mark as requiring verification. Consumed by the
  minify `tighten` class (opt-in, propose-only) on non-normative prose only —
  normative regions (MUST-rules, stop conditions, output contracts) are
  hard-banned from tighten in v1 (`gate-unavailable`), where it stays
  detection-only.

Note: always-loaded `SKILL.md`-body bloat is covered by `LA-BLOAT`; not
duplicated here.

Out of v1 scope: source-level *dead code* (tracked for v1.1); semantic code
duplication / DRY ownership (owned by `software-design`, `SD-S-2`); the rest of
the Lean waste taxonomy (waiting, transport, motion, over-production beyond the
above). Mechanical source *duplication* is now in scope via `LA-CODE-DUP-*`.
Intra-passage over-processing (wordy but unique prose) is in scope via
`LA-VERBOSE-*` (deterministic nomination + judgment confirmation).
