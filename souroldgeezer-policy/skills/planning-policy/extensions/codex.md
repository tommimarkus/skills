# Codex execution adapter

## Standard workflow

Follow the shared authority check: clear settled implementation proceeds within
its authorized outcome. When approval is required, use native Plan mode when
active/exposed; otherwise present the readable plan and wait for explicit
approval without claiming a mode change. Delegate when its benefit earns the
cost, using `spawn_agent` with a self-contained assignment and
`fork_turns: "none"`. Use supported host defaults unless the task requires a
particular capability. Concurrent writers get separate persistent worktrees.
A required independent reviewer is a fresh read-only assignment; do not give it
builder reasoning. Use host notifications instead of busy-polling.

Follow the shared [assignment and return](../references/core-workflow.md#standard-assignment-and-return),
[review](../references/core-workflow.md#independent-review), and
[approval/recovery](../references/core-workflow.md#approval-and-output) rules.
Standard has no v5 packet, tier-map requirement, ledger, or exact JSON return.
Explicit managed requests, approved v5 plans, and existing packets instead use
the managed sections below. Malformed managed input blocks; never downgrade it.

## Managed execution only

The remaining sections apply only to strict or existing managed v5 execution.
They add host mechanics to the [strict workflow](../references/strict-workflow.md).

This additive adapter does not replace the portable handoff contract.

Include the shared **Execution economics** line only when requested; do not
invent missing ranges. Normal dispatch never enables or inspects tracing.

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

Versions 1–4 are retired; retained pre-v5 runs are handled per
[ledger compatibility](../references/ledger-compatibility.md).

## Capability resolution

Before **every** initial or retry dispatch, resolve every leaf's
`capability_requirements` against the active Codex host and selected executor.
The baseline `plan-step-base-v1` and every additional `tool`, `skill`,
`service`, `permission`, and `runtime` requirement need current host evidence.
Create or use the exact `planning-capability-binding-v1` whose plan digest,
step ID, executor, and requirements exactly join the approved plan; do not
reuse a binding for a different executor or attempt assignment.

If the baseline or any additional requirement cannot be evidenced, stop before
dispatch with `blocked:capability_unavailable`; do not silently substitute,
drop, defer, or probe for a replacement capability.

## Dispatch and model mapping

When the host exposes delegation, use `spawn_agent` for each ready, independent
step. Give concurrent writers separate persistent worktrees. Set
`fork_turns: "none"` for every mapped agent so it begins with the handoff rather
than inherited conversation context. The parent keeps decomposition,
integration, and end-to-end verification.

For mapped runs and explicit pins, use this table:

| Portable tier | Codex model and reasoning effort |
|---|---|
| `plan-step-mechanical` | `gpt-5.6-luna` / `low` |
| `plan-step-standard` (default) | `gpt-5.6-terra` / `medium` |
| `plan-step-analytical` | `gpt-5.6-sol` / `high` |
| `plan-step-deep` | `gpt-5.6-sol` / `xhigh` |

This follows the official [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model). It is a repository mapping, not a claim that every account exposes every model.

For workers, reviewers, and retries, apply
[new-run executor selection](../references/strict-workflow.md#new-run-executor-selection).
Mapped initialization uses `init-v5 --host codex --evidence ...`.
Pass the generated `prompt` from `dispatch` to the agent unchanged, appending host facts
only. Launch the steps a `next` block lists in `concurrent` together
(concurrent `spawn_agent` calls in the same turn).

A `batch` dispatches once: one `spawn_agent` call with ordered member handoffs.
`dispatch` on the first member starts every member in listed order and returns
one packet per member. The worker commits
each, runs its acceptance through `run-acceptance`, and returns one `bounded-step-return-v1` per member. A member
whose acceptance fails only for an environmental reason (for example a sandbox
blocks a test) commits its work, returns `blocked` / `blocked:environment`, and
the worker continues to the next member; any other stop halts the batch at the
first stop. The parent marks unrun followers `transition --to pending`,
remediates the stopped member in the same worktree, dispatches followers singly,
and lands the batch once every member is completed or terminal. An
environment stop follows the
[ledger contract](../references/ledger-contract.md) environment-stop rule.

Mapped per-leaf verification uses `spawn_agent` with `fork_turns: "none"` once per
`verify-handoff` packet group, passing the packet unchanged: `gpt-5.6-terra` /
`medium` for mechanical and standard builds, `gpt-5.6-sol` / `high` for
analytical and deep builds, as named by `verifier_tier`. Never pass builder
context. Every selected reviewer follows the same
[verifier procedure](../references/verify-handoff.md).

Parent review, including each target the `task` names, precedes `record-return`;
after a verifier pass, use the [ledger contract](../references/ledger-contract.md)
`record-verify --parent-review` lane.

If a required mapping or pin is unavailable, do not silently downgrade it:
return `blocked:model_unavailable` with tier/model/effort and availability evidence.

## Ledger-owned retry remediation

The ledger alone decides retry eligibility and the target portable tier. A retry
handoff contains only bounded `retry-remediation-v1` material: prior-return
digest, diagnosis and action, reuse or fresh executor mode, next agent/host,
target portable tier, and optional paired evidence. It does not expose raw
history or a host transcript.

Mapped retries use the table; explicit-assignment retries follow the shared
selection rule. Preserve the ledger-selected tier, attempt cap, and reuse/fresh
decision. An unavailable required executor returns `blocked:model_unavailable`.
An agent needing more reasoning returns `blocked:needs_higher_tier`
with bounded evidence; it never selects its retry. Repairable stops (`blocked:environment`, or any
stop amended after its return) retry at the same tier; only reasoning stops
escalate. A wrong write/read set, acceptance command, or attempt cap is not
retried: the parent runs `amend`.

## Required handoff

Call the host mechanism with a prompt containing all of the following:

- stable step ID and dependency IDs;
- run ID, step ID, agent ID, and attempt ID;
- v5: exact resolved binding `planning-capability-binding-v1` (plan digest,
  step requirements, selected executor);
- task and boundary;
- for v5, the assigned work unit's cohesive outcome and `decomposition` context:
  `shape: single` only, or the required `basis` and `rationale` for
  `parallel`/`checkpointed`;
- named reads and writes, which with the packet form the worker's read budget;
- settled decisions and constraints;
- `size: <small|medium|large>` and portable tier;
- worktree owner and its persistent worktree path;
- one acceptance command, run only through `run-acceptance` (see [worker handoff](../references/worker-handoff.md));
- the `bounded-step-return-v1` profile below; and
- any ledger-supplied bounded `retry-remediation-v1` material, without raw
  history; and
- stop conditions: missing load-bearing data, scope exceeding the stated size,
  unavailable mapped model, unavailable required capability, or a required
  decision outside the handoff.

Pair bindings with plan/step/attempt identity; reject a missing or
mismatched binding as `blocked:capability_unavailable` without probing.

For a missing load-bearing input, return `blocked:missing_input`; do not search
for or invent it. If the work exceeds its stated size, stop and return the
status `oversized` — a status value, not a `blocked:` code — with the unstarted
remainder so the parent re-cuts it. Do not make integration decisions, edit
outside the named writes, or substitute a local check for the parent’s
end-to-end verification.

For ledger-backed v5 assignments and local return preflight, follow
[worker handoff](../references/worker-handoff.md).

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
`residual_risk`, `untouched`, `verification_limit`, or `extra_read`. `unstarted_remainder`
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
final verification. For every successful leaf `land` runs the Git-policy
helper and ingests its bounded result through
`completed` → `integrated` → `cleaned`; the parent dispatches dependents once
each prerequisite is `integrated`, from a worktree based on the
current parent tip.
It uses rebase plus fast-forward integration, never a routine cherry-pick.
