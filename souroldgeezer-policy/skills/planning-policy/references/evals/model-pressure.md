# Planning-policy forward-evaluation pressure set

`forward-cases.jsonl` is an opt-in, live, fresh-context comparison. It does not
run in unit tests and stores only bounded result summaries. Each harness receives
the same copied synthetic repository, prompt, expected return shape, and
deterministic verifier.

The standard lane runs twice per harness at the exact settled mappings: Claude
`sonnet` / `medium`, Codex `gpt-5.6-terra` / `medium`. Missing input and an
oversized standard step each run once per harness and must stop rather than infer
or expand. The mechanical exact-edit case uses Claude `haiku` / `low` and Codex
`gpt-5.6-luna` / `low`; the analytical unknown uses Claude `opus` / `high` and
Codex `gpt-5.6-sol` / `high`. Deep has structural mapping coverage only because
its pressure task would need a separate adversarial oracle.

Run after an intentional workflow or adapter change:

```text
uv run python scripts/planning_policy_forward_eval.py --harness both --output-dir /secure/path --execute
```

An unavailable mapped model is recorded as `blocked:model_unavailable`; the
runner never downgrades. Results are comparison evidence, not a claim that a
single provider run establishes universal model quality.

Every host run is fresh and non-resuming: Claude uses `--no-session-persistence`
with `--permission-mode acceptEdits`, JSON output, a bounded `--json-schema`,
and the configurable `--claude-max-budget-usd` cap. Codex uses `exec
--ephemeral --approve-for-me --sandbox workspace-write`, an output schema and
a bounded last-message file in the disposable synthetic workdir. Codex has no
CLI dollar cap, so its bounded synthetic scope and `--timeout-seconds` (maximum
180) are the cost limit. Neither host transcript nor final-message file is
retained.
