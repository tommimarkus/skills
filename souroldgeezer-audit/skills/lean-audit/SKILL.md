---
name: lean-audit
description: >-
  Use when auditing prose and skill surfaces — a repo, file, or diff of docs, SKILL.md, agents, references, or extensions — for duplication and waste: near-duplicate or restated prose, broken or stale references, dead or unreferenced reference/extension files, oversized always-loaded context, verbose passages, and — when skills, commands, or agents are in scope — per-use/per-mode load cost. Markdown/prose plus mechanical source-code copy-paste **duplication** (bundled token-clone engine, `LA-CODE-DUP-*`); *semantic* duplication/DRY stays with software-design; mechanical source-level dead code is out of scope. Read-only; defer security, test-quality, and IP/licence work to sibling skills. On explicit request only, two opt-in lenses: platform-redundancy flags custom hooks/scripts, guidance prose, skills/commands/agents, or MCP servers that reinvent a native Claude Code™ or Codex capability (verified live, never auto-run); and minify produces a propose-only reduction diff plus fidelity report — never applied.
---

# Lean Audit

Audit prose and skill surfaces for duplication and waste (Lean *muda*). A bundled
deterministic engine computes the findings; this workflow runs it, ranks by
materiality, and adds the judgment-only waste checks the engine cannot decide.
Cite [`references/smell-catalog.md`](references/smell-catalog.md) codes (`LA-*`). Conform to
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2/§3/§4/§5.

## Contract

Own read-only duplication/waste audits of markdown prose and skill surfaces
(governance docs, `SKILL.md`, agents, `docs/*-reference/**`, `references/**`,
`extensions/**`), plus mechanical source-code copy-paste duplication. Claude Code
expands `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PLUGIN_ROOT}` in the loaded skill;
Codex resolves `<skill-dir>` once from the absolute source path reported for this
loaded `SKILL.md`. Delegate: security → `devsecops-audit`; test quality →
`test-quality-audit`; copyright / marks / licence → `ip-hygiene`; *semantic* code
duplication / DRY ownership → the design skills (`software-design`). Source code:
mechanical copy-paste **duplication** is owned via the bundled `code_lens.py`
(token-window clones, `LA-CODE-DUP-*`). Mechanical source-level **dead code**
remains out of scope and unowned today (tracked for v1.1) — do not reroute it to a
design skill, which reviews structure, not mechanical dead code.

A second lens — per-use load cost — is surface-gated and composes with the waste
lens: it fires only when the scope contains at least one entry artifact (`SKILL.md`,
`agents/*.md`, or `commands/**/*.md`). When no entry artifact is in scope the per-use lens is silent
and the waste lens runs unchanged. Both lenses are read-only and advisory.

A third lens — platform redundancy (`LA-NAT-*`) — is OPT-IN, not surface-gated: it
runs ONLY when the request explicitly asks whether custom artifacts reinvent a
native Claude Code or Codex capability named by the request. A normal duplication/waste run never
activates it and makes zero agent/network calls. It is read-only and advisory,
and its native verdicts come from a live check of that host's official docs
(never a bundled capability list). See `## Platform-redundancy lens (opt-in)`.

A fourth lens — minify (`LA-MIN-*`) — is OPT-IN and PROPOSE-ONLY: it runs ONLY
when the request explicitly asks for a minification / reduction proposal. It
consumes the waste and per-use lenses' findings to produce a reviewable diff
plus a fidelity report; it NEVER writes target files — applying the diff is a
separate, explicit user step outside this skill. A normal duplication/waste
run never activates it and it makes zero agent/network calls. See
`## Minify lens (opt-in, propose-only)`.

Inputs: a scope (the whole repo, a file, a set of named files, or a diff) and an optional `.lean-audit.toml` canonical-home / carve-out registry. Ask or stop when the scope, the intended
surface, or requested edits lack a safe default. For false-positive discipline,
fact-vs-inference, and severity, see
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2–§3.

