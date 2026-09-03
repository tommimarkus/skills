# Successive-Plan Series

Load this reference only when a plan carries, or needs, an optional top-level
`series` block — authoring a successor slice, grooming a predecessor's
handoff into it, or closing a non-final slice. A plan without `series`
behaves exactly as documented elsewhere in this reference set; nothing here
changes it.

## What a series is

A series is a finite chain of plans that slices genuinely oversized work only
after outcome-first grooming merges microleaf candidates
(`PLANCOST-PLAN-SCALE`) into successive, separately approved plans that carry
settled decisions forward. It has a stable `series_id`, an integer `slice`
starting at 1, a `final` boolean, and `end_verification_commands` (1 to 4
bounded strings, 1–480 characters) declared once at slice 1 and copied
verbatim by every successor. Changing those commands mid-series is never a
validator error; it is a flagged re-decision the init-v5 predecessor
cross-check discloses (see below). A series is not a living backlog, roadmap,
or value ordering — it stops at its declared final slice, not when new work
occurs to someone.

Slice > 1 additionally requires a `predecessor` block of copied,
self-contained evidence: `plan_id`, `plan_sha256`, `run_id`, `outcome` (one of
`completed`, `blocked`, `abandoned`), and `handoff_sha256` (64 lowercase hex,
or `""` for a predecessor closed with no handoff). Slice 1 forbids
`predecessor`. This evidence is copied at authoring time, not resolved live;
the init-v5 cross-check below is what actually re-verifies it.

## Grooming a successor plan

When slicing a plan into a series, or authoring the next slice of an existing
one:

1. **Fold the predecessor's settled decisions into `approved_decisions`.**
   Fold means carry forward, not re-derive — a decision the predecessor
   settled stays settled. If a folded decision must change, that is a flagged
   re-decision: state it explicitly rather than silently overwriting.
2. **Re-validate the assumptions the handoff names** in
   `assumptions_to_revalidate` before relying on them; do not carry an
   assumption forward unexamined just because a prior slice recorded it.
3. **Finalize the `series` block before minting the capability binding.**
   The `series` block is inside the plan digest
   (`planning-capability-binding-v1` binds the canonical plan SHA-256), so a
   `series` field settled after the binding is minted invalidates that
   binding. Settle `series_id`, `slice`, `final`, `end_verification_commands`,
   and `predecessor` first.
4. When a predecessor closed anything other than `completed`, see "Successor
   on a blocked predecessor" below before assuming the chain is broken.

## Close and handoff mechanics (parent's point of view)

`close --actor parent --run-id <id> --outcome <outcome> --series-handoff-file
<path>` is how a completed non-final slice hands work to its successor. From
the parent's side:

- **Content file.** The parent supplies exactly four bounded content fields —
  `landed`, `decisions`, `assumptions_to_revalidate`, `remaining_scope` — each
  a list of up to 16 strings, 1–480 characters. Nothing else; the ledger
  rejects a content file that carries any other key, including identity
  fields. The ledger composes the rest (`schema`, `plan_id`, `run_id`,
  `series_id`, `slice`) itself from the closing run, so a stale or copied
  identity can never be pasted into a new close.
- **The flag requirement is exactly this matrix:**
  - No `series` block on the plan and the flag is supplied → rejected; the
    flag requires a series plan.
  - `series.final: true` and the flag is supplied → rejected; a final slice
    hands nothing on.
  - `series.final: false`, `--outcome completed`, and the flag is **not**
    supplied → rejected, naming `--series-handoff-file` in the error.
  - `series.final: false` and `--outcome blocked` or `--outcome abandoned`,
    flag not supplied → allowed; no handoff is composed. The flag stays
    optional on a non-completed close of a non-final slice.
  - `series.final: false` and the flag **is** supplied, regardless of
    outcome → the content file is read, composed, and written.
