# Legacy Ledger Compatibility

Load only when a ledger command refuses a retained pre-v5 run, when `list` or
`gc` reports one, or when a retained v5 run lacks a newer policy stamp.

Contract versions 1–4 are retired: the ledger initializes and runs only
version-5 plans. A version-1 ledger kept `checkpoint.json` directly in its plan
directory; a version-2/3/4 run records its version as the checkpoint `schema`.
Such a run is never loaded or validated:

- Every command aimed at it — `show`, `validate`, `transition`, `dispatch`,
  `land`, `record-return`, `amend`, `handoff`, the verify commands, `close`,
  `reopen`, `purge`, and `trace-*` — refuses with
  `blocked:contract_migration_required`. Finish or close it with
  souroldgeezer-policy 2026.10.9 or earlier; never rewrite it to migrate it.
- `list` reports it minimally: `legacy: true`, its `contract_version` (null
  when unreadable), and `run_status: unsupported`.
- `gc` never deletes or rewrites it and counts it in `unsupported_count`.
- `init-v5` refuses a plan ID that holds a version-1 ledger; a new v5 run may
  sit beside a retained v2–v4 run.

Do not approve new legacy work—initialize a separate v5 run.

## Version-5 policy stamps

A retained v5 run without a newer stamp (`retry_policy`, `return_codes`,
`precision_policy`, `verify_policy`) keeps the behavior the
[ledger contract](ledger-contract.md) states for that absent stamp.

A retained v5 run stamped `pipeline_policy: provisional_v1` (the removed
provisional-start pipeline) still loads; with no stacked step it resumes under
integrated-or-cleaned readiness, while a step carrying `provisional_base`,
`upstream_stale`, `upstream_change`, `pending_acceptance`, or
`blocked:upstream_changed` makes every mutating command stop
`blocked:contract_migration_required` (and `show --next-only` names
`contract_migration_required`); `show`, `list`, and `gc` keep working.
