# Source Grounding — lean-audit

All `LA-*` codes, the smell catalog, the workflow, the fuzzy-waste procedure, and
every eval case are repo-authored. The deterministic detection lives in the
bundled engine `scripts/lean_engine.py` (stdlib-only; shingling and containment
are direct expressions of standard k-gram resemblance set math — Broder-style —
not lifted from any library or post). No third-party prose, fixtures, tables,
schemas, or code are copied into this skill.

- Lean / *muda* waste framing: a general manufacturing-quality concept, described
  in the auditor's own words, not quoted.
- Audit discipline and output contract: cited from
  `../../../docs/audit-reference/audit-craft.md` (§2/§3/§5), not restated.
- Engine behavioral evidence (precision/recall calibration, false-positive
  corpus) lives with the engine tests at repo-root `tests/lean_engine_test.py`
  and `tests/lean_engine_ledger.jsonl`.
