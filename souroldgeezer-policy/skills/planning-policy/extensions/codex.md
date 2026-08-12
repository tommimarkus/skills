# Codex execution adapter

Render the shared plan's compact **Execution economics** line without inventing
token ranges: expected/high attempts, largest repeated-context driver, declared
range or `indeterminate`, final-verification reserve, and `tracing: off`.
Normal dispatch never enables or inspects usage tracing.

Read this additive adapter after the shared execution shape when the approved
plan will execute in Codex. It does not replace the portable handoff contract.

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

If the selected mapping is unavailable, do not silently downgrade it. Return
`blocked:model_unavailable` with the requested tier/model/effort and the host's
availability evidence; the parent reassigns the step or executes it locally.

## Ledger-owned retry remediation

The ledger alone decides retry eligibility and the target portable tier. A retry
handoff contains only bounded `retry-remediation-v1` material: prior-return
digest, diagnosis and action, reuse or fresh executor mode, next agent/host,
target portable tier, and optional paired evidence. It does not expose raw
history or a host transcript.

Map the ledger-selected target portable tier to this table exactly. Neither the
parent, this adapter, nor the spawned agent selects or changes it. Honor the
ledger's reuse or fresh executor assignment when dispatching. If the exact
mapping is unavailable, return `blocked:model_unavailable` with target
tier/model/effort and availability evidence; never silently downgrade. An agent
that discovers a real need for more reasoning returns
`blocked:needs_higher_tier` with bounded evidence; it does not select its retry.

## Required handoff

Call the host mechanism with a prompt containing all of the following:

- stable step ID and dependency IDs;
- run ID, step ID, agent ID, and attempt ID;
- task and boundary;
- named reads and writes;
- settled decisions and constraints;
- `size: <small|medium|large>` and portable tier;
- worktree owner and its persistent worktree path;
- one acceptance command;
- the `bounded-step-return-v1` profile below; and
- any ledger-supplied bounded `retry-remediation-v1` material, without raw
  history; and
- stop conditions: missing load-bearing data, scope exceeding the stated size,
  unavailable mapped model, or a required decision outside the handoff.

For a missing load-bearing input, return `blocked:missing_input`; do not search
for or invent it. If the work exceeds its stated size, stop and return the
status `oversized` — a status value, not a `blocked:` code — with the unstarted
remainder so the parent re-cuts it. Do not make integration decisions, edit
outside the named writes, or substitute a local check for the parent’s
end-to-end verification.

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
