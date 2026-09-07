# Approval handoff

Load before presenting an executable plan for approval, or when the parent
resumes it after context clearing. A validation claim or prose summary cannot
replace its decision-complete JSON. Keep worker missing-assignment stops intact.

1. Finish and validate the v5 contract. Prefer saving its exact JSON, when the
   host permits preparatory plan writes, at the resolved persistent
   `<git-common-dir>/planning-policy/plans/<sha256>/plan.json`. The parent owns
   that artifact; these helpers never save, initialize a ledger, or manage
   retention. Never request a host-mode exception just to save it: use inline
   JSON when plan writes are unavailable.
2. Run `validate PLAN --emit-handoff reference` for the saved file, or
   `validate - --emit-handoff inline` with the complete JSON on stdin. Extract
   the successful result's `handoff`, run `resolve-handoff -` with that envelope,
   and require success before presenting approval. Keep the envelope **inside**
   the host-carried approval plan, alongside the human explanation. Codex uses
   the final `<proposed_plan>`; Claude uses the plan document presented through
   `ExitPlanMode`. Earlier messages, tool outputs, and session variables do not
   satisfy this requirement.
3. After approval, resolve the carried envelope again before capability binding,
   worker assignment, or ledger initialization. Use the returned exact `plan`;
   approval recovery does not grant dispatch readiness or additional authority.

Claude command forms:

```text
uv run python ${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py validate PLAN --emit-handoff reference
uv run python ${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py validate - --emit-handoff inline
uv run python ${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py resolve-handoff HANDOFF
```

Codex uses the same commands with `<skill-dir>` replaced by the absolute source
directory of the loaded skill:

```text
uv run python <skill-dir>/references/scripts/validate_plan_contract.py validate PLAN --emit-handoff reference
uv run python <skill-dir>/references/scripts/validate_plan_contract.py validate - --emit-handoff inline
uv run python <skill-dir>/references/scripts/validate_plan_contract.py resolve-handoff HANDOFF
```

`PLAN` and `HANDOFF` accept `-` for stdin. An emitted envelope has exactly
`schema: planning-approval-handoff-v1`, `plan_sha256`, and **one** of absolute
`plan_path` or complete `plan`. Digests use the existing canonical plan hashing
(sorted keys, compact separators, ASCII JSON escaping); formatting changes do
not change identity. The digest binds content, not provenance or user approval.
Only approval-ready v5 plans emit/resolve; plain legacy validation stays unchanged.

Reference emission resolves relative input filenames to absolute paths. A
reference must name a regular file outside resolved `/tmp`, `/var/tmp`,
`/dev/shm`, `/run/user`, the system temporary root, and absolute configured
`TMPDIR`/`TEMP`/`TMP` roots. Stdin and devices are ineligible references. Choose
inline mode if the only available file is temporary. Plan canonical bytes are
bounded at 64 KiB; envelopes at 4 KiB for reference and 68 KiB for inline. The
CLI additionally bounds raw envelope input at 68 KiB and raw plan-file input at
256 KiB, allowing whitespace without unbounded reads. Emit compact envelopes.

Both commands are read-only. Resolution returns `{plan, validation}` only after
schema, digest, limits, and approval-readiness checks. Errors return no partial
plan: missing/unrecoverable input is `blocked:missing_input`; digest mismatch is
`blocked:plan_tampered`. Exit codes are 0 success, 1 contract/digest failure,
2 I/O, JSON, or CLI usage failure. Resolve does not bind capabilities.

## Parent recovery of older handoffs

An explicitly supplied complete raw v5 plan can be validated and used within its
recorded approval. An explicitly identified existing run uses its authoritative
ledger and `show --next-only`; do not initialize duplicate work.

If neither is supplied, inspect at most three same-task candidates from documented
local plan roots (the persistent plans directory above or an explicitly named
host plan directory), **or** one explicitly linked prior session. Accept only
exact recorded JSON with its matching recorded validation digest and unambiguous
task identity and approval. Do not execute transcript code, reconstruct decisions
from prose, broadly crawl sessions, or relax worker assignment fields. Ambiguous,
missing, or exhausted evidence stops `blocked:missing_input` naming the needed
artifact. A different digest stops `blocked:plan_tampered`. Ask for the exact
artifact only after this bounded parent recovery is unavailable or unsuccessful.
