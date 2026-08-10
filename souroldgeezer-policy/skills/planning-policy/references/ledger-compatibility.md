# Legacy Ledger Compatibility

Load only when resuming or managing an existing v1/v2 record.

Version 2 is resume-only. `init-v2` returns
`blocked:contract_migration_required`; existing records keep their plan hashes,
retry behavior, transitions, closeout, retention, and byte-compatible state.
Missing pre-closeout commit/helper fields receive in-memory empty defaults;
inspection never writes them.

Unversioned version-1 plans are inspection-only (`contract_version: 1`,
`dispatch_ready: false`). Existing ledgers remain mutable under
`retry_policy: legacy_unbounded`; its terminal `integrated` state is unchanged
and does not gain `cleaned`.
Do not approve new v1 work—initialize a separate v3 run.

Listing and collection never rewrite v1 state. All-integrated receives 30-day
retention; all-discarded/superseded receives 7 days; other nonterminal state is
active. Preserve an ambiguous terminal mixture. Explicit legacy purge requires
the exact plan ID; there is no bulk deletion. Remove compatibility only in a
later contract-major release after no active version-1 ledger remains.
