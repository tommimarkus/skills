# Opt-In Usage Tracing

Load this procedure only after an explicit request to trace token usage,
measure one run, or calibrate its forecast. Ordinary planning and execution do
not inspect telemetry, write usage state, install hooks, call a network, or
contact a provider.

For one active version-3 run, the parent uses the already-resolved ledger helper:

```text
... --plan-id <plan-id> trace-init --actor parent --run-id <run-id>
... --plan-id <plan-id> trace-record --actor parent --run-id <run-id> --usage-file <summary.json>
... --plan-id <plan-id> trace-show --actor parent --run-id <run-id>
... --plan-id <plan-id> trace-close --actor parent --run-id <run-id>
```

`trace-record` accepts one at-most-4-KiB `planning-usage-summary-v1` object with
exactly: `schema`, `run_id`, `step_id`, `attempt_id`, `actor`, `stage`,
`harness`, `model`, `input_tokens`, `output_tokens`, and `total_tokens`.
Stages are `prepare`, `implement`, `validate`, `integrate`, `final_verify`, or
`unknown`. Parent records use `step_id: parent` and `attempt_id: run`; worker
records must match the current ledger step/attempt and harness. Counters are
non-negative integers and total equals input plus output.

Never include prompts, completions, messages, arguments, results, raw logs, or
other content. Usage metadata lives under the run's `usage/` directory, outside
`checkpoint.json`. It is absent until `trace-init`, follows the run's existing
retention and exact-target purge safeguards, and cannot be added after
`trace-close`.

`trace-show` returns an at-most-600-proxy-token
`planning-usage-advisory-v1` aggregation by attempt cycle and stage. Keep
provider-measured counters separate from stable-proxy and declared-model-token
lanes. Compare observation with forecast only when units and harness/model
provenance are compatible; otherwise report the comparison as indeterminate.
Drift and reserve findings are advisory and never affect validity, readiness,
dispatch, retry selection, or lifecycle.
