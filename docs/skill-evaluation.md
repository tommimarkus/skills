# Skill Evaluation Evidence

Use this guide to choose and record evidence for a skill change. Keep the files
one hop from `SKILL.md`; load them only for changes to triggers, workflow
behavior, model-family extensions, source grounding, or high-risk rejection
gates.

| What changed | Evidence to prepare |
|---|---|
| When the skill should activate | [Trigger cases](#trigger-cases), including a positive and a negative case |
| What the skill should do or refuse | [Behavior cases](#behavior-cases), with required and forbidden outcomes |
| A model or runtime needs an exception | [Model pressure](#model-pressure), showing why generic wording failed |
| A trace, issue, or review informed a rule | [Source grounding](#source-grounding), recording the lesson and bundling decision |

Apply [source hygiene](#source-hygiene) to every artifact. The formats below
describe expected activation and behavior for Claude Code and Codex without
choosing an eval runner. The repository report checks that the evidence files
exist and meet its structural rules; an external harness or grading agent must
execute the cases against their rubric or grader. A structural pass alone is
not behavioral evidence.

See the [contributor guide](contributing.md) for repository workflow and the
[skill architecture standard](skill-architecture.md) for the conditions that
require this evidence.

## Source Hygiene

Evaluation artifacts are repo-authored evidence, not mirrors of benchmark
repositories or vendor docs.

- Prefer synthetic prompts derived from observed failure modes.
- Link external source material by URL or local path; do not copy third-party
  prompt text, examples, code, fixtures, tables, schemas, diagrams, logos, or
  screenshots.
- Use original paraphrase when recording a lesson from a source.
- Set `contains_third_party_text` to `false` for cases that are safe to bundle.
- If a case cannot be made safe without copying protected material, keep only a
  URL reference in `references/source-grounding.md` and do not add it to JSONL.

## Trigger Cases

Path: `references/evals/trigger-cases.jsonl`.

Each line is one JSON object:

```json
{"id":"api-design-trigger-yes-001","prompt":"Design a POST endpoint for order creation.","expected_activation":true,"reason":"Direct HTTP API build request.","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
```

Required fields:

- `id`: stable local case identifier.
- `prompt`: synthetic or originally paraphrased user prompt.
- `expected_activation`: boolean.
- `reason`: why the skill should or should not activate.
- `source_kind`: `synthetic`, `local-trace`, `issue`, `review`, `runbook`, or
  another narrow provenance label.
- `source_url`: URL or local path when the case comes from a source; empty for
  synthetic cases.
- `ip_handling`: short source-hygiene note.
- `contains_third_party_text`: must be `false` for bundled cases.

A trigger pack needs at least one `expected_activation: true` case and one
`expected_activation: false` case.

## Behavior Cases

Path: `references/evals/behavior-cases.jsonl`.

Each line is one JSON object:

```json
{"id":"api-design-behavior-001","prompt":"Review a route handler for missing problem+json errors.","expected_artifacts":["per-finding report"],"required_checks":["load the API reference","cite file evidence"],"forbidden_behaviors":["claim runtime SLI evidence from static code"],"grader":"rubric: output cites evidence and separates static from runtime verification","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
```

Required fields:

- `id`: stable local case identifier.
- `prompt`: synthetic or originally paraphrased task prompt.
- `expected_artifacts`: non-empty list of outputs the skill should produce.
- `required_checks`: non-empty list of checks the agent must perform.
- `forbidden_behaviors`: non-empty list of behaviors that should fail the case.
- `grader`: deterministic check, rubric, or manual review note.
- `source_kind`, `source_url`, `ip_handling`,
  `contains_third_party_text`: same meaning as trigger cases.

For a stochastic evaluator, establish an observed noise envelope with at least
two runs over unchanged pinned input before treating a score delta as evidence;
movement inside that envelope is noise. Change only one variable per scored
comparison, and match every other recorded condition between the baseline and
the subject run.

## Model Pressure

Path: `references/evals/model-pressure.md`.

Use this only when a model-family or runtime-specific extension exists because
generic wording failed. Record the pressure prompt, tested runtime/model,
observed failure, accepted extension, retest, and merge-back condition.

## Fixed workflow-evidence pilot

Planning-policy has one approved, opt-in synthetic pilot for comparing its
guidance. The parent uses
`scripts/planning_policy_workflow_report.py --manifest PATH --output PATH` to
summarize at most sixteen content-free trial records. Each record is capped at
64 KiB; the JSON report is capped at 16 KiB. The reporter is Python 3.11
stdlib only and never discovers telemetry, dispatches work, or contacts a
provider.

The manifest is `planning-policy-workflow-manifest/v1` with pinned Git
`revisions` (`baseline` and `candidate`) and `trials`. A trial
has a unique `trial_id`, `baseline` or `candidate` variant, sequence, fixture
and oracle SHA-256 values, its variant's `policy_revision`, host/profile,
coordinator and available worker model
mapping, the fixed limits (two worker leaves, four worker attempts, 15 minutes),
content-free source path/digest summaries, coordinator/worker actor summaries
(including step/attempt identities, actual model/effort, worker tier, and
`coverage_complete`), an explicitly reconciled `roster_complete`, worker leaf/attempt, failed
attempt, retry, escalation, and dispatch counts, and execution outcome,
lifecycle, oracle, and elapsed-time evidence. Unknown counters and elapsed time
remain `null`. Usage keys are input/output/cached-input/total tokens. Supplied
source paths/digests identify private metadata summaries; the caller verifies
them and reconciles the actor roster with native spawn and ledger identities.
The reporter validates those supplied facts; it cannot discover omitted actors
or authenticate a caller's asserted coverage.
For a worker reused at the same model/effort, list later ledger-issued identities
in optional `additional_attempt_ids`; its usage covers all listed attempts once.
Unrecorded or reused retry identities leave the actor accounting unreconciled.

The report preserves failed and blocked trials. It reports medians, baseline
repeat ranges, and paired deltas only when every trial has complete actor usage,
matching conditions, a passed oracle, a completed outcome, and cleaned
lifecycle. Otherwise it marks the comparison incomparable. It rejects malformed
records, duplicate/conflicting trial or actor identities, and any
limit outside the approved bounds.
Oracle states are `passed`, `failed`, `not_run`, or `unknown`; failures stay
visible. Record order in the report preserves validated trial sequence, and
shared revisions and model mappings are stored once. The reporter bounds its
input read before JSON parsing and rejects oversized output without writing it.

## Complex planning coverage

Planning-policy's [complex trial procedure](../souroldgeezer-policy/skills/planning-policy/references/evals/complex-trial.md)
adds shared decisions, dependent work, a fork and join, and restart evidence.
Its offline grader separates immutable task-oracle results, ledger lifecycle,
dependency coverage, and observer-supplied worker behavior. Local integration
tests use deterministic executors; they are not live planning-quality or
token-economy measurements.

## Source Grounding

Path: `references/source-grounding.md`.

Use this when a skill encodes lessons from real traces, issues, reviews,
runbooks, or correction history. A useful entry names:

- source URL or local path,
- source type,
- lesson extracted in original wording,
- bundled material decision: `idea-only`, `paraphrase-with-citation`, or
  `URL-only`,
- licence or trademark note when relevant.
