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
- Platform-redundancy lens (`LA-NAT-*`): the reinvention-pattern catalog is
  repo-authored (patterns to suspect, in the auditor's own words — not a copied
  feature list). Native verdicts are NOT stored here; they come from a live
  `claude-code-guide` consultation for Claude Code or official OpenAI docs
  consultation for Codex at audit time and are disclosed with the capability's
  observed-on date. No third-party doc text is copied into the skill; findings
  cite the live source and never transfer verdicts across runtimes.
- Minify lens (`LA-MIN-*`): the Locate → Propose → Fidelity-verify → Emit
  protocol, the obligation-ledger method, and the rejection taxonomy are
  repo-authored, motivated by this repo's own token-reduction lessons
  (deterministic gates and spec review alone miss precision loss in dense
  skill docs; every "covered elsewhere" pointer must be verified against its
  target's content). The deterministic gates reuse the bundled harness
  (`scripts/skill_load_cost.py`) and engine (`scripts/lean_engine.py`); no
  third-party prose, diffs, or fixtures are copied into the skill, and every
  eval case is synthetic.
- Per-use declared profiles: the multi-entry route, predicate, heading-anchor,
  fallback, cross-entry deduplication, and selection-metadata schema are
  repo-authored from local skill-loading needs. The pending-edit marginal
  advisory is likewise a local guard contract. No host/vendor loading schema,
  selection text, or trace was copied; committed scenarios use repository paths
  and synthetic selection strings.
- Hook-cost inventory: the content-free selector/evidence fixture schema and
  enabled/model-visible frequency multiplication are repo-authored. Hook
  commands remain opaque and are neither executed nor emitted. Fixtures are
  synthetic metadata; no command bodies, hook output, provider logs, or vendor
  hook schema are bundled.
- Run-viability/orchestrator lens (`LA-RUN-*`, `LA-ORCH-*`): the workflow score,
  three-lane budget simulator, fixed/per-item output forecast, retry/progress/
  unresolved-scope/checkpoint checks, evidence hierarchy, findings, and
  fixtures are repo-authored from user-reported staged-workflow and bounded-loop
  failure modes. The current trace lane measures usage metadata only; raw
  lifecycle reconstruction, TDD-loop detection, and unchanged-hypothesis
  history remain deferred and are not claimed. Trace adapters map field names
  documented by the
  [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create),
  [Anthropic tool-use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview),
  [Claude Code monitoring guide](https://code.claude.com/docs/en/monitoring-usage),
  [Codex manual](https://developers.openai.com/codex/codex-manual.md), and
  [OpenTelemetry GenAI attributes](https://opentelemetry.io/docs/specs/semconv/registry/attributes-gen-ai/).
  No vendor prose, schemas, raw traces, or third-party fixtures are bundled;
  trace fixtures and evals are synthetic and metadata-only.
