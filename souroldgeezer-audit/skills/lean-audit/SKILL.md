---
name: lean-audit
description: >-
  Use when auditing prose and skill/plugin workflow surfaces — a repo, file, or diff of docs, SKILL.md, agents, references, or extensions — for duplication and waste: restated prose, stale/dead references, oversized or verbose context, per-use/per-mode load cost, and pre-run finishability of staged, iterative, or delegated workflows (orchestrator context growth, tool/hook/log/handoff cost, verification reserve, and trace calibration). Includes mechanical source copy-paste duplication (`LA-CODE-DUP-*`); semantic DRY stays with software-design and source dead code is out of scope. Read-only; defer security, test quality, and IP/licence. Explicit-request-only lenses: platform redundancy (live verified) and propose-only minify (never applied).
---

# Lean Audit

Audit prose and skill surfaces for duplication and waste (Lean *muda*). A bundled
deterministic engine computes the findings; this workflow runs it, ranks by
materiality, and adds the judgment-only waste checks the engine cannot decide.
Cite the owning catalog/procedure code (`LA-*`). Conform to
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

Compose four additional lenses with the waste path:

- **Per-use cost (`LA-PUC-*`, surface-gated):** run when scope contains a
  `SKILL.md`, `agents/*.md`, or `commands/**/*.md`; otherwise remain silent.
- **Run viability (`LA-RUN-*` / `LA-ORCH-*`, surface-gated):** run on an entry
  surface that declares staged, iterative, delegated, retrying, or token-budget
  work, or on an explicit finishability/orchestrator-cost request. It is an
  offline pre-run forecast; traces only calibrate it when supplied.
- **Platform redundancy (`LA-NAT-*`, opt-in):** run only on an explicit native-
  capability request and verify candidates against current host documentation.
- **Minify (`LA-MIN-*`, opt-in, propose-only):** run only on an explicit
  reduction request; emit a gated diff but never write targets.

All lenses are read-only. The default path makes zero agent/network calls.

