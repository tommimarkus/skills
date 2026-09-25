# Codex execution adapter

This additive adapter does not replace the portable handoff contract.

Include the shared **Execution economics** line verbatim; do not invent missing
ranges. Normal dispatch never enables or inspects tracing.

Before approval, put the resolved `planning-approval-handoff-v1` envelope inside
`<proposed_plan>`; resolve again before dispatch and follow
[approval handoff](../references/approval-handoff.md). Writable storage alone is
not permission.

## Live lifecycle

For new work, the parent uses `init-v5` and consumes each successful v5 command's live `next` result and runs
the stated command. After dispatch it waits for a host notification that the
assigned return is available; it does not busy-poll, start an autonomous loop,
or enable telemetry. After a 24-hour pause or context compaction, call
`show --run-id <uuid4> --next-only` once and continue from that bounded result.
Load the full ledger reference only for an error, legacy resumption, diagnosis,
retention work, or ledger authoring/audit.

Version 1–4 plans and ledger state are resume-compatible only. New `init-v4`
is refused as `blocked:contract_migration_required`; existing v4 records remain
resumable and mutable. Do not initialize new work from them or translate their
handoffs into a new v5 plan assignment.

## Capability resolution

For v4–v5, before **every** initial or retry dispatch, resolve every leaf's
`capability_requirements` against the active Codex host and selected executor.
The baseline `plan-step-base-v1` and every additional `tool`, `skill`,
`service`, `permission`, and `runtime` requirement need current host evidence.
Create or use the exact `planning-capability-binding-v1` whose plan digest,
step ID, executor, and requirements exactly join the approved plan; do not
reuse a binding for a different executor or attempt assignment.

If the baseline or any additional requirement cannot be evidenced, stop before
dispatch with `blocked:capability_unavailable`; do not silently substitute,
drop, defer, or probe for a replacement capability. This is distinct from
`blocked:model_unavailable`, which applies only when the already selected
model/effort mapping is unavailable.
For a ledger-confirmed v1–v3 resume, preserve that version's dispatch contract:
do not require or synthesize capability requirements or a binding. New work
still starts from v5.

## Dispatch and model mapping

When the host exposes delegation, use `spawn_agent` for each ready, independent
step. Give concurrent writers separate persistent worktrees. Set
`fork_turns: "none"` for every mapped agent so it begins with the handoff rather
than inherited conversation context. The parent keeps decomposition,
integration, and end-to-end verification.

Use this settled mapping:

| Portable tier | Codex model and reasoning effort |
|---|---|
| `plan-step-mechanical` | `gpt-5.6-luna` / `low` |
| `plan-step-standard` (default) | `gpt-5.6-terra` / `medium` |
| `plan-step-analytical` | `gpt-5.6-sol` / `high` |
| `plan-step-deep` | `gpt-5.6-sol` / `xhigh` |

This follows the official [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model). It is a repository mapping, not a claim that every account exposes every model.

A `batch` dispatches once: one `spawn_agent` call with ordered member handoffs.
In listed order, each member gets `transition --to ready` then `--to in_progress`
to mint its attempt before running. The worker commits each, runs its acceptance
command, and returns one `bounded-step-return-v1` per member, stopping at the
first stop. The parent marks unrun followers `transition --to pending`,
remediates the stopped member in the same worktree, dispatches followers singly,
and integrates once with helper `--batch-commit` when every member is completed
or terminal.

If the selected mapping is unavailable, do not silently downgrade it. Return
`blocked:model_unavailable` with the requested tier/model/effort and the host's
availability evidence; the parent reassigns the step or executes it locally.

## Ledger-owned retry remediation

The ledger alone decides retry eligibility and the target portable tier. A retry
handoff contains only bounded `retry-remediation-v1` material: prior-return
digest, diagnosis and action, reuse or fresh executor mode, next agent/host,
target portable tier, and optional paired evidence. It does not expose raw
history or a host transcript.

Retries use the mapping above. Honor the ledger-selected tier and executor;
the parent and agent never change them. If unavailable, return
`blocked:model_unavailable` with target tier/model/effort and availability
evidence. An agent needing more reasoning returns `blocked:needs_higher_tier`
with bounded evidence; it never selects its retry.

## Required handoff

Call the host mechanism with a prompt containing all of the following:

