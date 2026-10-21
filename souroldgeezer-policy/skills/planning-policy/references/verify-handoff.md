# Verifier handoff

Portable procedure for the read-only verifier of one completed leaf. The
parent runs `verify-handoff` and `record-verify`; the verifier sees only the
generated `planning-verify-handoff-v1` packet (at most 16 KiB) and never the
builder's notes, logs, or reasoning. The packet carries `schema`,
`packet_sha256`, `plan_id`, `run_id`, `plan_sha256`, `step_id`, `attempt_id`,
`agent_id`, `verify_id`, `verifier_tier`, `task`, `boundary`,
`settled_decisions`, `write_set`, `acceptance_command`, `cohesive_outcome`,
`acceptance_exit_code`, `base_commit`, `returned_commit`, `budget`,
`changeset`, `outside_write_set`, and `return_schema`. A retry's packet also carries `prior_verify`
(`verify_id`, `rejected_commit`, `findings`).

## Inputs and reads

Work from the packet alone. Read the diff `base_commit..returned_commit` and at
most 8 surrounding files that the diff touches or depends on. You may run at
most one targeted probe (for example a single `grep` or one focused read-only
command) when a check cannot be settled by reading. Never edit, stage, or
commit, and never re-run the test suite or the acceptance command; the packet's
`acceptance_exit_code` is the recorded result.

## Five checks

1. Task coverage: every part of `task` is done.
2. Settled decisions: each entry of `settled_decisions` is respected.
3. Silent removal: no behavior, rule, test, or assertion was removed without
   the task asking for it.
4. Scope creep: no unrequested change inside the write set. For each
   `outside_write_set` path (committed outside the write set under standard
   precision), reject only when the task did not require it;
   `outside_write_set_count` above the list length means the list is truncated.
5. Acceptance: the acceptance command actually exercises the change.

## Rejection gate

Reject only on a finding that cites `path:line` (or the path alone when no line
applies) and the contract clause it breaks. Suspicion without such support is a
`notes` entry, or `inconclusive` when it blocks a check entirely. Style,
naming, and alternative designs never block.

Finding codes: `verify:coverage` (check 1), `verify:decision` (check 2),
`verify:regression` (check 3), `verify:scope_creep` (check 4),
`verify:acceptance_gap` (check 5).

## Re-verification

With `prior_verify` present, check the delta since `rejected_commit` and each
prior finding (fixed, or still present); do not re-review unchanged hunks.

## Batches

A batch gets one verifier dispatch. Give one verdict per member commit, in
member order, each as its own return object.

## Return

Return one `bounded-verify-return-v1` object (at most 4 KiB) and nothing else:
`schema`, `step_id`, `verify_id`, `verdict` (`pass`, `reject`, or
`inconclusive`), `findings` (at most 8, each with `code`, `path`, `line` or
null, `clause`, and a `summary` up to 240 characters), and `notes` (at most 8
strings up to 240 characters). A `reject` needs at least one finding; a `pass`
has none. Preflight it, read-only, before returning:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" validate-verify-return --handoff-file PACKET --return-file RETURN
python3 -B "<skill-dir>/references/scripts/planning_ledger.py" validate-verify-return --handoff-file PACKET --return-file RETURN
```

Claude substitutes `${CLAUDE_SKILL_DIR}`; Codex resolves `<skill-dir>` to the
loaded skill's source directory. The parent alone ingests the verdict.
