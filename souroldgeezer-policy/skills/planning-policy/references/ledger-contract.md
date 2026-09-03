# Parent Ledger Contract

This is the exception-only reference for ledger errors, legacy resumption,
diagnosis, retention operations, and ledger authoring or audit. Normal
version-5 execution follows each command's bounded live `next` result and uses
read-only `show --next-only` after a long pause or context compaction. The
ledger records lifecycle facts; it does not approve a plan, select a model, or
replace the executable-plan validator.

## Runtime reference

This part reconstructs the runtime mechanics when a live result reports an
error or full diagnosis is required. Successful v5 lifecycle commands state
their next legal action from the post-command checkpoint. A fresh parent uses
`show --run-id <uuid4> --next-only`, not this section, for low-cost normal
rehydration. "Authoring and audit reference" below carries the unabridged
mechanical detail, including how the ledger enforces state legality in code.

### Isolation, authority, and initialization

Only one parent writes a run. Its isolated ledger directory is
`<git-common-dir>/planning-policy/ledgers/<plan-id>/<run-id>/`, where `plan-id`
is the stable approved-plan identifier and `run-id` is the contractually
canonical lowercase UUID4. A delegated leaf returns one `bounded-step-return-v1`
object to the parent and never mutates the ledger. Independent leaves may run concurrently only when their dependencies
are already `cleaned` and they do not share a worktree or write path — except
that an in-batch dependency on an earlier-listed same-batch member satisfies
readiness at `ready`, `in_progress`, or `completed`, since a batch shares one
worktree; an external dependency still requires `cleaned`. Each step
has exactly one current attempt at a time.

The binding a parent must construct before calling `init-v5` is
`planning-capability-binding-v1`: it joins the canonical plan digest, every
leaf, its declared `capability_requirements`, selected host/executor, and
bounded evidence. It joins every assignment to exactly one declared leaf by
`step_id`: every leaf has exactly one assignment, no assignment names an
unknown leaf, and a duplicate `step_id` is rejected; a returned
`agent_id`/`attempt_id` pair is checked against that one step's own current
identity, not for uniqueness across assignments — a shared batch-worker
`agent_id` across member assignments is legal. An assignment records the stable `agent_id`, a helper-generated
bounded opaque `attempt_id`, its first attempt count (`1`), tier, and
worktree; it cannot replace the plan's portable tier or worktree owner.

At initialization the parent stores a canonical approved-plan copy and its
lowercase 64-hex-character SHA-256 hash. Every version-2/3/4/5 lifecycle command
compares the supplied or stored plan hash with that copy before changing or
trusting state. A missing copy, hash mismatch, or changed leaf contract is
`blocked:plan_tampered`; do not dispatch, retry, or silently reinitialize it.

Every new version-5 run also stamps `retry_policy: escalating_remediation_v1`.
It retains the resolved binding with each assigned step. An assignment change
requires an exact re-binding before the step can become ready; otherwise stop
`blocked:capability_unavailable`, never silently substitute or downgrade.

### Driving transitions and validate --closeout

`init-v5` requires `--plan-id`, the approved version-5 plan, the complete
assignment set, and an exact capability-binding file. It rejects a non-UUID4 run
ID, a plan that is not `dispatch_ready`, an unavailable capability, or an existing
`<plan-id>/<run-id>` directory. Its success result's `next` block states the
ready steps and the first legal command; treat that live block, not this
paragraph, as authoritative for what to run next.

All lifecycle commands require the same `--run-id` after `init-v5` returns it:
`transition`, `show`, and `validate`. Parent mutations use `--actor parent`.
`transition` names a `--step-id` and a `--to` target status; it checks that
exactly one attempt is current and records a bounded reason plus an optional
safe relative evidence path. A step may move to `ready` from `pending`,
`blocked`, or `failed`, provided every dependency is already `cleaned` (an
in-batch dependency on an earlier-listed same-batch member instead needs only
`ready`, `in_progress`, or `completed`), the
attempt limit is not exhausted, and — for a retry — the call passes `--retry`;
any other starting status rejects the move. A step may move to `in_progress`
only from `ready`. A step may also move to `pending` from `in_progress`: this
is the batch unwind, legal only for a batch member, and only when a
same-batch member has already stopped at `blocked`, `failed`, or `oversized`.
It refunds the member's attempt count and clears its `agent_id` and
`attempt_id`, since the member never ran; the stopped member itself
remediates through the normal retry path in its same assigned worktree,
because that shared worktree still holds the completed prefix its dependents
need, and an unwound follower later redispatches as an ordinary single step in
that same worktree. Before a `blocked` or `abandoned` close, unwind any
in-progress, un-returned batch members this way first — `close` itself is
unchanged and still refuses `in_progress` work. Moving to `integrated` or `cleaned` additionally requires a
bounded `planning-worktree-result-v1` from the Git-policy helper matching the
expected prior status (`completed` for `integrated`, `integrated` for
`cleaned`); the ledger stores the returned commit, rebased/integrated commit,
and bounded helper-result evidence without changing `bounded-step-return-v1`.
Any other `--to` value is rejected. These per-status checks are dedicated,
hardcoded logic in the script (not the legacy `TRANS` lookup table described
under "State machine and legal transitions" below), so a `transition` call's
own error or success result is the authoritative statement of whether a given
move is legal right now.

