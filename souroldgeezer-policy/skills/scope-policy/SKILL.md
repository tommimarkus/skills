---
name: scope-policy
description: "Use when loaded repo or user guidance initializes scope-policy, or when asked to inspect, adopt, or enforce how wide a change may reach — bounding a change to a declared scope level (targeted, balanced, or open), recording out-of-level findings instead of doing them, and escalating one rung only when a level is insurmountable. Not for how minimal a solution should be, nor for planning, testing, or code design; defer to software-design, planning-policy, tdd-policy, and the owning sibling skill."
---

# Scope Policy

Own standing scope-boundary discipline for repositories that explicitly
initialize this policy, and answer explicit "keep this change scoped" requests.
The shared enforcement posture — passive install, opt-in through the
consumer's own guidance, the standing line (which carries the invariant
itself) as enforcement authority, low-friction opt-out — is canonical in
[`../../docs/policy-reference/policy-posture-core.md`](../../docs/policy-reference/policy-posture-core.md);
this skill supplies the invariant, levels, escalation, and adoption on demand.
Unlike `tdd-policy` and `planning-policy`, a bare initialization has no
default profile: a standing line naming `scope-policy` without a level is
`blocked:missing_input` — the invariant only binds once a rung is named, so a
level-less line cannot satisfy the posture core's "carries the invariant"
rule.

Invariant: a change stays inside a declared scope level; work that cannot be
done at that level escalates one rung under a declared escalation mode, never
silently widens.

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
loaded repo guidance initializes `scope-policy` with a level, or the user
explicitly asks to enforce scope. Apply the declared level's footprint; record
out-of-level findings rather than doing them, and route them to `issue-ops`.
Delegate existing-code reuse/debt disposition to the design skills'
`project-assimilation`, duplication/waste assessment to `lean-audit`, solution
minimalism and code/module design to `software-design`, plan-first approach to
`planning-policy`, test-first ordering to `tdd-policy`, commit/branch handling
to `git-workflow-policy`.

Ask vs continue: continue when the level, escalation mode, scope, and
exceptions are clear. Stop and ask on a level-less standing line, ambiguous
footprint, an unlogged exception request, or a level-3 (`open`) task that
cannot be completed even after disclosing the derived footprint.

Enforcement honesty follows the posture core's limits rule (enforced-by-default
posture, no mechanical guarantee). No deterministic script ships with this
skill: judging whether a refactor stays inside the blast radius is not
mechanizable, and diffing paths against scope globs alone is too thin to earn
a bundled engine.

Stop and report if a change would widen past its declared level without a
disclosed escalation, and do not proceed on a level-less standing line. Stop if
the task cannot proceed even at `open`'s model-derived footprint — that is
task-exceeds-request, not a scope problem; escalate it to the user rather than
widening further.

After guidance edits, rerun structured-file checks, `git diff --check`, and the
repo's documented skill-architecture validation. End with the output footer
from [references/core-workflow.md](references/core-workflow.md).
