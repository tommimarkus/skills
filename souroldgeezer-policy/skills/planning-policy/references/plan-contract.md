# Shared Plan Contract

Runtime-neutral fields for strict and existing managed v5 execution; adapters
add host syntax. Standard native delegation does not use this JSON contract.

## Plan JSON

Start every new plan from the canonical
[plan-v5.json](templates/plan-v5.json) scaffold and fill
its blank load-bearing values before approval. New executable plans use
`contract_version: 5`; use `contract_version` first, since `version` is always
invalid (the discriminator is never `version`).

Version 5 requires `objective` (1–240 characters), `scope_summary` (1–480), and
one to eight `approved_decisions` (1–240 each); leaves may rely on these facts.
Verifiers see these and each leaf's `settled_decisions`; evidence a verifier
must check independently belongs in the leaf's `acceptance_command`, because
builder notes never reach it.

The validator accepts only `contract_version: 5`; an absent discriminator or
any other value is one validation error. Versions 1–4 were retired after
souroldgeezer-policy 2026.10.9; a retained pre-v5 ledger run follows
[ledger compatibility](ledger-compatibility.md).

Each `leaves` entry has non-empty
`id`, `dependencies`, `task`, `boundary`, `write_set`,
`settled_decisions`, `size`, `portable_tier`, `worktree_owner` (its git branch), one string
`acceptance_command`, `return_contract`, `stop_conditions`, and `work_unit_id`.
IDs/dependencies match `[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*` (maximum 64).
Dependencies/read/write/stops are arrays (`read_set` is optional in v5 under
standard precision); stops include
`missing_load_bearing_information`. Sizes are small/medium/large and tiers are
mechanical/standard/analytical/deep. Every leaf requires `max_attempts` 1–5 and
exact `bounded-step-return-v1`, never raw logs.

Optional top-level `precision` is `standard` (default) or `strict`; any other
value is invalid. Standard: v5 `read_set` may be absent, and `write_set` and any
present `read_set` may name areas. Strict: every `write_set` is non-empty and
exact (no glob characters) and `read_set` is a non-empty exact array. Both
modes keep exact disjoint parallel write sets and the overlap ordering rule.
A leaf's `read_set` with `write_set` forms the worker's read budget (see
[worker handoff](worker-handoff.md)), so supply `read_set` under standard
precision too, to avoid `extra_read` misses.

`validate PLAN --pin-roots ROOT [ROOT ...] [--repo-root DIR]` adds a read-only
pin scan: files under the repository-relative roots (hidden directories,
`node_modules`, `__pycache__`, `*.pyc`, and files over 1 MiB skipped) that mention a leaf's write paths
(exact path, a repository-unique basename, or an area's literal prefix) but sit
in no leaf's `write_set`. Each yields `PLANSCOPE-UNOWNED-PIN`: a warning under
standard precision, an error (approval blocked) under strict. `pin_scan` reports
`roots`, `roots_missing`, at most 8 unowned paths per leaf, and `truncated`.
Without `--pin-roots` nothing is scanned.

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
when `additional` is empty. Select only `portable_tier`; host adapters own
model/effort.

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
and identity. Every v5 run uses `escalating_remediation_v1`; a v5 checkpoint
without it is invalid. A running v5 step's execution metadata (`write_set`/`read_set`
additions, `acceptance_command`, `max_attempts`) is parent-amendable; scope
fields (task, boundary, decisions, dependencies, tier, owner) need a new plan.

`work_units` declares `{id, original_size, cohesive_outcome, decomposition}` once
per cohesive outcome; each nonempty unit owns a leaf and is weighted once.

After convergence, the parent records bounded reads, scoped acceptance, and
permitted worker judgment once per outcome. They derive `small`, `medium`, or
`large`; large names a concrete irreducible reason. Multiple checks alone do not
justify leaves. A required unknown remains missing input.

Analytical/deep requires `irreducible_unknown_or_risk`; mechanical mirrors it —
`settled_decisions` and an enumerated `write_set` leaving no open choice.
`standard` names its remaining judgment in optional
`open_implementation_choice`; lacking one it is advisory
`PLANCOST-TIER-OVER-ASSIGNED`, never an error. Missing decisions,
scope expansion, failed acceptance, or a stop condition returns bounded evidence;
no tier invents input.

## New-plan admission

