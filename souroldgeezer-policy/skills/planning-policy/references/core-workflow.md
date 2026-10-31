# Planning Policy Core Workflow

The standing line sets scope. Apply its stated scope and exceptions. Explicit
scope overrides the bare default of new feature/build/creative work; fixes,
refactors, hotfixes, spikes, and trivial edits are exceptions only when that
line permits them. Installation alone grants no enforcement authority.

## Workflow selection

`workflow: standard` is the default; `workflow: strict` explicitly selects the
[managed workflow](strict-workflow.md). This is separate from `precision`, which
controls paths in v5 plans. A risk trigger adds independent review, not strict
machinery. Explicit user and repository settings override these defaults. Unknown or
conflicting workflow values require clarification rather than a guessed profile.
Existing approved v5 plans, packets, and ledger runs stay managed and retain
their recorded settings, even when the current default is standard. Never
reinterpret malformed managed input as a lightweight assignment.

## Enforcement

1. Orient enough to settle the goal, constraints, success, and approach. Use
   the active host's planning/approval lane when a plan needs approval. Ask only for material missing
   decisions; inspect discoverable repository facts first. Do not invent an
   alternative when direction is settled. Before approval, invoke the owning
   design skill for an unresolved domain-design choice.
2. Scale the plan to the work: outcome, material decisions, boundaries,
   dependencies, and acceptance checks. A settled implementation request is
   authority to proceed within its stated outcome; briefly state the approach
   and work inline when that is sufficient. Delegate when parallelism,
   isolation, independent analysis, or reusable expertise earns the setup and
   integration cost; decomposability alone does not require workers. The parent
   prepares shared facts once and retains integration and final verification.
   Keep code and its tests together.
   Select an owning audit only for a bounded unresolved inspection question
   that can change approach or acceptance; otherwise use the owning design skill.
3. Obtain approval for an explicit plan-first request or constraint, a material
   unresolved decision, or an action outside existing authority. Do not insert
   another approval turn for clear authorized work or routine execution choices.
   When delegating, give the selected workers self-contained assignments under
   the contract below. Keep independent writers
   in separate persistent worktrees; sequence overlapping writes. Start dependents
   from the parent state containing their integrated prerequisites.
4. Review each returned diff against its outcome, decisions, named targets,
   scope, and actual acceptance coverage. Apply the independent-review triggers
   below before integration. Parent review and appropriate tests apply always.
5. Integrate under the repository's Git policy and run the required final
   verification once at closeout. Do not repeat the full suite per integration;
   rerun affected scoped acceptance when integration changes the tested tree.
   Preserve non-force cleanup proofs and report checks, limitations, and blockers.
   When tdd-policy is in force, the parent runs its suite step once, at
   integration, before final verification.

Standard requires no executable JSON, digest envelope, capability-binding file,
ledger, readiness score, line/file budget, mandatory pin scan, economics forecast,
or policy footer. Detailed cost forecasting and tracing remain explicit opt-ins.
Targeted impact checks remain necessary, including affected call sites, fixtures,
path-pinning tests, load budgets, generated indexes, and publication surfaces.

## Role selection

Choose the simplest suitable role for each bounded assignment, independent of workflow:

| Role | Assignment needs |
|---|---|
| [`plan-step-mechanical`](../../../agents/plan-step-mechanical.md) | Decisions are settled; apply an exact pattern or target. Stop when a new judgment is needed. |
| [`plan-step-standard`](../../../agents/plan-step-standard.md) | Approach is settled; ordinary implementation judgment remains. |
| [`plan-step-analytical`](../../../agents/plan-step-analytical.md) | Resolve a real unknown, cause, tradeoff or blast radius from evidence. |
| [`plan-step-deep`](../../../agents/plan-step-deep.md) | Challenge a correctness claim, conflicting evidence, concurrency or security assumption; a plausible wrong answer is a material risk. |

There is no quota or target mix. Settled work does not need a higher role because
its workflow is strict; a bounded hard question can use deep under standard.
Standard work may also stay inline. These roles do not impose the managed model
map on standard assignments. Keep the existing profile defaults; do not change
profile tools to satisfy an assignment. In particular, mechanical has no `Skill`.

The selected host adapter owns dispatch syntax. Check the actual executor's
required capabilities before dispatch, including role tool limits, and honor
explicit pins for model, effort, tools and behavior. If a profile is unavailable,
an equivalent native fallback may carry the same role instructions only when
its checked capabilities and settings satisfy every requirement and explicit
pin. Otherwise stop with the missing capability/model; never silently weaken a
requirement. Record the selected role and actual executor (including any fallback)
once in the assignment or compact progress record. Existing managed runs keep
their assignment, bindings, retry target and settings; use their managed rules.

