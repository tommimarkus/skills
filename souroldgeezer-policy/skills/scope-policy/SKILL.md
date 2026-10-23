---
name: scope-policy
description: "Use when loaded repo or user guidance initializes scope-policy, or when asked to inspect, adopt, or enforce how wide a change may reach — choosing a declared scope level (targeted, balanced, or open), recording unrelated wider findings, and making justified bounded extensions within authority. Not for solution minimalism, planning, testing, or code design; defer to the owning sibling skill."
---

# Scope Policy

Own standing scope-boundary discipline for repositories that explicitly
initialize this policy, and answer explicit "keep this change scoped" requests.
The shared enforcement posture — passive install, opt-in through the
consumer's own guidance, the standing line (which carries the invariant
itself) as enforcement authority, low-friction opt-out — is canonical in
[`../../docs/policy-reference/policy-posture-core.md`](../../docs/policy-reference/policy-posture-core.md);
this skill supplies the invariant, levels, escalation, and adoption on demand.
Bare initialization uses the default profile in
[references/core-workflow.md](references/core-workflow.md): level `balanced`,
escalation `auto`. Explicit stop constraints and immutable managed boundaries
retain their recorded behavior. `adopt-guidance` still writes the level inline so the
standing line carries the invariant without relying on that fallback.

Invariant: use the declared scope level; make necessary bounded extensions under
the declared escalation mode with a reason, preserving explicit exclusions and
immutable managed boundaries.

Non-goal: this skill says nothing about how minimal a solution is inside its
footprint. Solution minimalism, YAGNI, and design simplicity stay with
`software-design` — do not let this skill drift into a second design skill.

Inputs: request, repo guidance, initialized level/escalation/scope/exceptions,
the diff or change about to be made. Evidence: cite the initialization source
or explicit request, the declared level and escalation mode, any rung change
with its evidence, and the out-of-level findings recorded.

Read [references/core-workflow.md](references/core-workflow.md) before real
enforcement, guidance edits, or adoption. When editing triggers, behavior,
source grounding, or evals, also read `references/evals` and
[references/source-grounding.md](references/source-grounding.md).

Modes: default `enforce-initialized` when loaded repo guidance initializes
this policy and the model is about to change code, or on an explicit enforce
request; otherwise default `lookup`. Narrower modes: `inspect`,
`adopt-guidance` (writes the standing block — MUST embed the invariant and a
level per the reference template), `preflight` (check a working diff against
the declared level and list the out-of-level hunks).

Rules: do not enforce just because the plugin is installed. Enforce when
loaded repo guidance initializes `scope-policy`, or the user explicitly asks to
enforce scope. Apply initialized options; bare initialization uses the default
profile. Apply the declared level's footprint; record
unrelated out-of-level findings rather than doing them; issue creation still
needs authority. Standard planning permits parent-reviewed automatic escalation;
strict or existing immutable managed leaves retain replacement-plan approval.
Delegate existing-code reuse/debt disposition to the design skills'
`project-assimilation`, duplication/waste assessment to `lean-audit`, solution
minimalism and code/module design to `software-design`, plan-first approach to
`planning-policy`, test-first ordering to `tdd-policy`, commit/branch handling
to `git-workflow-policy`.

Ask vs continue: resolve routine footprint facts and continue within authority.
Record a justified extension under the declared escalation mode. Ask the user when a
material boundary or explicit stop constraint needs authority, or an `open`
task exceeds the authorized outcome; keep useful independent work moving.

Enforcement honesty follows the posture core's limits rule (enforced-by-default
posture, no mechanical guarantee). No deterministic script ships with this
skill: judging whether a refactor stays inside the blast radius is not
mechanizable, and diffing paths against scope globs alone is too thin to earn
a bundled engine.

Stop and report if a change would widen past the level in force without a
disclosed escalation. Stop if the task cannot proceed even at `open`'s
model-derived footprint — that is task-exceeds-request, not a scope problem;
escalate it to the user rather than widening further.

After guidance edits, rerun structured-file checks, `git diff --check`, and the
repo's documented skill-architecture validation. Use the compact output
from [references/core-workflow.md](references/core-workflow.md).