New v5 approval/init requires unique safe repository-relative read/write
strings; at least one set is nonempty. Reject standalone placeholder decisions
and no-op acceptance (`true`, `:`, `exit 0`). Shared owners or overlapping writes
across any work units require dependency/batch ordering, including transitive
dependencies. Paths own descendants; glob overlap uses the literal prefix before
the first glob segment. Narrow or sequence uncertain writes; shared reads are
allowed. The parent still reviews semantic completeness and acceptance coverage.
Retained runs preserve prior admission after identity/digest checks; structural
validation remains mandatory, with no new-approval bypass.

## Advisory execution cost

An optional at-most-4-KiB `execution_cost` object has schema
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
over-assignment, an unbatched chained mechanical/standard pair, same-owner or a distinct-owner
pure chain (one dependency, one dependent) (`PLANCOST-UNBATCHED-CHAIN`), microleaf risk (`PLANCOST-MICROLEAF-RISK`: a
split lacks a permitted evidence-backed decomposition rationale), and plan scale (`PLANCOST-PLAN-SCALE`: more than
12 leaves or 20 declared work-unit weight — consider successive plans,
advisory only); `tier_mix` reports per-tier counts, mechanical share, and
over-assigned count; `critical_path` and `max_parallel_width` count dispatch-group
depth and the widest level. Every finding
is advisory. Consider merging unjustified splits before series slicing; neither
a finding nor its suggested disposition is mandatory. After an oversized return, derive the re-cut from the original
cohesive outcomes, not a list of remainder items. Successive-plan composition and
handoff live in [plan series](plan-series.md).

## Verification and changeset budget

Optional top-level `verification` is `per-leaf` (default when absent) or
`closeout-only`; any other value is a contract error. Optional per-leaf
`changeset_budget` holds only `max_changed_lines`, `max_files`, `exempt_paths`,
and `reason`. Defaults: `small` 150 lines and 6 files; `medium`/`large` 400 and
15 (added plus deleted lines; tests count). Limits are positive integers at most
2x the default; a raised limit or any exempt path requires a `reason` of 1-240
characters. `exempt_paths` holds at most 8 safe repository-relative paths, each
covered by the leaf `write_set` (exact, descendant, or glob), and leaves both
counts. `changeset_budget(leaf)` in the validator is the only derivation; the
ledger imports it. The cost advisory adds `verify_dispatches`: the dispatch-group
count, or 0 for `closeout-only`.

## Readiness diagnostics

Weights remain `small=1`, `medium=2`, `large=3`. `standard_ready_ratio`,
`ready_weight`, `total_weight`, and `analytical_heavy_exception` remain output
fields for compatibility, not admission gates. An analytical-only plan needs no
user-approved tier-mix exception. Retained `analytical_heavy_exception` metadata
remains readable. Decision completeness, bounded risk, ordering, and exact
capability binding still govern approval and dispatch readiness.

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
capability or executor.

## Validator

Run one of these forms before approval or dispatch. For approval transport,
use [approval handoff](approval-handoff.md); validation alone does not preserve
the executable JSON across a context reset:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/validate_plan_contract.py" validate plan.json
uv run python "<skill-dir>/references/scripts/validate_plan_contract.py" validate plan.json
uv run python "<skill-dir>/references/scripts/validate_plan_contract.py" validate plan.json --capability-binding capability-binding.json
```

Output includes validity/readiness, `contract_version`, `approval_ready`, `dispatch_ready`,
`warnings`, and `cost_advisory`. Exit 0 is valid, 1 contract
failure, 2 usage/JSON failure. Only a v5 plan with its exact capability binding dispatches.

`validate_plan_contract.py` remains read-only; approval handoff owns authorized saves.

## Parent ledger helper

After approval, for two or more delegated steps, resolve the parent helper:

```text
uv run python "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
uv run python "<skill-dir>/references/scripts/planning_ledger.py" --plan-id <plan-id> --help
```

The parent uses `init-v5`, then follows each successful v5 command's live
`next` result through `transition`, `record-return`, `amend`, cleanup,
`validate --closeout`, and terminal `close`. After a pause or context
compaction, `show --run-id <uuid4> --next-only` returns one deterministic highest-priority
legal category and first command; its `next` block is at most
120 proxy tokens and the whole result at most 240 proxy tokens. Full `show`
remains the at-most-1,200-token diagnostic fallback. `reopen` is blocked-run
only; `list`, `gc --dry-run`, and exact-target `purge` manage retention.
Mutations require `--actor parent`. Read
the [ledger contract](ledger-contract.md) only for errors,
diagnosis, retention operations, or ledger authoring/audit.
