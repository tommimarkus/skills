---
name: planning-policy
description: "Use when loaded repo or user guidance initializes planning-policy, or when asked to inspect, adopt, or enforce plan-first discipline and economical delegated completion — brainstorm an approach, prepare cohesive handoffs, and get it approved before implementing new feature or build work. Not for domain design, writing code, or one-off diagrams; defer to the owning design, audit, or ops skill."
---

# Planning Policy

Own plan-first enforcement only when repo/user guidance initializes this policy,
or on an explicit “plan this first” request. The standing line is authority;
installation alone is not. It protects economical delegated completion: plan
new feature/build work, prepare cohesive bounded handoffs, and obtain approval.
The parent prepares, integrates, verifies, and recovers; workers execute their
assigned outcomes and scoped acceptance.

Inputs: request, guidance, intended work, and orienting files. Evidence: source,
approved approach or blocker, and bounded footer. An unresolved domain-design
choice invokes its owning design skill before approval.

## Load map

- **Lookup / inspect:** this entry surface only. Report whether the line applies;
  do not invent an enforcement result.
- **Enforce or adopt guidance:** read
  [core workflow §enforcement](references/core-workflow.md#enforcement) and
  [§approval-and-output](references/core-workflow.md#approval-and-output).
- **Executable plan, delegation, or returned handoff:** also read
  [plan contract](references/plan-contract.md), start new plan JSON from
  [plan-v5.json](references/templates/plan-v5.json), and run the advertised
  [`validate_plan_contract.py`](references/scripts/validate_plan_contract.py)
  command before approval. For approval/recovery, [approval handoff](references/approval-handoff.md)
  selects authorized [persistence](references/scripts/persist_plan.py) (`--help`)
  or inline JSON. Resolve before approval and dispatch; carry the envelope in the
  host plan. The [binding scaffold](references/templates/capability-binding-v1.json)
  joins plan digest, leaves, requirements, executor, and evidence. For an approved
  plan with two or more
  delegated steps, the parent alone uses `init-v5`, `transition`, `record-return`, `show`,
  `validate --closeout`, `close`, `reopen`, `list`, `gc`, and `purge` commands from
  [`planning_ledger.py`](references/scripts/planning_ledger.py). For assigned workers, use the generated packet and read-only return preflight
  in [worker handoff](references/worker-handoff.md). Normal v5
  execution follows live `next` results through the lifecycle; after a long
  pause or context compaction, use `show --run-id <uuid4> --next-only` once to
  recover the next action. The ledger alone owns retry remediation and tier
  selection; approval and dispatch validation remain separate. Slicing an oversized
  plan into a successive series loads [plan series](references/plan-series.md).
- **Compatibility or audit route only:** read
  [ledger compatibility](references/ledger-compatibility.md) when inspecting or
  resuming v1–v4 state; load the retained [v3 scaffold](references/templates/plan-v3.json)
  or [v4 scaffold](references/templates/plan-v4.json) only to interpret that
  legacy plan shape. Read the [ledger contract](references/ledger-contract.md) only for
  errors, legacy resumption, diagnosis, retention operations, or ledger
  authoring/audit. Read [selective audit](references/selective-audit.md) only
  when targeted inspection leaves its bounded audit question unresolved.
- **Usage tracing (explicit opt-in only):** only after the user explicitly asks
  to trace, measure, or calibrate, read [usage tracing](references/usage-tracing.md).
  Ordinary runs never inspect telemetry,
  create trace state, install hooks, or make measurement network/provider calls.
- **Host dispatch:** read exactly one additive adapter:
  [Claude Code](extensions/claude-code.md) or [Codex](extensions/codex.md).
  If the host/mapping is unavailable, return its documented blocker; never
  silently downgrade. Re-load the other adapter only after the host changes.
- **Trigger/behavior/eval edits only:** load `references/evals/` and
  `references/source-grounding.md`.

## Enforcement

Select `enforce-initialized` for initialized guidance or an explicit request;
otherwise use `lookup`. `inspect` reports compliance and `adopt-guidance`
writes the core template. Enforcement details, host lane behavior, and the
executable-leaf contract live in the on-demand [core workflow](references/core-workflow.md).

Worker stops: missing assigned load-bearing information is `blocked:missing_input`
(never discovery or invention). Parent recovery follows approval handoff; stop
for unclear scope/success, sibling ownership, unavailable plan mode, or
unapproved new build work. This skill does not write specs, commits, or implementation.

Ask vs continue: continue when goal, constraints, success, inputs, and scope are
clear; otherwise ask the user before grooming.
