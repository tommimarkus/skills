# Claude Code Execution Adapter

Render the shared plan's compact **Execution economics** line without inventing
token ranges: expected/high attempts, largest repeated-context driver, declared
range or `indeterminate`, final-verification reserve, and `tracing: off`.
Normal dispatch never enables or inspects usage tracing.

Read this adapter when an approved `planning-policy` plan dispatches its steps
through Claude Code. It adds host execution details to the portable tier roster;
it does not replace the shared workflow.

## Live lifecycle

The parent consumes each successful v4 command's live `next` result and runs
the stated command. After dispatch it waits for a host notification that the
assigned return is available; it does not busy-poll, start an autonomous loop,
or enable telemetry. After a 24-hour pause or context compaction, call
`show --run-id <uuid4> --next-only` once and continue from that bounded result.
Load the full ledger reference only for an error, legacy resumption, diagnosis,
retention work, or ledger authoring/audit.

## Capability resolution

Before **every** initial or retry Agent assignment, resolve every leaf's
`capability_requirements` against the active Claude Code host, the selected
alias/effort, and that Agent's granted tools. The baseline `plan-step-base-v1`
and every additional `tool`, `skill`, `service`, `permission`, and `runtime`
requirement need current host evidence. Create or use the exact
`planning-capability-binding-v1` whose plan digest, step ID, executor, and
requirements exactly join the approved plan; do not reuse a binding for a
different executor or attempt assignment.

Claude's `plan-step-mechanical` Agent intentionally lacks `Skill`. It cannot
evidence an additional `skill` requirement: stop with
`blocked:capability_unavailable` instead of granting a tool or changing Agent
frontmatter. Apply the same evidence rule to every other missing capability;
do not silently substitute, drop, defer, or probe for a replacement capability.
This is distinct from `blocked:model_unavailable`, which applies only when the
already selected alias/effort mapping is unavailable.

Use the `Agent` tool once per decomposed step. Assign the cheapest tier that
fits and preserve these portable Claude aliases and effort values exactly:

| Tier | Model alias | Effort |
|---|---|---|
| `plan-step-mechanical` | `haiku` | `low` |
| `plan-step-standard` | `sonnet` | `medium` |
| `plan-step-analytical` | `opus` | `high` |
| `plan-step-deep` | `opus` | `xhigh` |

Pass `subagent_type` as `souroldgeezer-policy:<tier>` — Claude Code registers
plugin agents under this scoped identifier, and the bare tier name alone
returns `Agent type '<tier>' not found`.

Never substitute a versioned model identifier for an alias and never silently
downgrade a requested tier. If Claude Code cannot provide the requested alias or
effort, return `blocked:model_unavailable` with the requested tier, alias, and
effort; the parent must reassign the step or execute it locally.

Every Agent assignment includes: run, step, agent, and attempt identity; the
exact resolved binding, including its `planning-capability-binding-v1` schema,
plan digest, matching step requirements, and selected executor; task and
boundary; named inputs and prior decisions; one scoped acceptance check; size
band; return contract; and the requested tier, alias, and effort. The parent
keeps integration and the plan's final verification; an agent verifies only its
own drafting. If the work exceeds its size band, the agent stops and asks the
parent to re-cut it rather than expanding scope. If an assignment is missing a
load-bearing field, return `blocked:missing_input` with the missing fields. An
agent rejects a missing or mismatched binding as
`blocked:capability_unavailable` without probing for a replacement.

## Ledger-owned retry remediation

The ledger alone decides whether a returned attempt is eligible for retry and,
when it is, the target portable tier. A retry handoff carries its bounded
`retry-remediation-v1` material: the prior-return digest, diagnosis and action,
reuse or fresh executor mode, next agent/host, target portable tier, and any
paired evidence. It never carries raw history or a host transcript.

Map that target portable tier to the table above exactly. Do not let the parent,
an Agent, or this adapter select a different tier. Honor the ledger's reuse or
fresh executor assignment when invoking the Agent. If the exact alias/effort
mapping is unavailable, return `blocked:model_unavailable` with the target tier,
alias, effort, and availability evidence; never silently downgrade. An executor
that cannot proceed because a genuinely higher tier is required returns
`blocked:needs_higher_tier` with bounded evidence; it does not choose its retry.

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

Run `claude plugin validate --strict` through the repository validation path to
validate configured aliases and efforts. It does not establish the underlying
version that Claude Code resolves for an alias.