- **Composed artifact.** The ledger writes the bound
  `planning-series-handoff-v1` object as run-level `series-handoff.json`,
  capped at 8 KiB (`MAX_SERIES_HANDOFF`), atomically, with a both-or-neither
  checkpoint stamp (`series_handoff_path`, `series_handoff_sha256`); the
  digest facts also splice into the single `close-v5` event. A missing
  content file, an unparseable one, one carrying the wrong key set, or one
  whose composed artifact would exceed the cap all leave the run untouched
  and `active` — the close is refused before any lifecycle mutation happens,
  the same way the retry-artifact validation ahead of a mutation works.
- **Reopen and re-close.** `reopen` retains the artifact and its stamp. A
  later `close --series-handoff-file` on the same run overwrites the artifact
  atomically; the latest close wins for the live stamp, while the event log
  preserves the full digest lineage of every close that happened.
- **Tamper detection.** `validate_series_handoff` is the sibling of the
  retry-artifact validation: it re-verifies the on-disk artifact against the
  checkpoint stamp (path, digest, and identity) on load, so an edited or
  substituted artifact, or a stamp with no matching file, is caught rather
  than silently trusted.

## Init-v5 predecessor cross-check

For an incoming `slice > 1` plan, `init-v5` resolves
`<ledger-root>/<predecessor.plan_id>/<predecessor.run_id>` (after its normal
auto-gc) and splices exactly one disclosure key, `series_predecessor`, into
the init result. It never raises on the predecessor's account — a missing,
purged, garbage-collected, unreadable, or tampered predecessor never fails
the successor's own init. The states, checked in this order, are:

- **`matched`** — the predecessor's plan digest, outcome, handoff digest, and
  `end_verification_commands` all agree with what the successor's
  `predecessor` block claims. Proceed with grooming as normal.
- **`mismatch:plan_digest`**, **`mismatch:outcome`**,
  **`mismatch:handoff_digest`**, or **`mismatch:end_commands`** — the first
  field, in that order, that disagrees. Treat this as a flagged re-decision
  surface: the successor's authoring claimed one fact about the predecessor
  and the ledger found another. Resolve the discrepancy (fix the copied
  evidence, or explicitly re-decide) before relying on the fold in "Grooming
  a successor plan" above.
- **`unresolvable`** — the predecessor's run directory could not be resolved
  at all (gc'd, purged, missing, or malformed). This is not a block: inherit
  from the predecessor *plan* document and its `close_reason` instead, and
  disclose that the live cross-check could not confirm it.

## Successor on a blocked predecessor

A predecessor that closed `blocked` and cannot reopen (retention elapsed, or
no retryable work remains) is not a dead end for the series. Author the
successor's `predecessor` block with `outcome: "blocked"` — a blocked close
never requires `--series-handoff-file`, so `handoff_sha256` is commonly `""`
— and the cross-check reports `matched` exactly as it would for a completed
predecessor, as long as the copied evidence agrees. This is the documented
escape hatch for a dead-blocked predecessor: without a handoff to fold from,
grooming instead inherits from the predecessor's plan document and its
`close_reason`, and the successor discloses that lineage rather than
pretending a handoff exists.

## The parent's series-end obligation

A series-final plan (`series.final: true`) declares no new obligation beyond
what final verification always meant: at final-slice closeout, the parent —
in whichever runtime is driving this run — runs `end_verification_commands`
itself, once, exactly as it always runs `final_verification_commands` today.
The ledger never executes a command on the parent's behalf. Closeout-adjacent
`next` results for a series-final plan carry the compact marker `series_end:
true` in place of the inlined command list, so the bounded `next` envelope
never has to smuggle 1–4 shell commands through it. The close hint for a
completed non-final series slice instead appends
`--series-handoff-file <path>` to the suggested command, naming the one flag
this run still owes.

`list` entries for series runs additionally carry `series_id`,
`series_slice`, and `series_final`; a non-series run's `list` entry is
unchanged.
