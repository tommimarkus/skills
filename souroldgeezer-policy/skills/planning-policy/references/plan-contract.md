# Shared Plan Contract

Runtime-neutral executable-plan fields; host adapters add syntax only.

## Plan JSON

Start every new plan from the canonical
[plan-v5.json](templates/plan-v5.json) scaffold and fill
its blank load-bearing values before approval. The first key is
`contract_version`. Do not use `version`; the validator rejects that mistaken
alias even when `contract_version` is also present.

Version 5 requires `objective` (1–240 characters), `scope_summary` (1–480), and
one to eight `approved_decisions` (1–240 each); leaves may rely on these facts.

Versions 1–4 are resume-only or inspection-compatible: `init-v4` stops as
`blocked:contract_migration_required`; v2/v3 preserve their resume behavior;
unversioned v1 stays inspection-only. Existing v1–v4 ledgers
remain readable/mutable according to [ledger compatibility](ledger-compatibility.md).
Other explicit versions are invalid.

Each `leaves` entry has non-empty
`id`, `dependencies`, `task`, `boundary`, `read_set`, `write_set`,
`settled_decisions`, `size`, `portable_tier`, `worktree_owner`, one string
`acceptance_command`, `return_contract`, `stop_conditions`, and `work_unit_id`.
IDs/dependencies match `[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*` (maximum 64).
Dependencies/read/write/stops are arrays; stops include
`missing_load_bearing_information`. Sizes are small/medium/large and tiers are
mechanical/standard/analytical/deep. Versions 2–5 require `max_attempts` 1–5 and
exact `bounded-step-return-v1`, never raw logs.

An optional `batch` field names a shared-dispatch group using `id`'s stable
identifier form: 2 to 8 members, each `mechanical` or `standard`, sharing one
`worktree_owner`. An in-batch dependency may name only an earlier-listed
member of the same batch — leaves-array order is the batch's execution order;
external dependencies are unrestricted. A batch dispatches once, in one shared
worktree, with one `bounded-step-return-v1` return per member.

Every v5 leaf also declares exact `capability_requirements`: `{ "baseline":
"plan-step-base-v1", "additional": [...] }`. `additional` is bounded and each
item names a supported requirement kind, name, and reason; it expresses what a
fresh worker needs without resolving it to a host. The baseline is required even
when `additional` is empty.

Select only `portable_tier`; model/effort belong to the host adapter. Missing
mapping or delegation returns its blocker without a silent tier change.

Each `work_units` entry has non-empty `cohesive_outcome` and a `decomposition`
object. `decomposition.shape` is `single`, `parallel`, or `checkpointed`.
`single` has only `shape`. `parallel` has exactly `shape`,
`basis: parallel_independence`, and a non-empty `rationale` explaining why
multiple independently acceptable leaves or outputs can proceed inside this
one cohesive outcome without shared-write or ordering risk. `checkpointed`
has exactly `shape`, `basis` (`failure_isolation` or `rollback_boundary`), and
a non-empty `rationale`; its represented intermediate work is independently
accepted through the ordinary leaf acceptance contract, not a stored
decomposition field. Genuinely separate cohesive outcomes normally use
separate single work units. Neither a `batch`, files touched, code-vs-test
division, preparatory helper, tier selection, nor plan-scale target is a
permitted decomposition rationale. A rejected microleaf is merged back into
its cohesive outcome.

Retries are ledger-owned, add no plan fields, and preserve the approved boundary
and identity. New v5 uses `escalating_remediation_v1`; old policy-less state is
unchanged.

`work_units` declares `{id, original_size, cohesive_outcome, decomposition}` once
per cohesive outcome; every nonempty unit owns at
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
retries, unbounded verification, comparable observed drift, tier
over-assignment, an unbatched chained same-owner mechanical/standard pair
(`PLANCOST-UNBATCHED-CHAIN`), microleaf risk (`PLANCOST-MICROLEAF-RISK`: a
split lacks a permitted evidence-backed decomposition rationale), and plan scale (`PLANCOST-PLAN-SCALE`: more than
12 leaves or 20 declared work-unit weight — slice into successive plans,
advisory only); `tier_mix` reports per-tier counts, mechanical share, and
over-assigned count. Every finding
is advisory; execution control is invariant. Merge microleaf candidates before
series slicing. After an oversized return, derive the re-cut from the original
cohesive outcomes, not a list of remainder items. Successive-plan composition and
handoff live in [plan series](plan-series.md).

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

For a valid v5 plan, `approval_ready` is true when all decision-complete plan
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
failure, 2 usage/JSON failure. Only a v5 plan with its exact capability binding dispatches.

## Parent ledger helper

After approval, for two or more delegated steps, resolve the parent helper:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
uv run python "<skill-dir>/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
```

The parent uses `init-v5`, then follows each successful v5 command's live
`next` result through `transition`, `record-return`, cleanup,
`validate --closeout`, and terminal `close`. After a pause or context
compaction, `show --run-id <uuid4> --next-only` returns one deterministic highest-priority
legal category and first command; its `next` block is at most
120 proxy tokens and the whole result at most 240 proxy tokens. Full `show`
remains the at-most-1,200-token diagnostic fallback. `reopen` is blocked-run
only; `list`, `gc --dry-run`, and exact-target `purge` manage retention.
Mutations require `--actor parent`. Keep bounded evidence, not raw logs. Read
the [ledger contract](ledger-contract.md) only for errors, legacy resumption,
diagnosis, retention operations, or ledger authoring/audit.
