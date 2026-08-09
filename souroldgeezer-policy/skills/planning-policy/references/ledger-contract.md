# Parent Ledger Contract

Read this only when a valid, approved version-2 plan has two or more delegated
leaves and the parent is about to initialize or resume its durable ledger. The
ledger records lifecycle facts; it does not approve a plan, select a model, or
replace the executable-plan validator.

## Isolation, authority, and initialization

Only one parent writes a run. Its isolated ledger directory is
`<git-common-dir>/planning-policy/ledgers/<plan-id>/<run-id>/`, where `plan-id`
is the stable approved-plan identifier and `run-id` is a UUID4. A delegated leaf
returns one `bounded-step-return-v1` object to the parent and never mutates the
ledger. Independent leaves may run concurrently only when their dependencies
are already complete and they do not share a worktree or write path; each step
has exactly one current attempt at a time.

`init-v2` requires `--plan-id`, `--run-id`, the approved version-2 plan, and
the complete assignment set. It rejects a non-UUID4 run ID, a plan that is not
`dispatch_ready`, or an existing `<plan-id>/<run-id>` directory. It joins every
assignment to exactly one declared leaf by `step_id`: every leaf has exactly one
assignment, no assignment names an unknown leaf, and duplicate `step_id` or
`agent_id`/attempt collisions are rejected. An assignment records the stable
`agent_id`, its first `attempt_id` (`1`), tier, and worktree; it cannot replace
the plan's portable tier or worktree owner.

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
`show --run-id <uuid4> --step-id <id>` returns only that step; without
`--step-id`, it returns the bounded run summary. `validate` checks the plan
copy/hash, assignment join, dependency order, current-attempt uniqueness, and
attempt limits before handoff or closeout.

An attempt starts at 1 and may never exceed the leaf's version-2
`max_attempts` (1 through 5). The parent and the returned handoff identify the
same `step_id`, `agent_id`, and `attempt_id`; an agent cannot borrow another
step's remaining attempts. A retry needs a bounded reason, safe relative
evidence path when evidence exists, and a new progress fingerprint. The
progress fingerprint is the SHA-256 of the canonical bounded return facts for
the attempt, excluding volatile timestamps. If its value is unchanged from the
previous attempt, reject the retry as `blocked:no_progress`. Once an attempted
step reaches `max_attempts` without completion, mark it terminal
`failed:retry_exhausted` and do not create another current attempt.

If changed paths, a failed acceptance result, or the return show that the
assigned task/boundary/read/write sets no longer bound the work, mark the step
`oversized`. Preserve the bounded evidence and return it to the parent; do not
split, broaden, or retry it under the same leaf. A leaf blocked for missing
load-bearing information reports `blocked:missing_input`; it does not discover
or invent the missing decision.

## Bounded step return

Each return is exactly one JSON object of at most 8 KiB with `schema` exactly
`bounded-step-return-v1`, a stable `step_id`, positive integer `attempt_id`,
and an `agent_id` string of 1 through 128 characters. Its `status` is exactly
one of `completed`, `blocked`, `failed`, or `oversized`. It contains:

- `changed_paths`: at most 32 unique, safe repository-relative paths of at
  most 240 characters (no absolute path or `..` segment), each inside the
  leaf's approved `write_set`.
- `acceptance`: the exact plan `acceptance_command` (at most 480 characters),
  an integer `exit_code` from 0 through 255, and a `summary` of at most 480
  characters; optional `evidence_path` is a safe repository-relative path of
  at most 240 characters and optional `sha256` is exactly 64 lowercase
  hexadecimal characters.
- `blockers`: at most 8 non-empty typed blocker codes of at most 120
  characters; `notes`: at most 8 objects whose `type` is 1 through 64
  characters and whose message is at most 480 characters;
  `unstarted_remainder`: at most 8 stable leaf IDs or bounded parent actions,
  each at most 240 characters.
- `commit_hash`: empty, or exactly 40 or 64 lowercase hexadecimal characters.

No return includes raw logs, credentials, or an unbounded transcript. A
`completed` return requires `acceptance.exit_code: 0` and a non-empty commit
hash; a failed acceptance must be `failed`, never completed. `blocked` and
`oversized` returns each include at least one typed blocker; `failed` and
`oversized` returns preserve their typed reason. The parent computes and records
the progress fingerprint after validating these invariants.

`show` emits one machine-readable bounded summary: plan/run IDs, plan hash,
contract version, aggregate counts, and for each included step only its ID,
status, current attempt, agent ID, progress fingerprint, and short reason. A
summary field is at most 480 characters. If records are omitted, it sets
`truncated: true` and a non-negative `omitted_count`; it never substitutes raw
event history for the omitted records.

## Version-1 compatibility

An unversioned version-1 plan remains inspection-compatible only. Its validator
and ledger summary emit `contract_version: 1`, `dispatch_ready: false`, and a
deprecation warning that migration to version 2 is required before new
dispatch. Existing version-1 state may be shown or closed with its legacy
commands, but may not start a new delegated attempt or be converted in place;
initialize a separate version-2 `<plan-id>/<run-id>` run after approval.

Remove this compatibility path only in a later published contract-major change,
after the migration has been documented and no active version-1 ledger remains.
