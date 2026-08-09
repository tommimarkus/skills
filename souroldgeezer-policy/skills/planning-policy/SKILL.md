---
name: planning-policy
description: "Use when loaded repo or user guidance initializes planning-policy, or when asked to inspect, adopt, or enforce plan-first discipline — brainstorm an approach in plan mode and get it approved before implementing new feature or build work. Not for domain design, writing code, or one-off diagrams; defer to the owning design, audit, or ops skill."
---

# Planning Policy

Own plan-first enforcement only when repo/user guidance initializes this policy,
or on an explicit “plan this first” request. The standing line is authority;
installation alone is not. It protects this invariant: before new feature or
build work, briefly brainstorm in the host plan lane, converge on an approach,
and obtain user approval before implementation.

Inputs: request, applicable guidance/options, intended work, and only the files
needed to orient. Evidence: source/options, approved approach or blocker, and
the bounded footer. Invoke the owning design skill before approval when an
unresolved domain-design choice materially affects implementation. Audits,
implementation, Git, issues, and PRs remain with their named sibling skills.

## Load map

- **Lookup / inspect:** this entry surface only. Report whether the line applies;
  do not invent an enforcement result.
- **Enforce or adopt guidance:** read
  [core workflow §enforcement](references/core-workflow.md#enforcement) and
  [§approval-and-output](references/core-workflow.md#approval-and-output).
- **Executable plan, delegation, or returned handoff:** also read
  [plan contract](references/plan-contract.md) and run its advertised
  [`validate_plan_contract.py`](references/scripts/validate_plan_contract.py)
  command before approval or dispatch. For an approved plan with two or more
  delegated steps, the parent alone uses the contract's `init`, `transition`,
  `show`, and `validate` commands from
  [`planning_ledger.py`](references/scripts/planning_ledger.py).
- **Host dispatch:** read exactly one additive adapter:
  [Claude Code](extensions/claude-code.md) or [Codex](extensions/codex.md).
  If the host/mapping is unavailable, return its documented blocker; never
  silently downgrade. Re-load the other adapter only after the host changes.
- **Trigger/behavior/eval edits only:** load `references/evals/` and
  `references/source-grounding.md`.

## Enforcement

Use `enforce-initialized` for applicable initialized guidance or an explicit
request; otherwise use `lookup`. `inspect` reports compliance; `adopt-guidance`
writes the core template with its invariant. In the host plan lane: orient
lightly, ask focused questions until goal/constraints/success are clear,
state a short approach and real tradeoff, groom ready steps, then stop for
approval. Claude enters plan mode and uses `ExitPlanMode`; Codex uses native
Plan mode when available, otherwise a read-only explicit-approval fallback.
Never claim an unavailable mode or approval.

Every executable leaf follows the contract: stable ID/dependencies,
task/boundary, named reads/writes, settled decisions, size/tier, worktree
owner, one acceptance command, return, stops, and work-unit ID. Missing
load-bearing information is `blocked:missing_input`, never discovery or
invention. The parent owns decomposition, integration, and end-to-end
verification; delegated drafting is bounded to its assigned acceptance.

Stop for ambiguous/multi-subsystem scope, missing success criteria, an owning
sibling request, unenterable non-interactive plan mode, or new build work with
no approved plan and no logged opt-out. Do not write a spec, commit, or start
implementation in this skill. After guidance edits run the documented checks,
`git diff --check`, and skill-architecture validation.

Ask vs continue: continue once goal, constraints, and success are clear. If the
request is ambiguous, input is missing, or scope is uncertain, ask the user
before grooming.
