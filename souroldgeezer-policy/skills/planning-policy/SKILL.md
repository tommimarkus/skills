---
name: planning-policy
description: "Use when loaded guidance initializes planning-policy and work is in its stated scope, including named fixes and refactors; or for explicit plan-first requests and policy inspection/adoption. Own approval and bounded handoffs; domain design stays with its owner."
---

# Planning Policy

Own proportionate planning only when repo/user guidance initializes this policy,
or on an explicit “plan this first” request. Installation alone is not authority.
Apply its stated scope, including named fixes and refactors. Clear implementation
authority permits settled work; explicit plan-first constraints and material
missing decisions require approval. The parent prepares, integrates, verifies, and recovers;
workers execute cohesive assigned outcomes and scoped acceptance.

Inputs: request, guidance, intended work, and orienting files.
Evidence: inspected source, approved decisions, actual checks/results, and limitations.
An unresolved domain-design choice invokes its owning design skill before approval.

## Load map

- **Lookup / inspect:** this entry only; report applicability, not invented enforcement.
- **Enforce or adopt:** select via [workflow selection](references/core-workflow.md#workflow-selection);
  standard reads the full [core workflow](references/core-workflow.md).
  `workflow: standard` is the default: proportionate planning and delegation,
  bounded assignments/returns, parent integration and verification, and independent
  review on risk. Use its [assignment contract](references/core-workflow.md#standard-assignment-and-return)
  and [review triggers](references/core-workflow.md#independent-review).
- **Standard host:** read exactly the selected section:
  [Claude Code standard](extensions/claude-code.md#standard-workflow) or
  [Codex standard](extensions/codex.md#standard-workflow). Do not load managed
  contracts or tier wrappers for an ordinary assignment.
- **Strict or existing managed execution:** also read
  [strict workflow](references/strict-workflow.md), [plan contract](references/plan-contract.md),
  and the full selected [Claude Code](extensions/claude-code.md) or [Codex](extensions/codex.md)
  adapter. Start new executable JSON from [plan-v5.json](references/templates/plan-v5.json).
  New strict plans select strict path precision and per-leaf verification;
  explicit settings and existing approved runs retain their recorded behavior.
  Validate through [validate_plan_contract.py](references/scripts/validate_plan_contract.py)
  before approval. [Approval handoff](references/approval-handoff.md) owns
  authorized [persistence](references/scripts/persist_plan.py) or inline JSON;
  resolve before approval and dispatch. The [binding scaffold](references/templates/capability-binding-v1.json)
  binds plan, requirements, and executor; [host tiers](references/host-tiers.json)
  selects managed models and effort. Only managed workers use
  [worker handoff](references/worker-handoff.md), `check-changeset`, and `run-acceptance`;
  managed verifiers use [verify handoff](references/verify-handoff.md).
- **Managed lifecycle:** the parent uses [planning_ledger.py](references/scripts/planning_ledger.py),
  the stable shim over [planningledger/](references/scripts/planningledger/),
  for two or more delegated steps: `init-v5`, `dispatch`, `record-return`, `amend`,
  `land`, and closeout follow live `next` results. Recover after compaction with
  `show --next-only`. Only errors, diagnosis, retention operations, or ledger
  authoring/audit load [ledger contract](references/ledger-contract.md).
  Legacy runs/packets load [compatibility](references/ledger-compatibility.md).
  Successive managed plans load [plan series](references/plan-series.md).
- **Bounded unresolved audit question:** load [selective audit](references/selective-audit.md)
  only when targeted inspection cannot settle a question that changes approach or acceptance.
- **Tracing:** only on explicit trace/measure/calibrate requests load
  [usage tracing](references/usage-tracing.md). Otherwise never inspect telemetry,
  create trace state, install hooks, or make measurement/provider calls.
- **Trigger/behavior/eval edits:** load `references/evals/` and
  `references/source-grounding.md`.

## Continue or stop

Ask vs continue: continue when the approved goal, constraints, success, and
scope are clear; otherwise ask the user for missing material decisions. Discover
routine repository facts within the assignment before asking. Stop when
implementation lacks authority, ambiguity is unsafe, authority is missing, or a
required capability is unavailable. Degraded host planning uses explicit
approval without claiming a mode change. Never route a malformed v5 plan,
binding, or packet into standard work as a fallback. This skill owns planning
and handoffs, not domain specs, commits, or implementation.