## One adaptive path (no mode dispatch)

This skill has no Quick/Deep modes — its detection is deterministic, so it runs
one path and DERIVES the assurance level from coverage: a file or diff scope →
`limited`; a full-repo enumeration → `reasonable`. State the assurance on one
line (audit-craft §4, by named principle — as `ip-hygiene` does).

The opt-in platform-redundancy and minify lenses are layered on top of this
path and do not change it: the default run (waste + surface-gated per-use
cost) is unchanged, and the opt-in lenses run only on explicit request.

## Load Map

- Load [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) (discipline + output contract).
- Load [`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md) (risk tier).
- Load [`../../docs/audit-reference/sampling-projection.md`](../../docs/audit-reference/sampling-projection.md) only at repo scale when
  full enumeration exceeds budget.
- Load [`references/procedures/fuzzy-waste.md`](references/procedures/fuzzy-waste.md) for the judgment-only `LA-STALE-2`,
  `LA-BLOAT-2`, and `LA-VERBOSE-2` checks (the engine does not emit these; `LA-VERBOSE-2` confirms or clears engine `LA-VERBOSE-1` nominations).
- Run the bundled engine [`references/scripts/lean_engine.py`](references/scripts/lean_engine.py) (the deterministic source of `LA-DUP-*` / `LA-STALE-1` / `LA-DEAD-1` / `LA-BLOAT-1` / `LA-VERBOSE-1`) per Workflow step 2.
- Run the bundled code lens [`references/scripts/code_lens.py`](references/scripts/code_lens.py) (the deterministic source of `LA-CODE-DUP-*`) when the scope contains source files — see Workflow step 2b.
- For the opt-in prevention hooks, see [`references/hook-recipe.md`](references/hook-recipe.md) (enablement) and the guard entrypoints [`references/scripts/lean_guard.py`](references/scripts/lean_guard.py) and [`references/scripts/load_cost_guard.py`](references/scripts/load_cost_guard.py) (not part of an audit run).
- All five scripts above are stable entry shims; the implementation lives in the sibling package [`references/scripts/leanaudit/`](references/scripts/leanaudit/) (verify: `uv run python -m unittest tests.lean_audit_shims_test` in this marketplace repo, or run any shim `--help`).
- **Per-use cost lens (surface-gated):** load [`references/procedures/per-use-cost.md`](references/procedures/per-use-cost.md)
  only when an entry artifact (the families listed in `## Contract`) is in scope.
  Run the bundled harness
  [`references/scripts/skill_load_cost.py`](references/scripts/skill_load_cost.py) (`resolve_closure` / `measure` /
  `baseline`) to size closures and project deltas. Cite the `LA-PUC-*` band from
  [`references/smell-catalog.md`](references/smell-catalog.md); do not restate procedure prose.
- **Platform-redundancy lens (opt-in):** load [`references/procedures/platform-redundancy.md`](references/procedures/platform-redundancy.md)
  ONLY when the request explicitly asks for a native/platform-redundancy check. It
  carries the reinvention-pattern catalog, the runtime-specific live consultation
  protocol, the confidence tiering, the degraded-mode rule, and the emit fields.
  Cite `LA-NAT-*` from [`references/smell-catalog.md`](references/smell-catalog.md); do not restate procedure prose.
- **Minify lens (opt-in, propose-only):** load [`references/procedures/minify.md`](references/procedures/minify.md)
  ONLY when the request explicitly asks for a minification / reduction
  proposal. It carries the Locate → Propose → Fidelity-verify → Emit protocol,
  the shadow-workspace mechanics, the rejection taxonomy, and the emit fields.
  Cite `LA-MIN-*` from [`references/smell-catalog.md`](references/smell-catalog.md); do not restate procedure prose.
- Cite codes from [`references/smell-catalog.md`](references/smell-catalog.md); never restate catalog prose.

## Workflow

1. Establish the scope: the whole repo, a single file, a set of named files, or a diff (its changed files). The bundled engine has no single-file or diff mode — it always scans the markdown tree rooted at a DIRECTORY — so pick the directory to run it in and the in-scope path set to keep. If a `.lean-audit.toml` exists at the scanned root the engine reads it; otherwise it runs heuristic-only — disclose which.
2. Run the bundled engine and parse its JSON. **Interpreter — `uv` is primary:** the engine needs Python ≥3.11 (it uses `tomllib`), so run it with `uv`, which provisions or selects a conforming interpreter even when the system `python3` is older. On Claude Code run `uv run "${CLAUDE_PLUGIN_ROOT}/skills/lean-audit/references/scripts/lean_engine.py" <dir> --format json` (Claude Code expands `${CLAUDE_PLUGIN_ROOT}` inline when this skill loads; reference procedures reuse that same resolved value, as they are read raw without substitution). On Codex run `uv run "<skill-dir>/references/scripts/lean_engine.py" <dir> --format json` with the resolved source path. The corresponding `python3` form is a fallback, valid only where `python3` is already ≥3.11. `<dir>` is the repo root for a repo scope, or the nearest common directory of the in-scope files for a file / named-files / diff scope. The engine scans the whole markdown tree under `<dir>` and emits `LA-DUP-1`/`LA-DUP-2` (block or advisory), `LA-STALE-1`, `LA-DEAD-1`, `LA-BLOAT-1`, `LA-VERBOSE-1` (info verbosity nominations); exit 1 = a block-severity duplication is present, exit 2 = engine error on input (report the limit, continue with the judgment-only checks), exit 3 = interpreter floor unmet — **STOP**, do not substitute a judgment-only pass (see `## Rules and Stop Conditions`). For a file / named-files / diff scope, KEEP ONLY findings whose `path` is in scope — the engine reports the whole tree, so this filter is what makes the scope real. Treat the output as evidence, not verdict: do not invent findings it did not produce, and do not suppress one without a cited reason.
2b. **Code-duplication lens (surface-gated).** If the scope contains source files (non-markdown code by extension), run `uv run "${CLAUDE_PLUGIN_ROOT}/skills/lean-audit/references/scripts/code_lens.py" <dir> --format json` on Claude Code, or `uv run "<skill-dir>/references/scripts/code_lens.py" <dir> --format json` on Codex (uv primary as in step 2; the corresponding `python3` form is a fallback only where `python3` is ≥3.11; `<dir>` = repo root, or the nearest common directory of the in-scope files) and parse its JSON. It emits `LA-CODE-DUP-1` (block, clone ≥ 2× min-tokens) and `LA-CODE-DUP-2` (advisory) clone pairs; exit 1 = a block clone present, exit 2 = engine error on input (disclose reduced coverage, continue with the other lenses), exit 3 = interpreter floor unmet — STOP as in step 2. For a file / named-files / diff scope, KEEP ONLY clones whose `path` or `matched_path` is in scope. If no source files are in scope, record "no source surfaces in scope — code lens silent" and skip this step.
3. Add the judgment-only checks from [`references/procedures/fuzzy-waste.md`](references/procedures/fuzzy-waste.md) —
   `LA-STALE-2` (prose describing a removed/renamed structure), `LA-BLOAT-2`
   (heavy reference material inlined in always-loaded context), and `LA-VERBOSE-2`
   (confirm or clear each engine `LA-VERBOSE-1` verbosity nomination — never
   free-scan for wordiness). Mark these inference (audit-craft §2), not confirmed
   fact.
4. **Per-use cost lens (surface-gated).** Detect whether the scope contains at
   least one entry artifact (the families listed in `## Contract`). If yes, run the
   procedure at [`references/procedures/per-use-cost.md`](references/procedures/per-use-cost.md) end-to-end (resolve
   closures → model per-mode load sets → find LA-PUC-1/2/3 → classify
   fidelity-safety → infer dial → emit findings + fidelity baseline). If no entry
   artifact is in scope, record "no per-use surfaces in scope — per-use lens
   silent" and skip this step; the waste-lens findings from steps 2–3 are
   unchanged.
5. Assign each waste-lens finding a risk tier per `materiality.md` (a smell on a
   high-fan-in surface such as CLAUDE.md outranks the same smell on a leaf file).
   Combine severity × risk into the P0–P3 worklist (audit-craft §3 grid). Per-use
   findings carry their own dial-adjusted priority (see procedure); merge them into
   the worklist under the `LA-PUC-*` band with their separate priority rationale.
6. Report against what was actually examined. Derive assurance from the in-scope coverage: a file / named-files / diff scope → `limited`; a full-repo enumeration → `reasonable`. A file/diff scope emits per-finding output; a repo scope adds a sectioned rollup by `LA-*` band and a remediation worklist. For each duplication, cite the matched code and the canonical target. Per-use findings include their emitted fidelity baseline as a named `baseline:` block.

## Platform-redundancy lens (opt-in)

Runs ONLY on an explicit native/platform-redundancy request — never as part of a
default waste run, and never auto-fired by surface detection. When requested, load
[`references/procedures/platform-redundancy.md`](references/procedures/platform-redundancy.md) and run it end-to-end (candidate
detection → runtime-specific live verification → synthesis → worklist merge).
Read-only; never auto-migrate. If the live check is unavailable, degrade to
unverified `LA-NAT-2` review items and disclose.

## Minify lens (opt-in, propose-only)

Runs ONLY on an explicit minification / reduction-proposal request — never as
part of a default waste run, and never auto-fired by surface detection. When
requested, run Workflow steps 1–5 first (they produce the ranked worklist the
lens consumes), then load [`references/procedures/minify.md`](references/procedures/minify.md)
and run it end-to-end (Locate → Propose → Fidelity-verify → Emit). Output is a
reviewable diff per target plus a fidelity report — never an applied edit.
Reductions that fail the adversarial fidelity gate are rejected with a reason
(`LA-MIN-2`), never merged; source-code clones are referred, not rewritten
(`LA-MIN-3`). All gates use only the bundled engine and harness — zero
agent/network calls.

## Rules and Stop Conditions

- Read-only: assess and produce a worklist; do not auto-fix unless edits are
  explicitly requested. Separate audit from repair (audit-craft §2). The
  minify lens is that explicit-request path — and even then it only PRODUCES
  the edit (see the minify bullet below); it never applies one.
- Intentional structural duplication — declared via `[[carve_out]]` / `exempt_paths` in the registry, or marked `<!-- lean-audit:sync-intentional -->` — is exempt; report it as disclosed, not as a finding.
- Suppress false positives: before asserting a finding, confirm the matched
  passage is independent duplication, not a quote, cross-reference, or code
  example; if the duplication claim is not supported by evidence, note it as a non-finding with the reason.
- Disclose every "covered elsewhere" claim against its canonical target; never
  assert a citation without confirming the target exists.
- **Interpreter floor is a stop cause, not a degrade.** The deterministic engine
  requires Python ≥3.11 (`tomllib`), reached via `uv` (primary — it can provision
  a conforming interpreter) or an already-≥3.11 `python3`. If no conforming
  interpreter is available — the shim exits 3 with a `requires Python >=3.11`
  message, or `uv` reports no compatible interpreter — STOP and report that
  lean-audit cannot run for lack of the required interpreter. A judgment-only pass
  is not a valid substitute for the missing deterministic layer; do not silently
  degrade to one.
- If the engine is otherwise unavailable or errors on input (exit 2), disclose the
  reduced coverage and continue with the judgment-only checks; do not fabricate the
  deterministic findings.
- When the requested scope, the in-scope path set, or whether edits are wanted is unclear, ask before running — do not guess (audit-craft §2).
- Platform-redundancy lens (opt-in): never assert "native" from the pattern catalog
  alone — the catalog only nominates; a cited live `claude-code-guide` answer
  for Claude Code or official OpenAI docs answer for Codex is
  what promotes a candidate to `LA-NAT-1`. Surface confirmed redundancy as *review*,
  never *delete*. Disclose the network dependency and the "capabilities as observed
  <date>" recency. If the live check is unavailable, degrade to unverified
  `LA-NAT-2` review items and disclose; do not fabricate a native verdict.
- Minify lens (opt-in, propose-only): emit proposal diffs in the report output
  (or a user-requested scratch file), never into the target tree; applying a
  proposed diff is a separate explicit user action outside this skill. Never
  emit a reduction that failed — or could not run — a required fidelity gate;
  reject it with its reason code instead (fail-closed for acceptance).

## Output footer (audit-craft §5)

End every output with: extensions loaded (none in v1) · registry used (path or `heuristic-only`) · engine
availability · reference path(s) · evidence limits · independence
(independent | self-review | unknown) · assurance level (derived: limited |
reasonable).

When the per-use lens ran, append: detected entry surfaces + closures analyzed ·
inferred dial + basis + any maintainer override · harness availability
([`references/scripts/skill_load_cost.py`](references/scripts/skill_load_cost.py) present / unavailable) · hookability
pointer ([`references/hook-recipe.md`](references/hook-recipe.md)).

When the code-duplication lens ran, append: code lens ran (source surfaces
detected) · languages/extensions scanned · min-tokens threshold · fail-open skips
(unreadable/binary/unknown-extension).

When the opt-in platform-redundancy lens ran, also append: lens ran (opt-in) ·
artifact families detected · runtime verifier + availability (`claude-code-guide`
for Claude Code | official OpenAI docs for Codex | unavailable →
degraded) · citations gathered + capabilities as observed `<date>` · network
dependency.

When the opt-in minify lens ran, also append: lens ran (opt-in, propose-only —
no target files written) · targets minified · reductions accepted / rejected
(with reason codes) · token delta and per-use closure delta
([`references/scripts/skill_load_cost.py`](references/scripts/skill_load_cost.py) `snapshot`/`measure`, before → after) ·
pointer verification result (`diff` gate + `LA-STALE-1` shadow scan) ·
guard-token gate result (`guard_tokens`, for any `tighten` reduction) · target
evals re-run (case counts + result | no eval pack — restricted classes) ·
shadow-workspace path.

## Prevention hook (opt-in)

The same deterministic engine backs an opt-in PreToolUse guard
([`references/scripts/lean_guard.py`](references/scripts/lean_guard.py)) that soft-blocks an edit introducing a NEW
block-severity duplication into guarded markdown. A sibling guard
([`references/scripts/load_cost_guard.py`](references/scripts/load_cost_guard.py)) protects a skill's per-use
inventory of codes and sections against its committed floor
(`tests/skill_load_cost/baselines/<skill>.json`). Both ship OFF; enable, override,
and fail-open semantics are defined in [`references/hook-recipe.md`](references/hook-recipe.md).

## Skill Maintenance

For trigger / workflow / grounding / eval edits, read `references/evals/` and
[`references/source-grounding.md`](references/source-grounding.md); keep evals synthetic. The engines' tests
live at repo root: `tests/lean_engine_test.py` / `tests/lean_engine_ledger.jsonl`
(markdown engine), `tests/lean_code_lens_test.py` / `tests/lean_code_ledger.jsonl`
(code lens), and `tests/lean_guard_test.py` / `tests/load_cost_guard_test.py` /
`tests/skill_load_cost_test.py` (guards + per-use harness).
For the bundled Python tooling's architecture and a safe-change guide — the
shim→`leanaudit/` package contract, module map, finding codes, the ruff/mypy
standard, config/data files, and this test matrix — read the maintainer guide
`references/scripts/README.md` (referenced as an inline path, not a link, so this
dev doc stays out of the runtime load closure; CLAUDE.md link-checks the path).
Rerun obligations after craft or skill-surface changes:
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §8.
