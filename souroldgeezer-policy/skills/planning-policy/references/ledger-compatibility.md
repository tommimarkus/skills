# Legacy Ledger Compatibility

Load only when resuming or managing an existing v1–v3 record.

Versions 2 and 3 are resume-only. `init-v2` and `init-v3` return
`blocked:contract_migration_required`; existing records keep their plan hashes,
retry behavior, transitions, closeout, retention, and byte-compatible state.
Missing pre-closeout commit/helper fields receive in-memory empty defaults;
inspection never writes them.

Version 4 is the forward contract. It owns capability binding and re-binding:
new v4 runs require `planning-capability-binding-v1` to join every leaf's
`capability_requirements` to the plan digest, selected host/executor, and bounded
evidence. Existing v1–v3 ledgers do not gain a binding merely by inspection or
resume.

Unversioned version-1 plans are inspection-only (`contract_version: 1`,
`dispatch_ready: false`). Existing ledgers remain mutable under
`retry_policy: legacy_unbounded`; its terminal `integrated` state is unchanged
and does not gain `cleaned`.
Do not approve new v1 work—initialize a separate v4 run.

Listing and collection never rewrite v1 state. All-integrated receives 30-day
retention; all-discarded/superseded receives 7 days; other nonterminal state is
active. Preserve an ambiguous terminal mixture. Explicit legacy purge requires
the exact plan ID; there is no bulk deletion. Remove compatibility only in a
later contract-major release after no active version-1 ledger remains.