A completed batch member becomes eligible to integrate only once no sibling
member can still commit to their shared worktree — none is still active, and
no `blocked`/`failed` sibling retains a retry — because a batch integrates its
one shared tip once. The parent passes the same `--worktree-result` artifact to
each member's `--to integrated` and `--to cleaned` call; a member's
`integrated` check accepts either the plain returned-commit match, or a
`batch_source_commits` entry mapping that member's `step_id` to its
`returned_commit`, when the artifact carries one. One integrate artifact and one cleanup artifact — both
carrying `batch_source_commits` for a batch — validate every member this way,
so the closeout order is: integrate every member, then clean every member. The
artifact's optional `rebased_tree_changed` flag states whether the rebase
changed the tree: `false` means a leaf's already-recorded acceptance evidence
stands; `true` means the parent re-runs only that leaf's own scoped acceptance
— never the plan's full final verification, which still runs exactly once, at
closeout.

For a version-5 run, successful transitions add bounded live guidance:
`ready` names the `in_progress` command; `in_progress` names the agent and
attempt to await; `integrated` names cleanup; and `cleaned` names newly
unblocked pending steps plus the first ready command, or `validate --closeout`
when every step is cleaned. These results are derived after the checkpoint is
written and do not alter v1 or policy-less v2/v3 output.

`validate` checks the plan copy/hash, assignment join, dependency order,
current-attempt uniqueness, and attempt limits before handoff. `validate
--closeout` additionally fails — by raising an error, not by returning a
result with a `next` field — while any successful step is only `completed` or
`integrated`; every successful step must reach `cleaned` before a closeout
validation can pass. A successful v5 closeout validation names the completed
run `close` command in its bounded `next` block.

### Bounded step return

Each return is exactly one JSON object of at most 8 KiB with `schema` exactly
`bounded-step-return-v1`, a stable `step_id`, the helper-generated bounded
opaque `attempt_id`, and an `agent_id` string of 1 through 128 characters. Its
`status` is exactly one of `completed`, `blocked`, `failed`, or `oversized`. It
contains:

- `changed_paths`: at most 32 unique, safe repository-relative paths of at
  most 240 characters (no absolute path or `..` segment), each inside the
  leaf's approved `write_set`.
- `acceptance`: the exact plan `acceptance_command` (at most 480 characters),
  an integer or `null` `exit_code`, and a `summary` of at most 480 characters.
  Its optional `evidence_path` and `sha256` appear as a pair: the path is safe
  and repository-relative (at most 240 characters), and the hash is exactly 64
  lowercase hexadecimal characters.
- `blockers`: at most 8 objects, each with `code`, a `summary` of at most 240
  characters, and the optional paired `evidence_path`/`sha256` evidence fields
  above. `notes`: at most 8 objects whose `type` is exactly one of `finding`,
  `decision_needed`, `residual_risk`, `untouched`, or `verification_limit`, and
  whose message is at most 480 characters;
  `unstarted_remainder`: at most 8 stable leaf IDs or bounded parent actions,
  each at most 240 characters.
- `commit_hash`: empty, or exactly 40 or 64 lowercase hexadecimal characters.

The return does not list `run_id`; the required lifecycle `--run-id` matches it
to ledger state. No return includes raw logs, credentials, or an unbounded
transcript. A `completed` return requires `acceptance.exit_code: 0`. A return
requires a non-empty `commit_hash` only when `changed_paths` is non-empty, on
every status, so changed work is always attributable to a commit. A failed
acceptance must be `failed`, never completed. Each `blocked`, `failed`, and
`oversized` return requires at least one blocker, and `oversized` also requires
a non-empty `unstarted_remainder`. The parent computes and records the progress
fingerprint after validating these invariants.

