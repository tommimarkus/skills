# Planning Policy Source Grounding

## 2026-08-29 batch dispatch, advisory-fed grooming, and verification economy

The batch lane and the two new cost-advisory codes are grounded in a
repository-observed overhead pattern, not a hypothetical one. Dispatching one
delegated leaf at a time charged a fixed per-dispatch overhead on every leaf
regardless of size, so that overhead scaled with leaf count even when several
leaves shared one worktree owner and ran one after another with nothing else
in between. Grooming's incentive ran one way only: a step could always be
split smaller to keep it readable, but nothing pushed the other direction once
a chain of small, dependency-consecutive leaves made that per-dispatch
overhead the dominant cost of the plan. Integration then serialized on top of
that: each returned leaf rebased, merged, and cleaned up on its own before the
next dependent leaf's worktree could even start. And the cost advisory itself,
once it existed, stayed purely descriptive — it could already report a shape
like an unbatched chain or an oversized plan in the rendered economics, but
nothing in grooming read the finding back before the plan was presented for
approval, so the computation ran and its result went unused. The
repository-authored regressions in
[`tests/planning_policy_shared_contract_test.py`](../../../../tests/planning_policy_shared_contract_test.py)
(`test_batched_dispatch_lowers_prefix_multiplication_while_handoff_total_matches`,
`test_unbatched_chain_fires_between_mechanical_leaves_even_without_profile`,
`test_plan_scale_fires_over_twelve_leaves_and_not_at_twelve`),
[`tests/planning_ledger_lifecycle_test.py`](../../../../tests/planning_ledger_lifecycle_test.py),
and [`tests/planning_worktree_helper_test.py`](../../../../tests/planning_worktree_helper_test.py)
model each part of that diagnosis directly.

The response keeps every vocabulary choice tied back to that same diagnosis.
A "batch" groups chained, same-owner mechanical or standard leaves — never
analytical or deep work, where holding the unknown alone is the reason to keep
a step by itself — into one dispatch that a worker executes member by member
in the one shared worktree, committing and returning each member on its own so
the fixed per-dispatch cost is paid once for the chain instead of once per
member. When a member stops, the batch "unwinds" the never-run followers
behind it back to pending — refunding the attempt already minted for each one
and clearing its identity — rather than leaving them stranded in-progress for
work they never started. "Advisory-fed grooming" is the fix
for the unread finding: grooming now acts on `PLANCOST-UNBATCHED-CHAIN` and
`PLANCOST-PLAN-SCALE` before the plan is presented for approval — batching the
flagged chain, re-tiering it, or recording the stated reason not to — instead
of only rendering them in the economics footer afterward. "Slice" names the
`PLANCOST-PLAN-SCALE` advice for a plan that has grown past twelve leaves or
twenty declared unit weight: split it into successive plans rather than
carrying one oversized plan forward, the same plain word this file already
uses for splitting an oversized migration by group. Both codes stay advisory;
neither changes a plan's validity, readiness, or dispatch eligibility, which
preserves the boundary the "2026-08-10 contract-v3 execution economics"
section below already drew between cost data and execution legality.

The verification-economy rule — trusting a leaf's recorded acceptance evidence
when a rebase left its tree unchanged, re-running only a leaf whose tree
actually moved, and running the full suite exactly once at closeout — promotes
this maintainer's own
working practice of not re-verifying output a gate already proved unchanged
into the published contract. It is the same avoid-redundant-verification habit
this repository already applies to its own gates (skip re-checking a
fast-forward integration, scope suites to changed inputs), now expressed
through the worktree helper's `rebased_tree_changed` comparison rather than
left as an unstated maintainer preference. See "IP provenance" below for how
this generalization is recorded alongside the earlier execution-shape default.

## 2026-08-25 complete live-next lifecycle

The v4 live-next chain is grounded in the repository-authored cost and restart
regressions in `tests/planning_policy_cost_test.py` and
`tests/planning_ledger_next_block_test.py`. Before this change, normal parent
execution loaded a 2,476-proxy-token runtime reference because only `init-v4`
and `record-return` stated their next action. That repeated context dominated a
4,487-proxy-token happy path and made recovery after a 24-hour pause or context
compaction depend on re-reading narrative mechanics.

The repository-authored remedy derives every new hint from the validated
post-command checkpoint and the same dependency, attempt, and retry predicates
that enforce legality. Successful v4 lifecycle results form the normal chain;
read-only `show --next-only` selects one deterministic priority category when a
fresh parent must resume. Full `show` and the runtime reference remain the
diagnostic and authoring fallbacks. No external orchestration framework,
workflow text, schema, or command design was copied; the action order and
bounded result shapes are original synthetic fixtures for this repository.

