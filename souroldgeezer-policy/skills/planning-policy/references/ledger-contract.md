# Parent Ledger Contract

Read this only when a valid, approved version-2 plan has two or more delegated
leaves and the parent is about to initialize or resume its durable ledger. The
ledger records lifecycle facts; it does not approve a plan, select a model, or
replace the executable-plan validator.

## Authority and boundary

Only the parent owns the ledger at
`<git-common-dir>/planning-policy/ledgers/<plan-id>/`. A delegated leaf returns
one `bounded-step-return-v1` object to the parent and never mutates the ledger.
The parent validates the plan before dispatch, initializes once after approval,
and is solely responsible for integration and end-to-end verification.

Use a stable `plan_id`, each plan leaf's stable `id`, and a per-leaf
`max_attempts` value from the version-2 plan. An attempt starts at 1 and never
exceeds that leaf's declared limit. A retry needs a bounded reason and evidence
path; it does not rewrite the original task, boundary, read/write sets, settled
decisions, size, tier, worktree owner, or acceptance command.

## Lifecycle

The parent uses `init` once, `transition` for a lifecycle or retry change,
`show` for a bounded rehydration summary, and `validate` before handoff or
closeout. Parent mutations use `--actor parent`. A leaf blocked for missing
load-bearing information reports `blocked:missing_input` to the parent; it
does not discover or invent the missing decision.

Persist only bounded state, summaries, typed blocker codes, evidence paths,
attempt counts, and returned commit/acceptance facts. Never persist raw agent
logs, credentials, or unbounded transcripts. If ledger state and the approved
version-2 plan disagree, stop dispatch and return the mismatch to the parent.
