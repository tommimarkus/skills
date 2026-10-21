# Legacy Ledger Compatibility

Load only when resuming or managing an existing v1–v4 record.

Versions 2–4 are resume-only. `init-v2`, `init-v3`, and `init-v4` return
`blocked:contract_migration_required`; existing records keep their plan hashes,
retry behavior, transitions, closeout, retention, and byte-compatible state.
Missing pre-closeout commit/helper fields receive in-memory empty defaults;
inspection never writes them.

Versions 4 and 5 own the unchanged capability binding and re-binding contract.
A resumed v4 record remains binding-dispatchable; new v5 runs require
`planning-capability-binding-v1` to join every leaf's
`capability_requirements` to the plan digest, selected host/executor, and bounded
evidence. Existing v1–v3 ledgers do not gain a binding merely by inspection or
resume.

A retained v5 run stamped `pipeline_policy: provisional_v1` (the removed
provisional-start pipeline) still loads; with no stacked step it resumes under
integrated-or-cleaned readiness, while a step carrying `provisional_base`,
`upstream_stale`, `upstream_change`, `pending_acceptance`, or
`blocked:upstream_changed` makes every mutating command stop
`blocked:contract_migration_required` (and `show --next-only` names
`contract_migration_required`); `show`, `list`, and `gc` keep working.

Unversioned version-1 plans are inspection-only (`contract_version: 1`,
`dispatch_ready: false`). Existing ledgers remain mutable under
`retry_policy: legacy_unbounded`; its terminal `integrated` state is unchanged
and does not gain `cleaned`.
Do not approve new legacy work—initialize a separate v5 run.

Listing and collection never rewrite v1 state. All-integrated receives 30-day
retention; all-discarded/superseded receives 7 days; other nonterminal state is
active. Preserve an ambiguous terminal mixture. Explicit legacy purge requires
the exact plan ID; there is no bulk deletion. Remove compatibility only in a
later contract-major release after no active version-1 ledger remains.
