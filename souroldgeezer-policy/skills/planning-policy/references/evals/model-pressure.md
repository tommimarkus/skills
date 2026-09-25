# Planning-policy forward-evaluation pressure set

## Approved fixed workflow-evidence pilot

This is a one-fixture, four-trial Codex-only procedure for testing whether the
planning-policy guidance changes complete-run outcomes or measured economy. It
does not authorize production telemetry, provider discovery, additional trials,
or a Claude comparison; Claude remains unverified.

The parent first pins the repository revision, fixture and immutable-oracle
SHA-256 values, host version/profile, coordinator model/effort, and every
available worker mapping. It then preflights complete coordinator and worker
usage coverage before each spend. Four fresh `gpt-5.6-sol`/`high` coordinators
run the original fixture in ABBA order: baseline, candidate, candidate,
baseline. Every trial has a 15-minute ceiling, at most two worker leaves, four
worker attempts, and terminal cleanup proof. Any deviation stops for approval.

The fixture at `tests/planning_policy_workflow/fixture/` has two independent
outcomes: separator-collapsing ASCII-alphanumeric slugs and stable
case-insensitive deduplication of stripped nonempty labels. Its `oracle.py`
and test are outside worker writes. Give coordinators only the goals and
repository, never a prewritten plan or target score.

After every trial, retain the supplied content-free usage summaries and outcome
evidence privately. Feed only those records to
`scripts/planning_policy_workflow_report.py`. The parent writes its bounded
result here after integration. Missing usage, mismatched provenance, failed or
blocked outcomes, unclean lifecycle, or failed oracle evidence make economy
claims incomparable; lower counters from a failed run are not improvement.

### 2026-09-25 pilot evidence

Pinned baseline: `33fae41589ddf05cf3ce07438302b97623b519ed`; candidate:
`873d8b0d3a51c880fb6c118dcb35e0c9dc6db338`. Fixture SHA-256:
`5731074c5cb3c1b7ba938f0a8f5cff1af7ae559432533b77d13bfdd3737a916a`;
immutable oracle SHA-256:
`7cf4d4996b8f47830c3c1697097a04f9fd95d18d6ce69a4c0ecb5e911ce60212`.
The host was Codex CLI 0.156.1, coordinator `gpt-5.6-sol`/`high`, with the
four declared exact tier mappings available. Workers selected
`gpt-5.6-luna`/`low`. Native contexts confirmed matching `workspace-write`,
`on-request`, and disabled sandbox network access.

| Trial | Variant | Seconds | Task oracle / cleanup | Worker turns / ledger attempts | Workflow result |
|---|---|---:|---|---:|---|
| a1 | Baseline | 573.707 | Passed / cleaned | 2 / 2 | Failed: worker finals lacked the required bounded return; parent normalized them |
| b1 | Candidate | 611.724 | Passed / cleaned | 4 / 2 | Failed: initial failed worker returns were omitted before same-ID follow-ups |
| b2 | Candidate | 531.910 | Passed / cleaned | 4 / 2 | Failed: initial return shape errors; worker model aliases rejected by ledger tracing |
| a2 | Baseline | 681.359 | Passed / cleaned | 4 / 2 | Failed: initial typed-note errors; coordinator usage could not be reconciled |

All eight worker outcomes reached cleaned state, and the supervisor independently
reran each final immutable oracle. The pilot required conforming native worker
returns, not only eventual code success. Existing ledger validation confirmed
typed-note errors in b2 and a2; b1 also returned invalid commit-hash fields.
Follow-up turns include artifact correction, so their count alone does not prove
a new ledger retry was required. This pilot leaves that turn/attempt workload
accounting unreconciled instead of inventing attempt IDs or omitting the turns.

Native usage normally carried two representations per inference. For the first
three trials the supervisor proved their ordered counter equality, then passed
only content-free native `last_token_usage` records to the existing collector.
Counting both forms would double the total. In a2 the coordinator had 54 native
events and 52 provider records, so its usage remains unknown. Each physical actor
is counted once, including follow-up turns. These are provider token counters,
including cached input, not billing amounts or stable proxies.

**Result: incomparable.** Four task successes and zero fully conforming workflow
results do not establish improved economy. The bounded reporter suppresses
variant medians, repeat ranges, and paired deltas because of workflow failures,
unreconciled attempt accounting, and missing usage. This small fixture establishes
specific failure evidence; it does not establish general model quality.

The host CLI automatically added a trial repository trust entry. For every
trial the supervisor proved that removing only that entry restored the exact
original configuration SHA-256; no other configuration change was retained.
Private metadata summaries, source digests, native-to-ledger identity checks,
and the bounded comparison report live under the ignored local
`.planning-policy/evaluations/planning-purpose-evidence/` directory. No native
conversation is bundled. Elapsed time covers the coordinator, workers,
acceptance, integration, and worker cleanup; supervisor export and outer
synthetic-repository cleanup are excluded.

Concurrent guidance repairs were subsequently integrated from `68efbd5`.
They are outside these pinned live comparisons; the combined final source has
repository verification but no additional live trial. Claude remains unverified.

## Narrow forward cases

Dependency and restart coverage now has a separate [complex trial](complex-trial.md).
The local test exercises real ledger/Git seams with deterministic executors.
No additional live trial has been run; the pilot result above remains unchanged.

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

For an explicitly authorized writable-root acceptance, use a separate-process
synthetic producer with an explicit durable root, then give a fresh consumer
only the returned reference envelope. Require exact digest and plan recovery.
This is storage-contract coverage, not a live clear-context UI claim; a
read-only host continues to use the inline case above.
