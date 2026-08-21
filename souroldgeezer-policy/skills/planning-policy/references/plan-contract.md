# Shared Plan Contract

Runtime-neutral executable-plan fields; host adapters add syntax only.

## Plan JSON

Start every new plan from the canonical
[references/templates/plan-v4.json](templates/plan-v4.json) scaffold and fill
its blank load-bearing values before approval. The first key is
`contract_version`. Do not use `version`; the validator rejects that mistaken
alias even when `contract_version` is also present.

Version 4 requires `objective` (1–240 characters), `scope_summary` (1–480), and
one to eight `approved_decisions` (1–240 each); leaves may rely on these facts.

Versions 1–3 are resume-only or inspection-compatible: v3 is resume-only and
new `init-v3` stops as `blocked:contract_migration_required`; v2 preserves its
resume behavior; unversioned v1 stays inspection-only. Existing v1–v3 ledgers
remain readable/mutable according to [ledger compatibility](ledger-compatibility.md).
Other explicit versions are invalid.

Each `leaves` entry has non-empty
`id`, `dependencies`, `task`, `boundary`, `read_set`, `write_set`,
`settled_decisions`, `size`, `portable_tier`, `worktree_owner`, one string
`acceptance_command`, `return_contract`, `stop_conditions`, and `work_unit_id`.
IDs/dependencies match `[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*` (maximum 64).
Dependencies/read/write/stops are arrays; stops include
`missing_load_bearing_information`. Sizes are small/medium/large and tiers are
mechanical/standard/analytical/deep. Versions 2–4 require `max_attempts` 1–5 and
exact `bounded-step-return-v1`, never raw logs.

Every v4 leaf also declares exact `capability_requirements`: `{ "baseline":
"plan-step-base-v1", "additional": [...] }`. `additional` is bounded and each
item names a supported requirement kind, name, and reason; it expresses what a
fresh worker needs without resolving it to a host. The baseline is required even
when `additional` is empty.

Select only `portable_tier`; model/effort belong to the host adapter. Missing
mapping or delegation returns its blocker without a silent tier change.

Retries are ledger-owned, add no plan fields, and preserve the approved boundary
and identity. New v4 uses `escalating_remediation_v1`; old policy-less state is
unchanged.

`work_units` declares `{id, original_size}` once; every nonempty unit owns at
least one leaf and is weighted once, preventing readiness-by-splitting.

Analytical/deep requires `irreducible_unknown_or_risk`; mechanical mirrors it —
`settled_decisions` and an enumerated `write_set` leaving no open choice.
`standard` names its remaining judgment in optional
`open_implementation_choice`; lacking one it is advisory
`PLANCOST-TIER-OVER-ASSIGNED`, never an error. Missing decisions,
scope expansion, failed acceptance, or a stop condition returns bounded evidence;
no tier invents input.

## Advisory execution cost

Version 3 adds an at-most-4-KiB `execution_cost` object: schema
`planning-execution-cost-v1`, `mode: advisory`, expected attempts (default 1),
optional per-leaf overrides within `max_attempts`, one to four final-verification
commands, and at most eight bounded assumptions and unknowns each. Optional
`declared_model_tokens` ranges (`low <= expected <= high`) cover parent baseline,
per-leaf worker attempts, parent turns, retained return context, and final
verification. Unknowns stay unknown; never mix stable-proxy,
declared-model-token, and provider-measured lanes.

The same validator call emits an at-most-600-proxy-token
`planning-cost-advisory-v1`: plan/handoff proxy size, retry and shared-prefix
multiplication, complete declared totals/retained context, and verification
reserve. Stable codes cover missing/invalid/unknown data, dominant prefix,
retries, unbounded verification, comparable observed drift, and tier
over-assignment; `tier_mix` reports per-tier counts, mechanical share, and
over-assigned count. Every finding
is advisory; execution control is invariant.

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

Ordinary design uses its owning design skill. When one unresolved bounded
initial-inspection question may justify an audit route, load
[selective audit routing](selective-audit.md) before adding `selective_audit`.

## Approval and dispatch readiness

For a valid v4 plan, `approval_ready` is true when all decision-complete plan
fields, including every leaf's `capability_requirements`, validate. It may be
approval-ready before any host is selected. `dispatch_ready` becomes true only
when an exact `planning-capability-binding-v1` joins the canonical plan SHA-256,
every leaf, the selected host and executor, identical requirements, and bounded
capability evidence. Missing, stale, incomplete, or mismatched bindings yield
`blocked:capability_unavailable`; never silently substitute or downgrade a
capability or executor. Host adapters own capability resolution, while this
shared contract owns the required join.

## Validator

Run one of these forms before approval or dispatch:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py" validate plan.json
uv run python "<skill-dir>/references/scripts/validate_plan_contract.py" validate plan.json
uv run python "<skill-dir>/references/scripts/validate_plan_contract.py" validate plan.json --capability-binding capability-binding.json
```

Output includes validity/readiness, `contract_version`, `approval_ready`, `dispatch_ready`,
`resume_ready`, `warnings`, and `cost_advisory`. Exit 0 is valid, 1 contract
failure, 2 usage/JSON failure. Only a v4 plan with its exact capability binding dispatches.

## Parent ledger helper

After approval, for two or more delegated steps, resolve the parent helper:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
uv run python "<skill-dir>/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
```

The parent uses `init-v4`; `transition` for retry and `completed` → `integrated`
→ `cleaned`; `show`; and `validate --closeout` before terminal `close`. `reopen`
is blocked-run only; `list`, `gc --dry-run`, and exact-target `purge` manage
retention. Mutations require `--actor parent`. Keep bounded evidence, not raw
logs. Read [ledger contract](ledger-contract.md) before ledger work.