## 2026-08-22 contract-v4 capability binding

The v4 contract separates a plan being ready for human approval from being ready
for host dispatch. The repository-authored regression in
[`planning_policy_v4_capability_test.py`](../../../../tests/planning_policy_v4_capability_test.py)
and synthetic cases in [`behavior-cases.jsonl`](evals/behavior-cases.jsonl)
model the failure: a decision-complete delegated plan could be approved before
the selected host had established whether the fresh worker had every required
capability. The repository-authored remedy keeps
host resolution in the Claude and Codex adapters while every v4 leaf declares
portable `capability_requirements`: the `plan-step-base-v1` baseline plus bounded
additional requirements. A `planning-capability-binding-v1` then joins the
canonical plan digest, every leaf, its exact requirements, selected host and
executor, and bounded evidence. A missing or mismatched join is
`blocked:capability_unavailable`, never an implicit substitute or downgrade.

This division is deliberate: approval is a decision about the bounded work, not
an assertion about transient host inventory. Dispatch is only permitted after
the adapter produces the exact binding. The binding follows assignment changes,
so a v4 retry or reassignment must re-bind before ready. The synthetic Claude
mechanical-worker case records the non-negotiable edge: its wrapper lacks
`Skill`, so it cannot dispatch a leaf whose additional requirement is a skill.
Existing v1–v3 ledger behavior remains readable/mutable under compatibility;
only new v4 ledgers own capability binding.

## 2026-08-13 canonical v3 authoring scaffold

The canonical scaffold addresses recurring discriminator drift observed in
repository-authored executable plans: an author used the mistaken `version` key
instead of `contract_version`, and the validator then treated the document as an
unversioned legacy plan. The absence of a fill-in scaffold made the field set
easy to reconstruct incorrectly from prose. The repository-authored remedy keeps
`contract_version` first, leaves load-bearing values blank, rejects the alias
explicitly, and preserves genuinely unversioned version-1 inspection. No
third-party plan schema or wording informed the scaffold or its synthetic eval.

## 2026-08-10 contract-v3 execution economics

The v3 additions are grounded in the repository's prior bounded-handoff and
token-awareness assessment: preserve unknown token quantities, keep proxy,
declared-model-token, and provider-measured lanes separate, reserve final
verification explicitly, and make runtime measurement a separate opt-in. The
implementation generalizes the v2 ledger rather than duplicating it; existing
v2 records remain resume-only and new initialization moves forward to v3.

This skill centralizes a plan-first discipline into an install-passive,
enforcement-active policy that a repository or a user's global guidance file
initializes with local scope and exceptions, plus an on-demand "plan this first"
path. Plugin installation alone does not enforce it; the standing guidance line —
which must embed the invariant — is the enforcement authority. `adopt-guidance`
writes that standing block. The enforcement action is native to Claude Code:
`EnterPlanMode` opens plan mode and `ExitPlanMode` presents the plan for
approval, so the skill owns no plan file of its own. The additive Codex lane uses
native Plan mode when active or exposed and otherwise stops for explicit user
approval without claiming a mode change. Enforcement is honest: a default
posture in phase 1, mechanically guaranteed only by an optional phase-2
PreToolUse/edit backstop (deferred).

The approved plan also carries an execution shape — subagent delegation by
default for decomposable steps, with decomposition, integration, and verification
retained by the parent session. Approval is the last cheap moment to decide how
work is split, so the decomposition belongs in the approach the user agrees to
rather than being improvised mid-implementation. The default is strong but not
absolute: a departure is legitimate when stated in the plan, which keeps the
choice visible instead of silent. The parent-retained verification exists because
a subagent's "verified" attests only to its own drafting checks.

The delegation contract selects a portable tier rather than per-step runtime
knobs. The host adapter maps that tier to its supported model, effort, and tool
settings, so the shared plan stays stable while host parameter surfaces change.
Hand-tuning a leaf outside its mapped tier is not a shared-contract option. If
the host lacks a mapping or delegation capability, the executor stops and
returns the blocker to the parent; the portable plan is retained rather than
silently downgraded. The failure mode that actually costs a delegated step — an
under-specified handoff to a subagent with no conversation history — remains
squarely plan content.

Grooming the plan's steps before presenting it for approval exists because this
repository's own sessions produced the failure it fixes, not a hypothetical one:
a single decomposition pass judged only by whether a step could be split at all,
with no check on whether the resulting steps were actually right-sized, handed
subagents work that exhausted their context and produced plans that cost far
more than the work warranted. The size band a groomed step carries is derived
from the same readiness tests that decide whether to split or merge it — a named
read-set and a single acceptance check — rather than estimated on its own, so the
band cannot drift out of step with the structural judgment that produced it.

