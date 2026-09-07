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

The original `synthetic-chained-escalation` case exercises ledger-owned
escalation without preserving an executor transcript: its first mechanical
attempt must stop as `blocked:needs_higher_tier`; its fresh second executor gets
only bounded `retry-remediation-v1` material and runs at the ledger-selected
analytical mapping. The adapters map that target exactly; neither the runner nor
the executor chooses a substitute tier.

Run after an intentional workflow or adapter change:

```text
uv run python scripts/planning_policy_forward_eval.py --harness both --output-dir /secure/path --execute
```

An unavailable mapped model is recorded as `blocked:model_unavailable`; the
runner never downgrades. Live execution requires an existing absolute private
output directory (mode 0700 or stricter); otherwise the runner rejects
`--execute` before any host call. Results are comparison evidence, not a claim
that a single provider run establishes universal model quality.

Every host run is fresh and non-resuming: Claude uses `--no-session-persistence`
with `--permission-mode acceptEdits`, JSON output, a bounded `--json-schema`,
and the configurable `--claude-max-budget-usd` cap. Codex uses `exec
--ephemeral --approve-for-me --sandbox workspace-write`, an output schema and
a bounded last-message file in the disposable synthetic workdir. Codex has no
CLI dollar cap, so its bounded synthetic scope and `--timeout-seconds` (maximum
180) are the cost limit. Neither host transcript nor final-message file is
retained.

## Approval transport acceptance

For an explicitly authorized handoff change, run one fresh producer and one
fresh consumer per requested model (`gpt-6-astra` and `gpt-5.6-sol`, high effort).
Use `codex exec --ephemeral --sandbox read-only`, 120 seconds per invocation,
no retries or substitutions, and at most four invocations. This is synthetic
transport acceptance, not a live TUI reset test or a model-quality comparison.

Give each producer a fixed self-contained approval-ready v5 fixture and the
candidate skill paths. The sandbox forbids saving the plan. Extract only its
final `<proposed_plan>` payload. Give the consumer only that payload and the
candidate skill paths, without producer tool history or fixture files. Require
successful `resolve-handoff` and exact equality of the canonical digest,
read/write sets, acceptance command, and capability requirements; require
`approval_ready: true` and `dispatch_ready: false`. A prose-only payload fails.
Keep bounded final approval/result artifacts and a compact comparison summary;
do not collect provider usage, raw transcripts, or broaden the existing runner.
