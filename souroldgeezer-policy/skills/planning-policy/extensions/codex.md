# Codex execution adapter

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

This applies the official [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model): Luna suits efficient high-volume work, Terra balances capability and cost, Sol is the frontier tier, and `medium` is the balanced reasoning starting point while higher effort is for demonstrated reasoning gains. It is a settled repository mapping, not a claim that every host account exposes every model.

If the selected mapping is unavailable, do not silently downgrade it. Return
`blocked:model_unavailable` with the requested tier/model/effort and the host's
availability evidence; the parent reassigns the step or executes it locally.

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
- stop conditions: missing load-bearing data, scope exceeding the stated size,
  unavailable mapped model, or a required decision outside the handoff.

For a missing load-bearing input, return `blocked:missing_input`; do not search
for or invent it. If the work exceeds its stated size, stop and return
`blocked:oversized` with the unstarted remainder so the parent re-cuts it. Do
not make integration decisions, edit outside the named writes, or substitute a
local check for the parent’s end-to-end verification.

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
objects of `{ "code": string, "summary": string, "evidence_path": string,
"sha256": string }`; each summary is at most 240 characters, paths are safe
and repository-relative, and digests are 64-hex. Blocker codes carry semantics
such as `blocked:missing_input`. `notes` has at most eight `{ "type": string,
"message": string }` objects; type is exactly `finding`, `decision_needed`,
`residual_risk`, `untouched`, or `verification_limit`. `unstarted_remainder`
has at most eight strings of at most 240 characters. `commit_hash` is an empty
string or a 40- or 64-hex hash. Keep the serialized object at most 8 KiB.

Use `completed` only after the assigned acceptance command exits `0`; completed
work with changed paths needs a commit hash. `blocked`, `failed`, and `oversized`
each require a blocker; `oversized` also requires an unstarted remainder. Stop
with the applicable blocker code, preserve unstarted work, and do not make a new
decision. The parent interprets the bounded return and owns integration and
final verification.
