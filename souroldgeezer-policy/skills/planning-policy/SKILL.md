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
  [plan contract](references/plan-contract.md), start new plan JSON from the
  [canonical v3 scaffold](references/templates/plan-v3.json), and run the advertised
  [`validate_plan_contract.py`](references/scripts/validate_plan_contract.py)
  command before approval or dispatch. For an approved plan with two or more
  delegated steps, read the [ledger contract](references/ledger-contract.md);
  the parent alone uses its `init-v3`, `transition`, `record-return`, `show`,
  `validate --closeout`, `close`, `reopen`, `list`, `gc`, and `purge` commands from
  [`planning_ledger.py`](references/scripts/planning_ledger.py). Lifecycle and
  retention commands do not replace approval or dispatch validation. The ledger
  is the sole retry owner: it records bounded remediation and chooses the next
  mapped tier without changing the approved leaf contract.
- **Compatibility or audit route only:** read
  [ledger compatibility](references/ledger-compatibility.md) when inspecting or
  resuming v2 state, and [selective audit](references/selective-audit.md) only
  when targeted inspection leaves its bounded audit question unresolved.
- **Usage tracing (explicit opt-in only):** only after the user explicitly asks
  to trace, measure, or calibrate one run, read
  [usage tracing](references/usage-tracing.md). Ordinary planning and execution
  never inspect telemetry, create trace state, install hooks, call a network, or
  contact a provider.
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

Universal stops: missing load-bearing information is `blocked:missing_input`
(never discovery or invention); stop for ambiguous or multi-subsystem scope,
missing success criteria, an owning sibling request, an unenterable
non-interactive plan mode, or new build work without approval or a logged
opt-out. This skill does not write specs, commits, or implementation.

Ask vs continue: continue once goal, constraints, and success are clear. If the
request is ambiguous, input is missing, or scope is uncertain, ask the user
before grooming.
