# Planning Policy Core Workflow

Once initialized, the standing line requires a brief brainstorm in the host
planning lane, an agreed approach and user approval before new feature/build
implementation.

## Enforcement

1. Select the lane: the **Claude Code lane** calls `EnterPlanMode` unless already
   there; the **Codex lane** uses native Plan mode when exposed, otherwise stays
   read-only for explicit approval. Never claim a mode change.
2. Orient only enough to ask good questions. Ask focused questions about goal,
   constraints, and success; stop when an approach is clear.
3. State a one- or two-sentence approach with a real tradeoff/pick and execution
   shape: decomposable steps delegate by default; the parent retains decomposition,
   integration, and final verification. Before approval, invoke the owning design skill for a material unresolved domain-design choice.
4. Groom outcomes before leaves. Enumerate shared call sites, guidance,
   reads/writes, scoped acceptance, and bounded worker judgment once; settle
   material choices with their owner. Required unknowns remain missing input.
   Default to one leaf per outcome; merge file-per-leaf, code-vs-test,
   preparatory-helper, tier-gaming, and plan-size-gaming splits. Record each
   unit's `cohesive_outcome` and permitted `decomposition` evidence; neither
   batching nor multiple checks justifies splitting. Derive size from bounded
   reads, acceptance and judgment; large requires an irreducible reason.
   A fresh worker must finish from its handoff, including shared decisions.
   Review acceptance for actual task coverage; structural validation cannot.
   Leaf acceptance covers its write set; whole-suite verification stays with
   the parent. Start from [plan-v5.json](templates/plan-v5.json), then follow
   [plan contract](plan-contract.md) for fields, capabilities and the Claude
   `${CLAUDE_SKILL_DIR}` / Codex `<skill-dir>` validator commands. Re-cut failed
   contracts; every leaf includes `missing_load_bearing_information`.
5. Add the bounded advisory `planning-execution-cost-v1` profile from the plan
   contract. Leave unavailable token ranges unknown; never infer them from a
   size, tier, model name, or stable-proxy count. Contract validation calculates
   the advisory in the same invocation. Act on its codes before approval:
   re-groom to batch the flagged chain for `PLANCOST-UNBATCHED-CHAIN`, re-tier
   for `PLANCOST-TIER-OVER-ASSIGNED`, and merge unjustified split candidates for
   `PLANCOST-MICROLEAF-RISK` unless the permitted evidence-backed decomposition
   rationale applies. Then assess `PLANCOST-PLAN-SCALE`; only a still-oversized
   plan is sliced into successive plans. After an approved leaf returns
   `oversized`, preserve that run and its evidence, and obtain approval for a
   replacement plan before dispatch; derive its leaves from the original
   cohesive outcomes, not from the unstarted remainder alone.
   A plan sliced into successive plans composes and hands off per
   [plan series](plan-series.md).

When guidance initializes `scope-policy`, the plan records its level and
escalation mode in `settled_decisions`; each leaf's `boundary`/`write_set`
materializes them, adding no plan field. `scope-policy` owns the semantics.

Delegate unless the plan records one case: indivisible/trivial, needs user
mid-flight, context cannot travel, each result redefines the next, or dispatch
overhead exceeds the work — a case valid only when it cites the cost-advisory
finding as its evidence. Overlap
is a sequencing/isolation issue, not an inline exception. Select an owning
audit only for one bounded initial-inspection question whose evidence cannot be
resolved by targeted inspection/tests and can change approach or acceptance;
otherwise use the owning design skill.

Select each leaf's portable tier and weighted readiness under the plan contract;
the adapter maps tiers or returns its blocker. No per-leaf runtime tuning.

Final verification runs once, at closeout, never per integration cycle;
per-integration checks are the helper's ancestry and fast-forward proofs, not
test re-runs. Acceptance evidence survives a tree-identical rebase: the
helper's `rebased_tree_changed: false` means a leaf's recorded acceptance
stands, and `true` means re-run only that leaf's scoped acceptance, never the
full suite.

## Approval and output

Before presenting an executable plan, follow [approval handoff](approval-handoff.md).
Include the resolved envelope in the host approval plan. Approval handoff owns
authorized preparatory saves and inline fallback. Present the groomed plan and stop: Claude uses
`ExitPlanMode`; Codex uses native approval or asks explicitly and ends the turn.
Non-interactive surfaces return a proposal and say approval was not obtained.
No spec, commit, implementation, or delegation happens before approval.
After approval, resolve the envelope before capability binding or ledger init.

The active adapter resolves capabilities using the
[exact binding contract](plan-contract.md#approval-and-dispatch-readiness).
Missing capabilities stop `blocked:capability_unavailable`; never substitute
silently. Claude mechanical wrappers lack `Skill` and cannot accept additional
skill requirements.

For two or more delegated steps, only the parent creates
`<git-common-dir>/planning-policy/ledgers/<plan-id>/`. Keep bounded checkpoints,
evidence paths, and returns, never raw logs. Successful leaves close
`completed` → `integrated` → `cleaned`; only then create dependent worktrees
from the current parent tip. Follow [worker handoff](worker-handoff.md) for
generated assignments and return preflight. Use the ledger's Git-policy helper, not a routine
cherry-pick, then validate `--closeout`.

For a new version-5 run, the parent uses the ledger's
`escalating_remediation_v1` retry policy. The ledger alone decides whether an
eligible return gets one same-tier remediation attempt or a higher mapped tier;
it preserves the leaf's task, boundary, read/write sets, and attempt identity
semantics. An agent reports bounded evidence and never self-escalates, alters
its contract, or treats an oversized/missing-input stop as retryable work.

The human plan includes one compact **Execution economics** line: expected/high
attempts; tier mix; largest repeated-context driver; declared-model-token range
or `indeterminate`; final-verification reserve or `indeterminate`;
`tracing: off`.
Cost findings never change validity, readiness, dispatch, retry, or lifecycle.

Adoption template (Codex uses its native approval/delegation wording):

> `planning-policy: <profile> — before new feature or build work, brainstorm the
> approach in plan mode and get it approved before implementing. The approved
> plan says who runs each step; delegate decomposable work unless it states why
> not, and keep integration and verification in the parent. Scope <globs>. Opt
> out per task by saying "skip planning" (logged). Enforcement <model>.`

Bare initialization governs new feature/build/creative work; trivial edits,
hotfixes, spikes, and end-to-end domain-owned work are logged exceptions.
`delegation` is `subagents-by-default` or `inline`; `enforcement` is behavioral
`model`, not a claimed mechanical backstop. Opt out by removing/off, a logged
per-task phrase, or scope/exception globs.

Footer:

```text
Planning policy: <enforced-initialized | on-demand | opt-out applied | not initialized>
Source: <initialization line | explicit request>
Scope/exceptions: <in force>
Plan mode: <entered | already active | fallback used (reason) | not available (reason)>
Execution shape: <subagents: N steps (bands) | inline (case) | delegation unavailable (reason)>
Opt-outs: <none | phrase logged>
```
