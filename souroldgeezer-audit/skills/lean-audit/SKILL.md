---
name: lean-audit
description: >-
  Use when auditing a repo, file, or diff for duplication and waste — near-duplicate or restated prose across docs and skills, broken or stale references, dead or unreferenced files, and oversized always-loaded context. Read-only; defer security, test-quality, and IP/licence work to sibling skills.
---

# Lean Audit

Audit prose and skill surfaces for duplication and waste (Lean *muda*). A bundled
deterministic engine computes the findings; this workflow runs it, ranks by
materiality, and adds the judgment-only waste checks the engine cannot decide.
Cite `references/smell-catalog.md` codes (`LA-*`). Conform to
`../../docs/audit-reference/audit-craft.md` §2/§3/§4/§5.

## Contract

Own read-only duplication/waste audits of markdown prose and skill surfaces
(governance docs, `SKILL.md`, agents, `docs/*-reference/**`, `references/**`,
`extensions/**`). Delegate: security → `devsecops-audit`; test quality →
`test-quality-audit`; copyright / marks / licence → `ip-hygiene`; code or design
structure → the design skills. Prose surfaces only in v1 (not code duplication).

Inputs: a scope (the whole repo, a file, a set of named files, or a diff) and an optional `.lean-audit.toml` canonical-home / carve-out registry. Ask or stop when the scope, the intended
surface, or requested edits lack a safe default. For false-positive discipline,
fact-vs-inference, and severity, see `../../docs/audit-reference/audit-craft.md`
§2–§3.

## One adaptive path (no mode dispatch)

This skill has no Quick/Deep modes — its detection is deterministic, so it runs
one path and DERIVES the assurance level from coverage: a file or diff scope →
`limited`; a full-repo enumeration → `reasonable`. State the assurance on one
line (audit-craft §4, by named principle — as `ip-hygiene` does).

## Load Map

- Load `../../docs/audit-reference/audit-craft.md` (discipline + output contract).
- Load `../../docs/audit-reference/materiality.md` (risk tier).
- Load `../../docs/audit-reference/sampling-projection.md` only at repo scale when
  full enumeration exceeds budget.
- Load `references/procedures/fuzzy-waste.md` for the judgment-only `LA-STALE-2`
  and `LA-BLOAT-2` checks (the engine does not emit these).
- Run the bundled engine `references/scripts/lean_engine.py` (the deterministic source of `LA-DUP-*` / `LA-STALE-1` / `LA-DEAD-1` / `LA-BLOAT-1`) per Workflow step 2.
- For the opt-in prevention hook, see `references/hook-recipe.md` (enablement) and the guard `references/scripts/lean_guard.py` (not part of an audit run).
- Cite codes from `references/smell-catalog.md`; never restate catalog prose.

## Workflow

1. Establish the scope: the whole repo, a single file, a set of named files, or a diff (its changed files). The bundled engine has no single-file or diff mode — it always scans the markdown tree rooted at a DIRECTORY — so pick the directory to run it in and the in-scope path set to keep. If a `.lean-audit.toml` exists at the scanned root the engine reads it; otherwise it runs heuristic-only — disclose which.
2. Run the bundled engine and parse its JSON. Use the portable absolute path: `python3 "$CLAUDE_PLUGIN_ROOT/skills/lean-audit/references/scripts/lean_engine.py" <dir> --format json` — `<dir>` is the repo root for a repo scope, or the nearest common directory of the in-scope files for a file / named-files / diff scope. The engine scans the whole markdown tree under `<dir>` and emits `LA-DUP-1`/`LA-DUP-2` (block or advisory), `LA-STALE-1`, `LA-DEAD-1`, `LA-BLOAT-1`; exit 1 = a block-severity duplication is present, exit 2 = engine error (report the limit, continue with the judgment-only checks). For a file / named-files / diff scope, KEEP ONLY findings whose `path` is in scope — the engine reports the whole tree, so this filter is what makes the scope real. Treat the output as evidence, not verdict: do not invent findings it did not produce, and do not suppress one without a cited reason.
3. Add the judgment-only checks from `references/procedures/fuzzy-waste.md` —
   `LA-STALE-2` (prose describing a removed/renamed structure) and `LA-BLOAT-2`
   (heavy reference material inlined in always-loaded context). Mark these
   inference (audit-craft §2), not confirmed fact.
4. Assign each finding a risk tier per `materiality.md` (a smell on a high-fan-in
   surface such as CLAUDE.md outranks the same smell on a leaf file). Combine
   severity × risk into the P0–P3 worklist (audit-craft §3 grid).
5. Report against what was actually examined. Derive assurance from the in-scope coverage: a file / named-files / diff scope → `limited`; a full-repo enumeration → `reasonable`. A file/diff scope emits per-finding output; a repo scope adds a sectioned rollup by `LA-*` band and a remediation worklist. For each duplication, cite the matched code and the canonical target.

## Rules and Stop Conditions

- Read-only: assess and produce a worklist; do not auto-fix unless edits are
  explicitly requested. Separate audit from repair (audit-craft §2).
- Intentional structural duplication — declared via `[[carve_out]]` / `exempt_paths` in the registry, or marked `<!-- lean-audit:sync-intentional -->` — is exempt; report it as disclosed, not as a finding.
- Suppress false positives: before asserting a finding, confirm the matched
  passage is independent duplication, not a quote, cross-reference, or code
  example; if the duplication claim is not supported by evidence, note it as a non-finding with the reason.
- Disclose every "covered elsewhere" claim against its canonical target; never
  assert a citation without confirming the target exists.
- If the engine is unavailable or errors, disclose the reduced coverage and
  continue with the judgment-only checks; do not fabricate the deterministic
  findings.
- When the requested scope, the in-scope path set, or whether edits are wanted is unclear, ask before running — do not guess (audit-craft §2).

## Output footer (audit-craft §5)

End every output with: extensions loaded (none in v1) · registry used (path or `heuristic-only`) · engine
availability · reference path(s) · evidence limits · independence
(independent | self-review | unknown) · assurance level (derived: limited |
reasonable).

## Prevention hook (opt-in)

The same deterministic engine backs an opt-in PreToolUse guard
(`references/scripts/lean_guard.py`) that soft-blocks an edit introducing a NEW
block-severity duplication into guarded markdown. It ships OFF (installation ≠
enforcement); enable it per `references/hook-recipe.md`. It is fail-open (engine
error / timeout / non-guarded path → allow) and overridable (cite, restructure,
or add `<!-- lean-audit:sync-intentional -->`); carve-outs are inherited from the
engine. Codex runs the engine at the Stop hook; true at-edit Codex parity is
future scope.

## Skill Maintenance

For trigger / workflow / grounding / eval edits, read `references/evals/` and
`references/source-grounding.md`; keep evals synthetic. The engine's own tests
live at repo-root `tests/lean_engine_test.py` / `tests/lean_engine_ledger.jsonl`.
After skill-surface edits, rerun `scripts/skill-architecture-report.sh .`.