If changed paths, a failed acceptance result, or the return show that the
assigned task/boundary/read/write sets no longer bound the work, mark the step
`oversized`. Preserve the bounded evidence and return it to the parent; do not
split, broaden, or retry it under the same leaf. Prefer stopping before any edit,
so an `oversized` return normally carries no `changed_paths`; a leaf that only
proves oversized mid-work either commits the finished slice into `commit_hash` or
reverts clean, leaving nothing uncommitted for the parent to find. A leaf blocked
for missing load-bearing information reports `blocked:missing_input`; it does
not discover or invent the missing decision.

### Ancestry-preserving worktree closeout

Load the Git-policy-owned
[planning worktree closeout](../../git-workflow-policy/references/planning-worktree-closeout.md)
procedure and ingest each successful helper result. Leave a cleanup failure at
`integrated` so it can be retried. Create a dependent leaf's worktree only
after its prerequisites are cleaned, from the then-current parent tip.

A terminal non-completed leaf — `oversized`, or an unretryable `blocked`/`failed`
— still owns a worktree. Close it out too: from the bounded return, integrate the
committed partial slice or discard it, then remove worktree and branch without
force. No terminal leaf is left undisposed.

### Run closure and reopening

Every new version-5 checkpoint records `run_status: active`, with `outcome`,
`closed_at`, and `purge_after` null. `close --actor parent --run-id <id>
--outcome <completed|blocked|abandoned>` changes it to `run_status: closed` and
sets the other three fields. A completed close requires every step to be
`cleaned`. A blocked close requires a bounded obstruction reason and refuses
`ready` or `in_progress` work. An abandoned close requires a bounded reason,
refuses `in_progress` work, and changes pending or assigned-but-unstarted work
to `discarded`. Closed runs refuse step transitions and returned handoffs.

`reopen --actor parent --run-id <id> --reason <bounded-reason>` is limited to a
blocked run whose retention period has not elapsed and which still has at least
one retryable pending, blocked, or failed step below its attempt limit. Reopen
clears the terminal lifecycle fields and returns the run to `active`; it does
not assign or start an attempt. A dependency is ready-compatible only after it
is `cleaned`. A successful v5 `reopen` result names its retryable step IDs and
the first ready/remediation command. `close` is terminal and emits no `next`.

`close --series-handoff-file <path>` exists only on a plan carrying a
`series` block: it is required on a `completed` close of a non-final slice
(the error names the flag), optional on a `blocked`/`abandoned` close of a
non-final slice, and forbidden — as is the flag itself — on the final slice
or on a plan with no `series` block. The ledger composes the run-level
`planning-series-handoff-v1` artifact from the parent-supplied content file
plus the closing run's own identity; see [plan series](plan-series.md) for
the full close/handoff mechanics and the init-v5 predecessor cross-check.

### Listing, retention, and deletion

`list` scans either the bounded `--plan-id` scope or the ledger root and emits
bounded run summaries plus counts. `gc [--dry-run]` reports bounded `kept`,
`eligible`, `removed`, and `invalid` groups; mutation requires `--actor parent`.
Active runs are always kept regardless of age. Closed version-2/3/4 runs retain
completed outcomes for 30 days, blocked outcomes for 90 days, and abandoned
outcomes for 7 days. The boundary is exact: a run becomes eligible at
`purge_after`, not one second earlier. Initialization and successful closure run
garbage collection after validating candidate directories. A stamped series
handoff survives `reopen` unchanged; a later `close --series-handoff-file`
overwrites it atomically, so the latest close's artifact is the one retention
and `gc` see, while prior digests stay in the preserved event log.

`purge --actor parent` deletes exactly one closed target: use `--plan-id` plus
`--run-id` for version 2, or `--plan-id` plus `--legacy` for one terminal
version-1 ledger. Before `purge_after`, deletion additionally requires both
`--before-retention` and a bounded `--reason`. There is no clear-all command.

Scanning never follows or removes a symlink. An unknown schema, malformed
checkpoint, unexpected directory content, invalid plan/run identity, or
ambiguous legacy terminal state is reported in `invalid` and preserved. A v2
run directory contains only `checkpoint.json`, `events.jsonl`, `plan.json`, and
the optional validated `returns/` and `worktree-results/` trees; conservative
validation wins over age.

## Authoring and audit reference

Everything below remains true and unabridged; it is no longer required
reading for a normal in-flight v5 run because lifecycle JSON results and
`show --next-only` state the applicable action live instead of this document
restating it ahead of time — exactly the prose-drifts-from-code
risk `tests/planning_return_contract_parity_test.py`'s own docstring documents
for the `bounded-step-return-v1` contract. Read this section when authoring or
auditing `planning_ledger.py` itself, when reconstructing the full mechanics
for a rare edge case, or when resuming a legacy v1/v2 ledger.

