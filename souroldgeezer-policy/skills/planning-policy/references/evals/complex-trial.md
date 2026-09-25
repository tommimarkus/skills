# Complex planning trial

This on-demand procedure adds dependency coverage to the narrow forward cases.
It does not extend the approved two-leaf pilot or authorize live provider calls.

## Local evidence

`tests/planning_policy_complex_eval_test.py` drives a four-leaf fork/join
through real ledger CLI processes and Git worktrees. It checks readiness,
shared-decision transport, restart discovery, return preflight, integration,
cleanup, and the external oracle. Its deterministic executors contain fixture
solutions; this establishes plumbing behavior, not model planning quality.

## Fresh-coordinator trial

For a separately authorized live trial, pin the policy revision, host and exact
coordinator/worker mappings, fixture/oracle digests, attempt/time limits, and
an explicitly writable persistent evaluation root before dispatch. Missing
capabilities stop the trial; no substitute model or inferred approval.

Copy only `tests/planning_policy_complex/fixture/` into an isolated Git
repository under that root. Give a fresh coordinator its `task.md` and repository
path, without a prewritten plan, fixture solutions, oracle source or target
score. Keep the oracle outside worker writes. The coordinator derives cohesive
outcomes and obtains normal approval before dispatch. Do not force file-per-leaf
decomposition to obtain a passing graph score: lack of a fork/join means this
trial did not exercise that path, not that a cohesive single leaf is invalid.

Workers receive generated packets plus named files. After a prerequisite is
cleaned, restart the coordinator with only the approval envelope and run identity;
use `show --next-only` to resume. Retain each original return and correction
as separate observed evidence. Do not normalize a return or invent an attempt
for formatting repair. Run the immutable oracle at parent closeout.

As a separate negative trial, omit the duplicate-ID policy from the task's
requirements. The coordinator must request that decision before approval;
neither the oracle nor a worker may supply the missing policy. Report this
negative trial by rubric; the positive oracle is not its grader.

## Offline report

From the pinned policy source, run:

```text
uv run python scripts/planning_policy_complex_eval.py --trial-root ABSOLUTE_TRIAL --plan-id PLAN --run-id UUID --observations-file OBSERVATIONS
```

The command makes no model call and collects no telemetry. It executes the
external task oracle and reads the specified ledger and Git status. `passed`
requires task success, a completed/cleaned run, a clean repository, and fork/join
coverage. It does not certify native worker conformance or observed recovery.

The optional at-most-4-KiB observations JSON has exactly four fields, each
nullable: `first_attempt_handoff_acceptance` counts first submitted returns
accepted unchanged; `worker_rediscovery` counts observed worker requests or
searches for already supplied shared decisions; `parent_repairs` counts parent
edits to submitted worker results; `interruption_recovery` is a boolean for the
observed coordinator restart. The counts are nonnegative integers. Record
unknown as `null`, never zero; omitted observations remain unknown. The caller
must retain evidence for these assertions; the grader cannot authenticate them.
Compare these separately from task success, workflow state and ledger attempts.
No token or model-quality improvement follows from a local passing test.