Inputs: a scope (the whole repo, a file, a set of named files, or a diff) and an optional `.lean-audit.toml` canonical-home / carve-out registry. Ask or stop when the scope, the intended
surface, or requested edits lack a safe default. For false-positive discipline,
fact-vs-inference, and severity, see
[`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) §2–§3.

## One adaptive path (no mode dispatch)

This skill has no Quick/Deep modes — its detection is deterministic, so it runs
one path and DERIVES the assurance level from coverage: a file or diff scope →
`limited`; a full-repo enumeration → `reasonable`. State the assurance on one
line (audit-craft §4, by named principle — as `ip-hygiene` does).

The surface-gated cost lenses and explicit opt-in lenses do not introduce a
second mode; coverage still derives assurance.

## Load Map

- Load [`../../docs/audit-reference/audit-craft.md`](../../docs/audit-reference/audit-craft.md) (discipline + output contract).
- Load [`../../docs/audit-reference/materiality.md`](../../docs/audit-reference/materiality.md) (risk tier).
- Load [`../../docs/audit-reference/sampling-projection.md`](../../docs/audit-reference/sampling-projection.md) only at repo scale when
  full enumeration exceeds budget.
- Load [`../../docs/audit-reference/scaled-audit.md`](../../docs/audit-reference/scaled-audit.md) (delegation + evidence
  durability) only at repo scale when per-finding evidence may not reach the rollup intact; §4 records that clone
  detection is not divisible by file. If evidence starts outgrowing context mid-run, load it then rather than continuing.
- Load [`references/procedures/fuzzy-waste.md`](references/procedures/fuzzy-waste.md) for the judgment-only `LA-STALE-2`,
  `LA-BLOAT-2`, and `LA-VERBOSE-2` checks (the engine does not emit these; `LA-VERBOSE-2` confirms or clears engine `LA-VERBOSE-1` nominations).
- Run the bundled engine [`references/scripts/lean_engine.py`](references/scripts/lean_engine.py) (the deterministic source of `LA-DUP-*` / `LA-STALE-1` / `LA-DEAD-1` / `LA-BLOAT-1` / `LA-VERBOSE-1`) per Workflow step 2.
- Run the bundled code lens [`references/scripts/code_lens.py`](references/scripts/code_lens.py) (the deterministic source of `LA-CODE-DUP-*`) when the scope contains source files — see Workflow step 2b.
- For the opt-in prevention hooks, see [`references/hook-recipe.md`](references/hook-recipe.md) (enablement) and the guard entrypoints [`references/scripts/lean_guard.py`](references/scripts/lean_guard.py) and [`references/scripts/load_cost_guard.py`](references/scripts/load_cost_guard.py) (not part of an audit run).
- All six entry scripts are stable shims; implementation lives in [`references/scripts/leanaudit/`](references/scripts/leanaudit/) (verify with `uv run python -m unittest tests.lean_audit_shims_test`).
- **Per-use cost lens (surface-gated):** load [`references/procedures/per-use-cost.md`](references/procedures/per-use-cost.md)
  only when an entry artifact (the families listed in `## Contract`) is in scope.
  Run the bundled harness
  [`references/scripts/skill_load_cost.py`](references/scripts/skill_load_cost.py) (`resolve_closure` / `measure` /
  `baseline`) to size closures and project deltas; declared multi-entry routes,
  predicates, anchors, and selection metadata are detailed in the procedure.
  The procedure owns the `LA-PUC-*` band; do not restate it.
- **Run-viability lens (surface-gated):** load [`references/procedures/run-viability.md`](references/procedures/run-viability.md)
  only for the workflow signals in `## Contract`. Run
  [`references/scripts/workflow_cost.py`](references/scripts/workflow_cost.py)
  offline to discover orchestrators, inventory hook registrations without
  executing them, and inspect declared convergence/checkpoint risks; add a
  declared scenario for a finishability verdict and supplied traces only for
  usage calibration. The procedure owns `LA-RUN-*` / `LA-ORCH-*`; do not infer
  a model capacity or observed lifecycle behavior.
- **Platform-redundancy lens (opt-in):** load [`references/procedures/platform-redundancy.md`](references/procedures/platform-redundancy.md)
  ONLY when the request explicitly asks for a native/platform-redundancy check. It
  carries the reinvention-pattern catalog, the runtime-specific live consultation
  protocol, the confidence tiering, the degraded-mode rule, and the emit fields.
  The procedure owns `LA-NAT-*`; do not restate it.
- **Minify lens (opt-in, propose-only):** load [`references/procedures/minify.md`](references/procedures/minify.md)
  ONLY when the request explicitly asks for a minification / reduction
  proposal. It carries the Locate → Propose → Fidelity-verify → Emit protocol,
  the shadow-workspace mechanics, the rejection taxonomy, and the emit fields.
  The procedure owns `LA-MIN-*`; do not restate it.
- Cite core waste codes from [`references/smell-catalog.md`](references/smell-catalog.md)
  and conditional-lens codes from their owning procedure; never restate either.

## Workflow

1. Establish the whole-repo, directory, named-file, or diff scope. Engines scan a
   directory, so use the repo root or nearest common directory; filter findings
   to the requested paths and apply declared carve-outs before deriving any
   limited-scope gate. Disclose `.lean-audit.toml` or `heuristic-only`.
2. Run the markdown engine as JSON (use `uv`; `python3` is fallback only at
   ≥3.11):

   ```text
   uv run "${CLAUDE_PLUGIN_ROOT}/skills/lean-audit/references/scripts/lean_engine.py" <dir> --format json
   uv run "<skill-dir>/references/scripts/lean_engine.py" <dir> --format json
   ```

   Exit 1 means block findings, 2 input/tool error (disclose and continue
   judgment checks), and 3 an unmet interpreter floor (stop). Keep only
   in-scope paths; never invent or silently suppress engine findings.
2b. If source files are in scope, run the same host-specific forms with
   `code_lens.py`; keep clone pairs where either path is in scope. Exit handling
   matches step 2. Otherwise record `no source surfaces — code lens silent`.
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
5. **Run-viability lens (surface-gated).** If entry surfaces declare phases,
   delegation, loops, retries, token budgets, or orchestrator/coordinator work,
   run [`references/procedures/run-viability.md`](references/procedures/run-viability.md)
   end-to-end. Static discovery runs without network access; an exact verdict
   requires declared context capacity and stage ranges. Supplied traces are
   metadata-only calibration evidence, never a prerequisite. Otherwise record
   "no long-running workflow signals — run-viability lens silent".
6. Assign each waste-lens finding a risk tier per `materiality.md` (a smell on a
   high-fan-in surface such as CLAUDE.md outranks the same smell on a leaf file).
   Combine severity × risk into the P0–P3 worklist (audit-craft §3 grid). Per-use
   findings carry their own dial-adjusted priority (see procedure); merge them into
   the worklist under the `LA-PUC-*` band with their separate priority rationale.
7. Report against what was actually examined. Derive assurance from the in-scope coverage: a file / named-files / diff scope → `limited`; a full-repo enumeration → `reasonable`. A file/diff scope emits per-finding output; a repo scope adds a sectioned rollup by `LA-*` band and a remediation worklist. For each duplication, cite the matched code and the canonical target. Per-use findings include their emitted fidelity baseline as a named `baseline:` block.

   **Limited-scope gate.** Emit `limited-scope gate: <status>` only for a file,
   named-file, or diff coverage — never for a directory or whole-repo rollup.
   Derive it after scope filtering and declared carve-outs; never derive it from
   a directory-wide engine exit alone. If a confirmed in-scope block exists,
   `fail` wins: high-band `LA-DUP-1`, `LA-DUP-2`, `LA-CODE-DUP-1`, `LA-RUN-2`,
   or `LA-RUN-3` when the expected lane exceeds declared capacity. Otherwise
   emit `not-evaluated` when the Python ≥3.11 floor is unmet, a required
   deterministic engine is unavailable, or an activated run-viability lens lacks
   evidence and cannot rule out overflow. Otherwise emit `pass-limited`.
   Per-use, platform-redundancy, minify, and judgment-only findings are warn/info
   and nonblocking. State the machinery/evidence cause for `not-evaluated` in
   the footer; it is a limited-assurance status, not a full-repo verdict.

## Platform-redundancy lens (opt-in)

Only on an explicit native/platform-redundancy request: run
[`references/procedures/platform-redundancy.md`](references/procedures/platform-redundancy.md)
end-to-end. Never auto-migrate; an unavailable live verifier yields disclosed,
unverified `LA-NAT-2` review items.

## Minify lens (opt-in, propose-only)

Only on an explicit reduction-proposal request: run Workflow steps 1–6, then
[`references/procedures/minify.md`](references/procedures/minify.md) end-to-end.
It emits reviewable diffs but writes no target; failed gates become `LA-MIN-2`
and source clones become `LA-MIN-3` referrals.

## Rules and Stop Conditions

- Read-only: assess and produce a worklist; do not auto-fix unless edits are
  explicitly requested. Separate audit from repair (audit-craft §2). The
  minify lens is that explicit-request path — and even then it only PRODUCES
  the edit (see the minify bullet below); it never applies one.
- Intentional structural duplication — declared via `[[carve_out]]` / `exempt_paths` in the registry, or marked `<!-- lean-audit:sync-intentional -->` — is exempt; report it as disclosed, not as a finding. Run-viability catalog/example files may instead use the exact file-wide `<!-- lean-audit:workflow-intentional — rationale -->` HTML comment defined by `run-viability.md`; it counts only outside fenced code and does not belong on runnable entry workflows.
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
- Run viability: never name a run `feasible` without a declared context window,
  stage ranges, and verification reserve. Treat missing bounds as `indeterminate`;
  do not substitute a model-name guess. Keep out-of-band telemetry out of model-
  visible cost, never coerce unknown values to zero, and never echo raw trace
  content.
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

End every output with: extensions loaded (none in v1) · registry path or
`heuristic-only` · engine availability · references · evidence limits ·
independence (`independent | self-review | unknown`) · derived assurance.
Append each activated conditional procedure's disclosure fields.

When the code-duplication lens ran, append: code lens ran (source surfaces
detected) · languages/extensions scanned · min-tokens threshold · declared
`dup-intentional` suppressions honoured (whole-file exempted files / region-scoped
spans) · fail-open skips (unreadable/binary/unknown-extension).

## Prevention hook (opt-in)

[`references/scripts/lean_guard.py`](references/scripts/lean_guard.py) and
[`references/scripts/load_cost_guard.py`](references/scripts/load_cost_guard.py)
protect new block duplication and committed fidelity floors. Both ship OFF;
[`references/hook-recipe.md`](references/hook-recipe.md) owns enablement,
override, and fail-open semantics.

## Skill Maintenance

For edits, read `references/evals/`, `references/source-grounding.md`, and the
non-runtime maintainer guide `references/scripts/README.md`; keep evals
synthetic. Repo-root ledgers/tests cover both engines, guards, load cost,
run viability, traces, and shims. Rerun audit-craft §8 obligations.