- stable step ID and dependency IDs;
- run ID, step ID, agent ID, and attempt ID;
- v4–v5: exact resolved binding `planning-capability-binding-v1` (plan digest,
  step requirements, selected executor); v1–v3 resume: no binding;
- task and boundary;
- for v5, the assigned work unit's cohesive outcome and `decomposition` context:
  `shape: single` only, or the required `basis` and `rationale` for
  `parallel`/`checkpointed`; a v1–v4 resume uses its versioned work unit shape;
- named reads and writes;
- settled decisions and constraints;
- `size: <small|medium|large>` and portable tier;
- worktree owner and its persistent worktree path;
- one acceptance command;
- the `bounded-step-return-v1` profile below; and
- any ledger-supplied bounded `retry-remediation-v1` material, without raw
  history; and
- stop conditions: missing load-bearing data, scope exceeding the stated size,
  unavailable mapped model, unavailable required capability, or a required
  decision outside the handoff.

Pair v4–v5 bindings with plan/step/attempt identity; reject a missing or
mismatched binding as `blocked:capability_unavailable` without probing. The
parent labels v1–v4 assignments as ledger-confirmed resumes; workers never
reinterpret them as new v5 work.

For a missing load-bearing input, return `blocked:missing_input`; do not search
for or invent it. If the work exceeds its stated size, stop and return the
status `oversized` — a status value, not a `blocked:` code — with the unstarted
remainder so the parent re-cuts it. Do not make integration decisions, edit
outside the named writes, or substitute a local check for the parent’s
end-to-end verification.

## Generated assignment and return preflight

For ledger-backed v5 work, follow [worker handoff](../references/worker-handoff.md)
to generate the assigned packet after `in_progress`. Send the packet unchanged,
including `plan_context` with objective, scope and all shared approved decisions.
The packet's `return_schema` supports host structured output. Workers run the
read-only `validate-return` command before submitting; the parent still uses
`record-return` to reject a stale attempt. Digest consistency grants no approval.

## Bounded step return

Every assigned agent returns exactly one UTF-8 JSON object with
`"schema": "bounded-step-return-v1"`; no Markdown, prose outside the object, or raw logs.
Its required fields are `step_id`, `agent_id`, `attempt_id`, `status`,
`changed_paths`, `acceptance`, `blockers`, `notes`, `commit_hash`, and
`unstarted_remainder`. `step_id`, `agent_id`, and `attempt_id` exactly echo the
helper-generated assignment value. The parent supplies `run_id`
when it ingests the return; the return itself does not carry `run_id`.

`status` is exactly `completed`, `blocked`, `failed`, or `oversized`.
`changed_paths` has at most 32 safe repository-relative paths. `acceptance` is
`{ "command": string, "exit_code": integer|null, "summary": string,
"evidence_path"?: string, "sha256"?: string }`: command exactly echoes the
assigned command, summary is at most 480 characters, and an evidence path is
safe and repository-relative with a 64-hex digest. `blockers` has at most eight
objects of `{ "code": string, "summary": string, "evidence_path"?: string,
"sha256"?: string }`; each summary is at most 240 characters, and the evidence
pair is optional — a safe repository-relative path with its 64-hex digest, or
neither, as `oversized` and `blocked:missing_input` return. Blocker codes carry
semantics such as `blocked:missing_input`. `notes` has at most eight `{ "type": string,
"message": string }` objects; type is exactly `finding`, `decision_needed`,
`residual_risk`, `untouched`, or `verification_limit`. `unstarted_remainder`
has at most eight strings of at most 240 characters. `commit_hash` is an empty
string or a 40- or 64-hex hash. Keep the serialized object at most 8 KiB.

Use `completed` only after the assigned acceptance command exits `0`; completed
work with changed paths needs a commit hash, as does any other status with
changed paths. `blocked`, `failed`, and `oversized`
each require a blocker; `oversized` also requires an unstarted remainder. Prefer
stopping before any edit; otherwise commit the finished slice into `commit_hash`
or revert clean — never leave edits uncommitted. Stop
with the applicable blocker code, preserve unstarted work, and do not make a new
decision. The parent interprets the bounded return and owns integration and
final verification. For every successful leaf it ingests the Git-policy
helper's bounded result through `completed` → `integrated` → `cleaned`, and
only then dispatches dependents from a worktree based on the current parent tip.
It uses rebase plus fast-forward integration, never a routine cherry-pick.
