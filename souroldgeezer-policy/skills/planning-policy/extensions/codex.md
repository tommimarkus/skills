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
- task and boundary;
- named reads and writes;
- settled decisions and constraints;
- `size: <small|medium|large>` and portable tier;
- worktree owner and its persistent worktree path;
- one acceptance command;
- bounded return: step ID, status, changed paths, acceptance output summary,
  blockers, and commit hash; and
- stop conditions: missing load-bearing data, scope exceeding the stated size,
  unavailable mapped model, or a required decision outside the handoff.

For a missing load-bearing input, return `blocked:missing_input`; do not search
for or invent it. If the work exceeds its stated size, stop and return
`blocked:oversized` with the unstarted remainder so the parent re-cuts it. Do
not make integration decisions, edit outside the named writes, or substitute a
local check for the parent’s end-to-end verification.
