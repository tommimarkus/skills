# Approval handoff

1. Validate v5. Check host instructions: writable storage is not write authority.
   When preparatory writes are permitted, prefer the primary
   checkout's already-ignored `.planning-policy/plans`, or an explicitly supplied
   persistent root. Never edit ignores/configuration, probe alternate locations,
   request escalation, or choose temporary storage. If writes are prohibited or
   no eligible root is available, go directly to inline without a write probe.
2. Invoke the writer with that absolute root. It validates
   before creating state, atomically publishes canonical JSON at
   `ROOT/<sha256>/plan.json`, verifies it, and returns the reference envelope.
   Only exit 2 with `blocked:persistence_unavailable` permits validated inline
   fallback after storage failure; disclose it briefly.
   Invalid input, unsafe paths, altered contracts, and CLI usage errors block.
3. For inline, pass the complete plan to `validate - --emit-handoff inline`
   and extract `handoff`. Require successful `resolve-handoff` before approval.
   Put the envelope **inside** the host approval plan,
   after the readable human plan: Codex's final `<proposed_plan>` or Claude's
   document presented through `ExitPlanMode`. Earlier messages, tool outputs,
   and session variables do not suffice.
4. Resolve again after approval, before binding, assignment, or ledger init.
   Use the returned exact `plan`; recovery grants
   neither dispatch readiness nor additional authority. Preparatory persistence
   is not implementation and changes no sandbox or Plan mode permissions.

Claude commands:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/persist_plan.py" --plan-root "ABSOLUTE_ROOT" "PLAN"
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py" validate - --emit-handoff inline
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py" resolve-handoff "HANDOFF"
```

Codex replaces `<skill-dir>` with the loaded skill's absolute source directory:

```text
python3 -B "<skill-dir>/references/scripts/persist_plan.py" --plan-root "ABSOLUTE_ROOT" "PLAN"
python3 -B "<skill-dir>/references/scripts/validate_plan_contract.py" validate - --emit-handoff inline
python3 -B "<skill-dir>/references/scripts/validate_plan_contract.py" resolve-handoff "HANDOFF"
```

Python 3.11 standard library only: no Git, installation, network, or host config
writes; `-B` suppresses bytecode. Existing `uv run python` forms remain compatible
where permitted. `validate PLAN --emit-handoff reference` emits a saved file's
absolute reference read-only. `PLAN` and `HANDOFF` accept `-` for stdin.

## Contract

The envelope has exactly `schema: planning-approval-handoff-v1`, `plan_sha256`,
and **one** absolute `plan_path` or complete `plan`. Canonical hashing uses sorted
keys, compact separators, ASCII escaping; formatting is irrelevant. Digests bind
content, not provenance/approval. Emission/resolution require approval-ready v5;
legacy validation is unchanged.

References require regular files outside resolved `/tmp`, `/var/tmp`, `/dev/shm`,
`/run/user`, the system temporary root, and absolute `TMPDIR`/`TEMP`/`TMP` roots.
Stdin/devices cannot be references. Limits: raw plan input 256 KiB, canonical
plan 64 KiB, reference envelope 4 KiB, inline envelope and raw envelope input
68 KiB. Errors return no partial plan.

The writer rejects symlink storage components and nonregular targets. New
files/directories are private where supported; existing permissions stay intact.
Existing publications are reused only after validation and exact canonical-byte
comparison, never overwritten. Staging stays beneath the supplied root; handled
failures clean only this invocation's staging. Preserve saved plans until explicit
cleanup; never initialize a ledger.

Read-only resolution returns `{plan, validation}` after
schema/digest/limit/readiness checks, without binding. Missing
input is `blocked:missing_input`; changed digests are `blocked:plan_tampered`.
Validator/resolver exits: 0 success, 1 contract/digest failure, 2 I/O/JSON/usage
failure. Exit 2 alone never authorizes fallback.

## Older handoffs

Validate a supplied complete raw v5 plan within its recorded approval. For an
identified run, use its ledger's `show --next-only`; never initialize a duplicate.

Otherwise inspect at most **three total** same-task candidates across preferred,
legacy `<git-common-dir>/planning-policy/plans`, or explicitly named host roots,
**or** one explicitly linked session. Existing references need no migration.
Accept only exact JSON with a
matching recorded validation digest and unambiguous task identity and approval.
Never execute transcript code, reconstruct prose, crawl sessions broadly, or
relax worker fields. Missing/ambiguous/exhausted evidence stops
`blocked:missing_input`; a changed digest stops `blocked:plan_tampered`.
Ask for the exact artifact only after bounded recovery fails or is unavailable.
