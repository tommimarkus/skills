# Parent Ledger Contract

Read this only when a valid, approved version-3 plan has two or more delegated
leaves, or when the parent is resuming an existing version-2 ledger. The
ledger records lifecycle facts; it does not approve a plan, select a model, or
replace the executable-plan validator.

## Isolation, authority, and initialization

Only one parent writes a run. Its isolated ledger directory is
`<git-common-dir>/planning-policy/ledgers/<plan-id>/<run-id>/`, where `plan-id`
is the stable approved-plan identifier and `run-id` is the contractually
canonical lowercase UUID4. A delegated leaf returns one `bounded-step-return-v1`
object to the parent and never mutates the ledger. Independent leaves may run concurrently only when their dependencies
are already `cleaned` and they do not share a worktree or write path; each step
has exactly one current attempt at a time.

`init-v3` requires `--plan-id`, the approved version-3 plan, and
the complete assignment set. It rejects a non-UUID4 run ID, a plan that is not
`dispatch_ready`, or an existing `<plan-id>/<run-id>` directory. It joins every
assignment to exactly one declared leaf by `step_id`: every leaf has exactly one
assignment, no assignment names an unknown leaf, and duplicate `step_id` or
`agent_id`/attempt collisions are rejected. An assignment records the stable
`agent_id`, a helper-generated bounded opaque `attempt_id`, its first attempt
count (`1`), tier, and worktree; it cannot replace the plan's portable tier or
worktree owner.

At initialization the parent stores a canonical approved-plan copy and its
lowercase 64-hex-character SHA-256 hash. Every version-2/3 lifecycle command
compares the supplied or stored plan hash with that copy before changing or
trusting state. A missing copy, hash mismatch, or changed leaf contract is
`blocked:plan_tampered`; do not dispatch, retry, or silently reinitialize it.
Every new version-3 run also stamps `retry_policy: escalating_remediation_v1`.
Policy-less existing version-2 checkpoints and all version-1 ledgers retain
their existing behavior. `init-v2` returns
`blocked:contract_migration_required`; stored version-2 plans remain
`resume_ready: true` and keep their original hashes and byte-compatible records.

## Shared version-2/3 lifecycle

All lifecycle commands require the same `--run-id` after `init-v3` returns it:
`transition`, `show`, and `validate`. Parent mutations use `--actor parent`.
`transition` names a `--step-id`, checks that exactly one attempt is current,
and records a bounded reason plus an optional safe relative evidence path.
Successful steps move `completed` → `integrated` → `cleaned`. Both closeout
transitions require a bounded `planning-worktree-result-v1` from the Git-policy
helper; the ledger stores the returned commit, rebased/integrated commit, and
bounded helper-result evidence without changing `bounded-step-return-v1`.
`show --run-id <uuid4> --step-id <id>` returns only that step; without
`--step-id`, it returns the bounded run summary. `validate` checks the plan
copy/hash, assignment join, dependency order, current-attempt uniqueness, and
attempt limits before handoff. `validate --closeout` additionally fails while
any successful step is only `completed` or `integrated`.

Version-3 checkpoints contain no usage or trace field. Only an explicit request
loads the separate usage-tracing procedure and creates `usage/` metadata outside
the checkpoint. It follows the same retention and purge safeguards; ordinary
`show` remains trace-free unless tracing was initialized.

## Ancestry-preserving worktree closeout

Load the Git-policy-owned
[planning worktree closeout](../../git-workflow-policy/references/planning-worktree-closeout.md)
procedure and ingest each successful helper result. Leave a cleanup failure at
`integrated` so it can be retried. Create a dependent leaf's worktree only
after its prerequisites are cleaned, from the then-current parent tip.

Every new version-3 checkpoint records `run_status: active`, with `outcome`,
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
is `cleaned`.

The step-wide attempt count starts at 1 and may never exceed the leaf's
version-2/3 `max_attempts` (1 through 5). The parent assigns each attempt a
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

If changed paths, a failed acceptance result, or the return show that the
assigned task/boundary/read/write sets no longer bound the work, mark the step
`oversized`. Preserve the bounded evidence and return it to the parent; do not
split, broaden, or retry it under the same leaf. A leaf blocked for missing
load-bearing information reports `blocked:missing_input`; it does not discover
or invent the missing decision.

## Bounded step return

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
transcript. A `completed` return requires `acceptance.exit_code: 0`; it requires
a non-empty `commit_hash` only when `changed_paths` is non-empty. A failed
acceptance must be `failed`, never completed. Each `blocked`, `failed`, and
`oversized` return requires at least one blocker, and `oversized` also requires
a non-empty `unstarted_remainder`. The parent computes and records the progress
fingerprint after validating these invariants.

`show` emits one machine-readable bounded summary: plan/run IDs, plan hash,
contract version, aggregate counts, and for each included step only its ID,
status, current attempt, agent ID, progress fingerprint, and short reason. A
summary field is at most 480 characters. If records are omitted, it sets
`truncated: true` and a non-negative `omitted_count`; it never substitutes raw
event history for the omitted records.

When resuming a v1 or v2 record, load
[legacy ledger compatibility](ledger-compatibility.md); never rewrite it merely
to inspect or migrate it.

## Listing, retention, and deletion

`list` scans either the bounded `--plan-id` scope or the ledger root and emits
bounded run summaries plus counts. `gc [--dry-run]` reports bounded `kept`,
`eligible`, `removed`, and `invalid` groups; mutation requires `--actor parent`.
Active runs are always kept regardless of age. Closed version-2/3 runs retain
completed outcomes for 30 days, blocked outcomes for 90 days, and abandoned
outcomes for 7 days. The boundary is exact: a run becomes eligible at
`purge_after`, not one second earlier. Initialization and successful closure run
garbage collection after validating candidate directories.

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
