# Parent Ledger Contract

Read this only when a valid, approved version-2 plan has two or more delegated
leaves and the parent is about to initialize or resume its durable ledger. The
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

`init-v2` requires `--plan-id`, `--run-id`, the approved version-2 plan, and
the complete assignment set. It rejects a non-UUID4 run ID, a plan that is not
`dispatch_ready`, or an existing `<plan-id>/<run-id>` directory. It joins every
assignment to exactly one declared leaf by `step_id`: every leaf has exactly one
assignment, no assignment names an unknown leaf, and duplicate `step_id` or
`agent_id`/attempt collisions are rejected. An assignment records the stable
`agent_id`, a helper-generated bounded opaque `attempt_id`, its first attempt
count (`1`), tier, and worktree; it cannot replace the plan's portable tier or
worktree owner.

At initialization the parent stores a canonical approved-plan copy and its
lowercase 64-hex-character SHA-256 hash. Every version-2 lifecycle command
compares the supplied or stored plan hash with that copy before changing or
trusting state. A missing copy, hash mismatch, or changed leaf contract is
`blocked:plan_tampered`; do not dispatch, retry, or silently reinitialize it.

## Version-2 lifecycle

All version-2 lifecycle commands require the same `--run-id`: `init-v2`,
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

## Ancestry-preserving worktree closeout

Load the Git-policy-owned
[planning worktree closeout](../../git-workflow-policy/references/planning-worktree-closeout.md)
procedure and ingest each successful helper result. Leave a cleanup failure at
`integrated` so it can be retried. Create a dependent leaf's worktree only
after its prerequisites are cleaned, from the then-current parent tip.

Every new version-2 checkpoint records `run_status: active`, with `outcome`,
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
version-2 `max_attempts` (1 through 5). The parent assigns each attempt a
helper-generated bounded opaque `attempt_id` (an implementation may use UUID4),
which the returned handoff echoes with the same `step_id` and `agent_id`; an
agent cannot borrow another step's remaining attempts. A retry needs a bounded
reason, safe relative evidence path when evidence exists, and a new progress fingerprint. The
progress fingerprint is the SHA-256 of the canonical bounded return facts for
the attempt, excluding volatile timestamps. If its value is unchanged from the
previous attempt, reject the retry as `blocked:no_progress`. Once an attempted
step reaches `max_attempts` without completion, mark it terminal
`blocked:retry_exhausted` and do not create another current attempt.

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

When a pre-closeout version-2 checkpoint lacks returned/integrated commit or
helper-result fields, reading it supplies empty compatibility defaults; the next
mutation persists the current shape without changing its approved-plan hash.

## Listing, retention, and deletion

`list` scans either the bounded `--plan-id` scope or the ledger root and emits
bounded run summaries plus counts. `gc [--dry-run]` reports bounded `kept`,
`eligible`, `removed`, and `invalid` groups; mutation requires `--actor parent`.
Active runs are always kept regardless of age. Closed version-2 runs retain
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

## Version-1 compatibility

An unversioned version-1 plan remains inspection-compatible only. Its validator
and ledger summary emit `contract_version: 1`, `dispatch_ready: false`, and a
deprecation warning that migration to version 2 is required before new
dispatch. Existing version-1 state may be shown or closed with its legacy
commands and remains mutable under `retry_policy: legacy_unbounded`; its
terminal `integrated` state is unchanged and it does not gain `cleaned`. Current
planning-policy does not approve or dispatch an unversioned version-1 plan as
new work; initialize a separate version-2 `<plan-id>/<run-id>` run after
approval.

Lifecycle listing and garbage collection never rewrite a version-1 checkpoint
or event stream. A legacy ledger with every step `integrated` is unambiguously
completed and receives 30-day retention from its last update. A legacy ledger
whose every step is `discarded` or `superseded` receives 7-day retention. Other
nonterminal legacy ledgers remain active and age-protected. A terminal mixture
of integrated and discarded/superseded states is ambiguous: report and preserve
it rather than infer an outcome. Explicit legacy purge uses the exact plan ID;
there is no bulk legacy deletion.

Remove this compatibility path only in a later published contract-major change,
after the migration has been documented and no active version-1 ledger remains.