### State machine and legal transitions

Successful steps move `completed` → `integrated` → `cleaned`. The `TRANS`
table in `references/scripts/planning_ledger.py` is **not** the general state
machine — its keys equal `V1_STATES` exactly, and it has exactly one call
site, `transition1()`, reached only when `--run-id` is absent (the legacy
version-1 path; version-1 also allows `superseded`, which the v2+ state set
drops). For a version-2/3/4 run, `transition2()` never reads `TRANS`: it
validates each move through dedicated hardcoded per-status checks (via
`advance()`), and `V2_STATES` adds `cleaned` and `oversized` on top of the v1
set. See "Driving transitions and validate --closeout" above for the v2–v5
mechanics; a v1 `transition` call's own result is the authoritative statement
of what `TRANS` permits from a given status.

### `show` output shape

`show --run-id <uuid4> --step-id <id>` returns only that step; without
`--step-id`, it returns the bounded run summary. It emits one machine-readable
bounded summary: plan/run IDs, plan hash, contract version, aggregate counts,
and for each included step only its ID, status, current attempt, agent ID,
progress fingerprint, and short reason. A summary field is at most 480
characters. If records are omitted, it sets `truncated: true` and a
non-negative `omitted_count`; it never substitutes raw event history for the
omitted records.

`show --run-id <uuid4> --next-only` is the read-only v5 rehydration lane. It
returns one deterministic highest-priority category and first command, with a
120-proxy-token `next` block and a 240-proxy-token whole envelope. Priority is:
cleanup integrated work; integrate completed work; remediate eligible
failures; ready unblocked pending work; dispatch ready work; await active
returns; validate closeout; then report terminal blockage or closure. It uses
the same dependency, attempt, and retry predicates as mutation. Full `show`
remains unchanged as the at-most-1,200-token diagnostic fallback, especially
when its wide summary reports truncation. Version 1 and policy-less v2/v3 reject
`--next-only` without migration.

### Retry policy, remediation, and terminal precedence

The step-wide attempt count starts at 1 and may never exceed the leaf's
version-2/3/4 `max_attempts` (1 through 5). The parent assigns each attempt a
helper-generated bounded opaque `attempt_id` (an implementation may use UUID4),
which the returned handoff echoes with the same `step_id` and `agent_id`; an
agent cannot borrow another step's remaining attempts. Under
`escalating_remediation_v1`, the ledger is the sole retry owner. It may retry
only an exact `failed:acceptance` return or `blocked:needs_higher_tier`; every
other outcome is ineligible. An exact `failed:acceptance` gets at most one
same-tier retry total, and only after bounded remediation. A
`blocked:needs_higher_tier` escalates immediately. Later eligible retries use a
higher mapped tier, may skip tiers, and stop at `deep` and `max_attempts`.

Before creating a new current attempt, the ledger persists one bounded
`retry-remediation-v1` artifact under the run. It binds `step_id`, prior
`attempt_id`, the prior-return digest, diagnosis, action, reuse or fresh mode,
next agent/host, target tier, and optional paired evidence. It records
the current tier, whether the same-tier retry has been used (`same-tier-used`),
the current assignment, and the remediation digest. Remediation cannot change
the approved worktree, task, boundary, read/write sets, or identity semantics.
The progress fingerprint is the SHA-256 of the canonical bounded return facts
for the attempt, excluding volatile timestamps. The terminal precedence is repeated
result (`blocked:no_progress`), then ineligible outcome, exhaustion
(`blocked:retry_exhausted`), then tier ceiling; none creates another attempt.

`record-return`'s own result states retry eligibility, target tier, and
terminal precedence for the specific step and outcome it just recorded; treat
that live `next` block as authoritative over this narrative summary. No other
command emits this.

### Tracing

Version-4 checkpoints contain no usage or trace field. Only an explicit request
loads the separate usage-tracing procedure and creates `usage/` metadata outside
the checkpoint. It follows the same retention and purge safeguards; ordinary
`show` remains trace-free unless tracing was initialized.

### Legacy and version compatibility

Policy-less existing v2/v3 checkpoints and all version-1 ledgers retain
their existing behavior. `init-v2` returns
`blocked:contract_migration_required`; stored version-2 plans remain
`resume_ready: true` and keep their original hashes and byte-compatible records.

When resuming a v1 or v2 record, load
[legacy ledger compatibility](ledger-compatibility.md); never rewrite it merely
to inspect or migrate it.
