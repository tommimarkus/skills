# Shared Plan Contract

Use this contract only when grooming an executable approved plan, delegating a
leaf, or checking a returned handoff. It is runtime-neutral: host overlays add
their dispatch syntax without changing these fields.

## Plan JSON

New executable plans use `contract_version: 2`. They also declare a concise
`objective` (1–240 characters), `scope_summary` (1–480 characters), and
`approved_decisions` (one to eight non-empty strings, each at most 240
characters). These are the parent-approved facts a leaf may rely on; a leaf
does not search for or invent a replacement decision.

An unversioned existing plan remains a valid version-1 plan when it satisfies
the version-1 fields below. The validator marks it `dispatch_ready: false` and
emits a deprecation warning. Migrate it to version 2 before dispatching new
delegated work. An explicit version other than `2` is invalid.

`leaves` and `work_units` are arrays. Each executable leaf has non-empty
`id`, `dependencies`, `task`, `boundary`, `read_set`, `write_set`,
`settled_decisions`, `size`, `portable_tier`, `worktree_owner`, one string
`acceptance_command`, `return_contract`, `stop_conditions`, and `work_unit_id`.
Leaf and work-unit IDs, and each dependency ID, are stable lowercase bounded
identifiers (`[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*`, at most 64 characters).
`dependencies` is an array of other leaf IDs; `read_set`, `write_set`, and
`stop_conditions` are arrays. Every leaf's `stop_conditions` includes the exact
marker `missing_load_bearing_information`. `size` and a work unit's `original_size` are
`small`, `medium`, or `large`; portable tiers are `mechanical`, `standard`,
`analytical`, or `deep`. In version 2, each leaf also has `max_attempts`, an
integer from 1 through 5, and its `return_contract` is exactly
`bounded-step-return-v1`. The bounded return records the assigned step and
attempt, status, changed paths, focused acceptance outcome, blockers, typed
notes, commit hash, and any unstarted remainder; it never carries raw logs.

The shared plan selects only `portable_tier`. The matching host adapter maps it
to host execution settings; do not record per-leaf model or reasoning-effort
overrides. If no mapping or delegation capability is available, stop and return
the adapter blocker to the parent rather than silently changing tiers.

`work_units` declares each stable top-level unit once as `{ "id": "…",
"original_size": "…" }`. Every leaf names one declared unit and every unit
has at least one leaf. Do not create extra leaves merely to improve readiness:
the unit is weighted once at its declared original size.

Analytical and deep leaves also require a non-empty
`irreducible_unknown_or_risk`. Missing any load-bearing decision, an unknown
outside that field, a scope expansion, a failed acceptance command, or a stop
condition means stop, preserve evidence, and return to the parent. No tier may
invent the missing information.

## Readiness gate

Weights are `small=1`, `medium=2`, `large=3`. A work unit is medium-ready only
when every leaf in it is `mechanical` or `standard`. The plan's
`standard_ready_ratio` is the sum of ready unit weights divided by the sum of
all declared unit weights; it must be at least `0.60`.

An analytical-heavy exception is valid only as
`analytical_heavy_exception` with a non-empty `rationale` and a non-empty
`user_approved_by`; it records an explicit user approval and waives that ratio,
not the leaf contract.

## Selective audit routing

Normally send domain design to its owning design skill. An initial-inspection
leaf may set `selective_audit` only for one owning audit (`devsecops-audit`,
`test-quality-audit`, `ip-hygiene`, or `lean-audit`) and only with all of:
`owner`, `initial_inspection: true`, `domain_match: true`,
`materially_changes_approach_or_acceptance: true`,
`targeted_inspection_or_focused_tests_cannot_resolve: true`, a bounded
`question`, and an `evidence_surface`. Only one leaf in a plan may route this
way. “Review risks” and “review for risks” are not bounded questions.
Do not use an audit route for ordinary domain design.

## Validator

Run one of these forms before approval or dispatch:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py" validate plan.json
uv run python "<skill-dir>/references/scripts/validate_plan_contract.py" validate plan.json
```

It emits one JSON object with `contract_version`, `dispatch_ready`, and
`warnings`, as well as validity and readiness facts. It exits `0` for a valid
plan that passes the readiness gate (or its recorded exception), `1` for a
contract failure, and `2` for usage or unreadable/invalid JSON. Only a valid
version-2 plan is dispatch-ready; a valid unversioned version-1 plan is
inspection-compatible but has a deprecation warning and cannot be dispatched.

## Parent ledger helper

Only after approval, and only for two or more delegated steps, resolve the
parent-owned helper with one host form:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
uv run python "<skill-dir>/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
```

The parent uses `init-v2`; `transition` for retry and `completed` → `integrated`
→ `cleaned`; `show`; and `validate --closeout` before terminal `close`. `reopen`
is blocked-run only; `list`, `gc --dry-run`, and exact-target `purge` manage
retention. Mutations require `--actor parent`. Keep bounded evidence, not raw
logs. Read [ledger contract](ledger-contract.md) before ledger work.
