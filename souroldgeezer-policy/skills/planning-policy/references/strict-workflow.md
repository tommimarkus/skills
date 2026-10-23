# Strict Managed Workflow

Load only for `workflow: strict`, explicit managed v5 execution, or an existing
approved managed run. Read the shared [selection](core-workflow.md#workflow-selection) and
[readability](core-workflow.md#orchestrator-readability) sections. This workflow
supplements those sections; it never
changes an existing run's recorded precision, verification, or retry settings.
New strict plans select `precision: strict` and `verification: per-leaf` unless
explicit user or repository guidance overrides them.

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
   Refine the whole plan for its parent using the
   [orchestrator readability target](#orchestrator-readability).
   Size each leaf to its changeset budget (see the
   [plan contract](plan-contract.md#verification-and-changeset-budget)): split
   or re-cut a leaf that would exceed it, or give the reason a raise requires.
   Choose `precision` once: existing v5 JSON defaults to `standard`; new strict
   plans select `strict`. `standard` declares write areas, treats
   `read_set` as optional orientation, and records a change outside the write
   set for the verifier to judge; `strict` requires exact paths, a non-empty
   `read_set`, and a clean pin scan, and stops on an out-of-set change. Run
   `validate --pin-roots` before approval in both modes and act on each
   `PLANSCOPE-UNOWNED-PIN` (see the [plan contract](plan-contract.md)).
   The scan sees only literal path mentions, so also give each leaf the tests
   that build its paths from segments, the load-cost caps and snapshots its
   edits move, fixtures whose outcome a changed default flips, and the index
   that must advertise any file it adds.
   Review acceptance for actual task coverage; structural validation cannot.
   Leaf acceptance covers its write set; whole-suite verification stays with
   the parent. Start from [plan-v5.json](templates/plan-v5.json), then follow
   [plan contract](plan-contract.md) for fields, capabilities and the Claude
   `${CLAUDE_SKILL_DIR}` / Codex `<skill-dir>` validator commands. Re-cut failed
   contracts; every leaf includes `missing_load_bearing_information`.
5. Detailed execution cost is opt-in in both profiles. When requested, add the
   bounded `planning-execution-cost-v1` profile from the plan contract. Leave
   unavailable token ranges unknown. Treat `PLANCOST-UNBATCHED-CHAIN`,
   `PLANCOST-TIER-OVER-ASSIGNED`, `PLANCOST-MICROLEAF-RISK`, and
   `PLANCOST-PLAN-SCALE` as advisory inputs, never mandatory dispositions or
   admission gates. Keep cohesive outcomes; batch, merge, re-tier, or slice only
   when justified by the work. After an approved leaf returns `oversized`,
   preserve that run and its evidence, and obtain approval for a replacement
   plan before dispatch. Derive its leaves from the original cohesive outcomes.
   A plan sliced into successive plans composes and hands off per
   [plan series](plan-series.md).

When guidance initializes `scope-policy`, the plan records its level and
escalation mode in `settled_decisions`; each leaf's `boundary`/`write_set`
materializes them, adding no plan field. `scope-policy` owns the semantics.

Delegate unless the plan states one case in one line: indivisible/trivial,
needs user mid-flight, context cannot travel, or each result redefines the
next. Dispatch overhead is a batching/merge issue and overlap a
sequencing/isolation issue; neither is an inline case. Select an owning
audit only for one bounded initial-inspection question whose evidence cannot be
resolved by targeted inspection/tests and can change approach or acceptance;
otherwise use the owning design skill.

Select each leaf's portable tier under the plan contract;
the adapter maps tiers or returns its blocker. No per-leaf runtime tuning.

Each completed leaf is also checked once by an independent read-only verifier
([verify handoff](verify-handoff.md)) unless the plan sets
`verification: closeout-only`; a run without delegation sets it at planning
time and discloses it in the footer. The verifier is independent of the builder
and never replaces the parent's integration or closeout verification. A verdict
stands across the integration rebase; the scoped-acceptance rule below is
unchanged.

`next` and `show --next-only` list other startable steps in a `concurrent`
field. Detail: [ledger contract](ledger-contract.md).

Final verification runs once, at closeout, never per integration cycle;
per-integration checks are the helper's ancestry and fast-forward proofs, not
test re-runs. Acceptance evidence survives a tree-identical rebase: the
helper's `rebased_tree_changed: false` means a leaf's recorded acceptance
stands, and `true` means re-run only that leaf's scoped acceptance, never the
full suite. When tdd-policy is in force, the parent runs its suite step once,
at integration, before final verification.

## Orchestrator readability

Refine plan prose for a fresh parent orchestrator at Codex `sol/high`, Claude
`opus/high`, or comparable capability on another host, including Copilot.
Authors may use a stronger model or greater effort. These are writing targets;
runtime model settings and subagent tier selection remain separate.

Before approval, read the plan and its named references as that fresh parent.
Provide enough detail to dispatch, assess returns, integrate, recover, and verify:

- Settled decisions and concise rationale affecting execution.
- Prerequisites, dependencies, sequencing, and integration order.
- Permitted routine judgment and decisions requiring clarification or replanning.
- Expected verification evidence, foreseeable failure responses, and the
  reference or checkpoint for resuming interrupted work.

If execution requires reconstructing the planning conversation, inferring a
missing decision, or reopening a settled choice, refine before approval.
Structural validation alone does not establish readability.

Keep cohesive steps and concise named references; avoid repeating workflows,
copying conversations, or splitting routine actions into extra steps. Bounded
implementation judgment remains with its assigned owner.

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
`completed` → `integrated` → `cleaned`; create dependent worktrees from the
current parent tip once each prerequisite is `integrated`. Follow [worker handoff](worker-handoff.md) for
generated assignments and return preflight. Use the ledger's Git-policy helper, not a routine
cherry-pick, then validate `--closeout`.

For a new version-5 run, the parent uses the ledger's
`escalating_remediation_v1` retry policy. The ledger alone decides whether an
eligible return gets one same-tier remediation attempt or a higher mapped tier;
it preserves the leaf's task, boundary, read/write sets, and attempt identity
semantics. An agent reports bounded evidence and never self-escalates, alters
its contract, or treats an oversized/missing-input stop as retryable work.

Only on an explicit economics request, include one compact **Execution economics**
line: expected/high attempts; verify dispatches; tier mix; largest repeated-context
driver; known token ranges and verification reserve, with unknowns disclosed;
`tracing: off`. Otherwise omit it. Cost findings never change validity,
readiness, dispatch, retry, or lifecycle.

Adoption template (Codex uses its native approval/delegation wording):

> `planning-policy: workflow: strict — before new feature or build work, brainstorm the
> approach in plan mode and get it approved before implementing. The approved
> plan says who runs each step; delegate decomposable work unless it states why
> not, and keep integration and verification in the parent. Scope <globs>. verify:
> per-leaf | closeout-only. precision: standard | strict. Opt out per task by saying "skip planning"
> (logged). Enforcement <model>.`

Explicit scope overrides the bare default of new feature/build/creative
work. Trivial edits, hotfixes, spikes, and domain-owned work are exceptions
only if the standing line does not cover them.
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
Verify: <per-leaf (N verified, M rejected) | closeout-only (opt-out) | unavailable (reason)>
Precision: <standard | strict>
Opt-outs: <none | phrase logged>
```
