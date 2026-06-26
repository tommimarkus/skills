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
`../../docs/audit-reference/audit-craft.md` §2/§3/§5.

## Contract

Own read-only duplication/waste audits of markdown prose and skill surfaces
(governance docs, `SKILL.md`, agents, `docs/*-reference/**`, `references/**`,
`extensions/**`). Delegate: security → `devsecops-audit`; test quality →
`test-quality-audit`; copyright / marks / licence → `ip-hygiene`; code or design
structure → the design skills. Prose surfaces only in v1 (not code duplication).

Inputs: a scope (file, diff, or repo) and an optional `.lean-audit.toml`
canonical-home / must-sync registry. Ask or stop when the scope, the intended
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
- Cite codes from `references/smell-catalog.md`; never restate catalog prose.

## Workflow

1. Establish the scope (file / diff / repo). If a `.lean-audit.toml` exists at the
   scanned root the engine reads it; otherwise it runs heuristic-only — disclose
   which.
2. Run the bundled engine and parse its JSON (resolve the path from this skill's
   directory; under Claude Code that is
   `${CLAUDE_PLUGIN_ROOT}/skills/lean-audit/references/scripts/lean_engine.py`):
   `python3 references/scripts/lean_engine.py <scope> --format json`.
   It emits `LA-DUP-1`/`LA-DUP-2` (block or advisory), `LA-STALE-1`, `LA-DEAD-1`,
   `LA-BLOAT-1`. Exit 1 = a block-severity duplication is present; exit 2 = engine
   error (report the limit, continue with the judgment-only checks). Treat the
   output as evidence, not verdict: do not invent findings it did not produce, and
   do not suppress one without a cited reason.
3. Add the judgment-only checks from `references/procedures/fuzzy-waste.md` —
   `LA-STALE-2` (prose describing a removed/renamed structure) and `LA-BLOAT-2`
   (heavy reference material inlined in always-loaded context). Mark these
   inference (audit-craft §2), not confirmed fact.
4. Assign each finding a risk tier per `materiality.md` (a smell on a high-fan-in
   surface such as CLAUDE.md outranks the same smell on a leaf file). Combine
   severity × risk into the P0–P3 worklist (audit-craft §3 grid).
5. Report. A file or diff scope emits per-finding output; a repo scope adds a
   sectioned rollup by `LA-*` band and a remediation worklist. For each
   duplication, cite the matched code and the canonical target.

## Rules and Stop Conditions

- Read-only: assess and produce a worklist; do not auto-fix unless edits are
  explicitly requested. Separate audit from repair (audit-craft §2).
- Intentional must-sync duplication — declared in the registry or marked
  `<!-- lean-audit:sync-intentional -->` — is exempt; report it as disclosed, not
  as a finding.
- Disclose every "covered elsewhere" claim against its canonical target; never
  assert a citation without confirming the target exists.
- If the engine is unavailable or errors, disclose the reduced coverage and
  continue with the judgment-only checks; do not fabricate the deterministic
  findings.

## Output footer (audit-craft §5)

End every output with: registry used (path or `heuristic-only`) · engine
availability · reference path(s) · evidence limits · independence
(independent | self-review | unknown) · assurance level (derived: limited |
reasonable).

## Skill Maintenance

For trigger / workflow / grounding / eval edits, read `references/evals/` and
`references/source-grounding.md`; keep evals synthetic. The engine's own tests
live at repo-root `tests/lean_engine_test.py` / `tests/lean_engine_ledger.jsonl`.
After skill-surface edits, rerun `scripts/skill-architecture-report.sh .`.
