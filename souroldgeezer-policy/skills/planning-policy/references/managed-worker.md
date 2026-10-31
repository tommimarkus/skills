# Managed worker execution

Load only after the entrypoint selects strict or existing managed execution.
The role instructions in the selected `plan-step-*` entry still apply.

For a generated `planning-worker-handoff-v1` packet, preserve its shared
`plan_context` decisions and use its `return_schema`. Follow the shared
[worker handoff procedure](worker-handoff.md)
for read-only return validation before submitting. The packet never grants
additional authority, and the parent remains responsible for current-attempt
validation and integration.

Before any inspection or tool use, establish the assigned contract version.
Assignments use v5. Require the exact resolved
`planning-capability-binding-v1` with the plan digest, this `step_id`, assigned
executor, and `capability_requirements`, alongside the assigned plan/step/attempt
identity. If it is missing or does not exactly match, return
`blocked:capability_unavailable`; do not probe for, substitute, drop, or defer a
replacement capability. The mechanical role intentionally has no `Skill` tool;
an additional `skill` requirement cannot be fulfilled by granting a new tool.

Before work, require the step's task and boundary, size band, named inputs and
prior decisions, acceptance check, and return shape. Also require the
assigned work unit's `cohesive_outcome` and `decomposition` context. If a required field is missing, stop and return `blocked:missing_input` with the missing
fields; do not proceed under an assumption.

If this is a retry, accept only the ledger-supplied bounded
`retry-remediation-v1` material. The ledger alone chose this target tier and
whether this is a reuse or fresh executor; honor both without reading raw
history or selecting another tier. If the settled task genuinely needs more
reasoning, return `blocked:needs_higher_tier` with bounded evidence so the
ledger, not you, can decide whether to retry.

Stay inside the packet's `changeset_budget`: make only the assigned task, with no
drive-by refactors, reformatting, or renames, and patch rather than regenerate.
Run `check-changeset` (see the
[worker handoff procedure](worker-handoff.md))
before returning `completed`. If the work cannot fit, stop `oversized:changeset`;
never shrink it by deleting required content.

Only mechanical and standard roles accept batches. You may be assigned an
ordered batch of members to run in one shared worktree.
Execute them in listed order; commit each member's work separately; run each
member's acceptance through `run-acceptance` with its own packet; return one
bounded return per member, echoing that member's own identities. If a
member's acceptance fails only for an environmental reason (for example a
sandbox blocks a test), commit its finished
work, return it as `blocked` / `blocked:environment`, and continue to the next
member. On any other stop (`failed`, another `blocked`, or `oversized`), stop the
batch there: return the stopped member's and the already-completed members'
returns, and do not start later members.

Run acceptance only through `run-acceptance` and return its `acceptance`
object. Stay within the packet's read budget and report other reads as one
`extra_read` note, per the [worker handoff procedure](worker-handoff.md). Your verification covers
only your own drafting; the parent session owns integration and the final check. Say
plainly what you did not check.

Return exactly one UTF-8 JSON object using `"schema": "bounded-step-return-v1"`;
no Markdown, prose outside the object, or raw logs. Echo assigned `step_id`,
`agent_id`, and helper-generated `attempt_id`; the parent supplies `run_id` at
ingestion, so do not return it. Include `status`, `changed_paths`, `acceptance`,
`blockers`, `notes`, `commit_hash`, and `unstarted_remainder`. Status is exactly
`completed`, `blocked`, `failed`, or `oversized`; blocker codes carry details
such as `blocked:missing_input`. Keep at most 32 safe repository-relative changed
paths, eight blockers, eight typed notes, and eight remainder strings. Acceptance
exactly echoes the command and carries integer/null exit code, a <=480-character
summary, and optional relative evidence path plus 64-hex digest. Every blocker
has code and a <=240-character summary; its relative evidence path and 64-hex
digest are optional and paired — supply both or neither, and omit both when the
stop has no evidence artifact, as `oversized` and `blocked:missing_input` do.
Note types are exactly `finding`, `decision_needed`, `residual_risk`, `untouched`,
`verification_limit`, or `extra_read`; remainder items are <=240 characters. `commit_hash` is
an empty string or 40/64-hex hash. Keep the return <=8 KiB. Use `completed` only
when acceptance exits `0`; completed changed work needs a commit hash, as does
any other status whose changed paths are non-empty. Blocked, failed, and
oversized returns require a blocker; oversized also needs remainder. Prefer
stopping before you change anything; when the stop only becomes clear after work
began, commit the finished slice and name it in `commit_hash`, or revert to a
clean tree and report no changed paths — never leave edits uncommitted.
Do not invent a decision. Verification is local to your drafting; the parent owns
integration and final verification.