`plan-verify-*` agents remain managed-only. Standard independent review uses a
fresh read-only native assignment under the review rules below.

## Standard assignment and return

Give the worker explicit `workflow: standard` and its selected role, outcome and
label, boundary/write areas, material approved decisions and constraints, useful source pointers, prerequisite state,
worktree, acceptance checks, and escalation conditions. Name any required tool,
skill, service, permission, or runtime; check availability before dispatch and
refresh that check when host, executor, or requirements change. Never silently
weaken an explicit capability requirement. Follow [role selection](#role-selection)
and the selected host adapter for profile/native dispatch and fallback. A missing
material brief field returns `blocked:missing_input`; a missing required capability
returns `blocked:capability_unavailable`. Discover routine facts from the named
source pointers instead of inventing material decisions.

Workers may inspect adjacent code, locate call sites, and establish routine
facts inside the approved outcome. Necessary adjacent edits and stronger checks
are allowed, reported, and parent-reviewed. Follow explicit repository scope or
path restrictions, including exact boundaries requested by `precision: strict`
without activating a ledger. Do not fix unrelated problems, weaken acceptance, invent
requirements, or cross an authority boundary. Missing material decisions,
unsafe ambiguity, unavailable required capability, or work that no longer fits
its bounded assignment returns a blocker with completed work and remainder.

Return a concise result, at most 8 KiB: outcome label, status, changed paths,
commit, checks with exit codes/results, blockers, limitations, and unfinished
work. Logs and large evidence live out of band behind pointers. Report changed
work with its commit; do not leave uncommitted edits. A blocked check is not a
pass. No managed schema, run/attempt identities, or JSON envelope is required.

The parent owns at most one corrective redispatch for a concrete remediation
per assigned outcome. If it fails again or makes no new progress, reassess and
report the blocker rather than repeating or resetting the count. This bounds
worker redispatches, not ordinary focused test iterations. Keep useful evidence.
The parent may resolve a routine execution correction within the approved
outcome; renewed approval is required for material changes to objectives,
constraints, externally visible behavior, or weakened acceptance.

## Independent review

Require a fresh read-only reviewer for a public-contract change, security-
sensitive change, destructive operation, removal of required behavior/rules/
assertions, or an impact the parent cannot bound. Assess these triggers during
planning and again against the actual diff; record which trigger applies. Honor
explicit repository or user review requirements even when no trigger applies.
The reviewer is independent of the builder. Give it the task, relevant approved
decisions, diff/base and returned commit, and inspectable acceptance evidence,
not builder reasoning. Check task coverage, decisions, silent removal, scope,
and whether acceptance exercises the change. Reject with a cited path and
violated requirement; style preferences do not block. Resolve substantive
findings and inconclusive required checks before integration. Review does not
replace parent responsibility or final verification.

## Orchestrator readability

A fresh parent must understand decisions, sequencing, allowed judgment,
verification evidence, blockers, and next action without reconstructing the
conversation. Keep cohesive outcomes and named references, not repeated
workflows. Size assignments by bounded reads, acceptance, and judgment rather
than predicted diff length. Re-cut when the actual task cannot be managed safely.

## Approval and output

When approval is required, use native approval when available, otherwise present
the plan for explicit approval and stop the dependent work. Never claim a mode
change or approval the host did not give. A non-interactive proposal that needs
approval discloses it was not obtained. Clear implementation authority does not
depend on a host exposing Plan mode. Read-only planning does not authorize
preparatory writes. Approval survives routine execution corrections; recovery
itself never grants new authority.

Keep a compact progress record with the approved plan/approval reference,
material decisions, completed and pending outcomes, actual attempts, evidence
pointers, blockers, and next action, at most 8 KiB excluding linked artifacts.
Use authorized persistent task storage when available. Otherwise carry a
self-contained checkpoint in the host conversation and disclose that durable
recovery is unavailable. After interruption, recover this record; ask for the
approved plan if its identity or authority cannot be established. Never invent
missing approval from a summary. This is a progress note, not another scheduler.

Adoption template (host adapters supply their native approval syntax):

> `planning-policy: workflow: standard — before work covered by Scope <globs>,
> settle the approach proportionately; proceed with clear implementation authority,
> ask for material decisions or explicit plan-first approval, delegate when its
> benefit earns the cost, retain parent integration and verification, and review on risk.
> Exceptions <globs>. Explicit settings override defaults. Say "skip planning"
> for a logged per-task opt-out. Enforcement model.`

Use `workflow: strict` for executable v5 contracts and managed execution. An
explicit `verify` setting continues to override the default review selection;
`precision` still controls v5 paths, not workflow selection. Removing/off,
a per-task opt-out, or scope exceptions remain available. Report meaningful
progress, results, and exceptions; no routine policy footer is required.