The band and the execution-tier agents' oversize stop-and-report edge form one
control loop rather than two separate features: the band gives the executing
agent something concrete to compare reality against, and the report hands the
re-cut decision back to the parent, which is where the decomposition judgment
already lives and where a subagent's local view cannot substitute for it.
Assigning discovery — enumerating a read-set, finding the call sites a broad ask
touches — to the parent during grooming follows the same reasoning: one
enumeration done once, while the parent is already oriented, replaces the same
search repeated inside every subagent it would otherwise delegate to, and that
cost asymmetry is the reason, not a preference for tidier handoffs.

The shared plan contract extends that loop without assigning host behavior to
the core workflow: stable leaf IDs, dependencies, boundaries, decision records,
one acceptance command, stop conditions, and a return shape make a fresh
executor's handoff auditable. A common portable tier lets the same plan travel
between Claude Code and Codex overlays. The weighted medium-ready gate measures
stable top-level work units once at their original size, so a plan cannot improve
its readiness score by splitting a concern into decorative leaves. Every tier
stops and returns when a load-bearing decision is missing; analytical/deep work
records the one irreducible uncertainty rather than silently widening scope.

The successful lifecycle extends through cleanup because a returned commit is
not yet integration evidence, and a patch-equivalent cherry-pick does not make
the source branch an ancestor. Rebase plus fast-forward preserves ancestry;
the separate non-force cleanup proof can then retire the branch deterministically.
Dependencies wait for that proof so their worktrees start from the parent state
that actually contains and has closed their prerequisites.

The ledger's lifecycle and retention rules preserve that bounded-parent model
after execution: terminal closure records one explicit outcome, reopening is
limited to a retained blocked run with retryable work, and list/garbage
collection/purge expose bounded discovery without a bulk-delete path. Outcome
retention (completed 30 days, blocked 90 days, abandoned 7 days) protects
active or ambiguous state from age-based inference while allowing conservative
cleanup of validated closed runs. These lifecycle, retention, and helper
contracts are repository-authored from the same durable-ledger need; they do
not derive from an external orchestration framework.

Runtime-escalating remediation follows the same boundary: the ledger, not a
leaf or host adapter, owns retries. A new version-4 run stamps
`escalating_remediation_v1`, while policy-less existing version-2 checkpoints
and version-1 ledgers retain prior behavior. It allows one same-tier retry only
after exact `failed:acceptance`; `blocked:needs_higher_tier` immediately moves
to a higher mapped tier, and later eligible retries may skip upward but never
past `deep` or `max_attempts`. The persisted `retry-remediation-v1` ties the
prior returned evidence to a diagnosis and action without changing the original
worktree, boundary, or identity semantics. This is repository-authored from
the observed need for bounded remediation rather than external orchestration
guidance.

## IP provenance

The idea — a lightweight brainstorm that opens plan mode and hands the approach
to native plan-mode approval, with an additive explicit-approval fallback for
Codex — was described independently for this repository.
No prose, structure, checklist, or wording was copied from any third-party
brainstorming or planning skill; only the general concept informed it. The
execution-shape default likewise generalizes this maintainer's own working
practice — delegate decomposable steps, keep integration and verification in the
parent session — and not any third-party delegation or orchestration skill. The
verification-economy rule likewise generalizes this maintainer's own
working practice — skip re-verifying output a gate already proved unchanged —
and not any third-party build-caching or continuous-integration tool. The
grooming pass was likewise described independently for this repository, from the
observed context-exhaustion failure mode described above, not from any
third-party source. It deliberately uses the plain-English terms "groom",
"refine", and "ready" rather than any agile or Scrum framework vocabulary,
ceremony name, or capitalized framework term, and no third-party planning,
estimation, or backlog-management framework prose was consulted or copied. All
eval cases are original synthetic prompts. If external material is ever referenced,
link it by URL and paraphrase in original wording; do not paste third-party text
into the bundle.

## Boundary decisions

- Plan-first approach approval before new build work: `planning-policy`.
- Test-first ordering while implementing: `tdd-policy` (composes after the plan).
- Code/module design and coupling: `software-design`.
- Frontend app design: `app-design`. HTTP API design: `api-design`. IaC design:
  `infra-design`. ArchiMate®/UML® models: `architecture-design`.
- Security posture: `devsecops-audit`. Test adequacy/brittleness:
  `test-quality-audit`.
- Commit/branch preflight: `git-workflow-policy`. PR/MR: `pr-ops`. Issues:
  `issue-ops`.
