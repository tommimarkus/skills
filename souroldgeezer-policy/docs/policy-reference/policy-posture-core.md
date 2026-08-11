# Policy Posture Core

The enforcement posture every `souroldgeezer-policy` skill (`git-workflow-policy`,
`release-policy`, `tdd-policy`, `planning-policy`, `scope-policy`) shares. Each
skill's SKILL.md and core-workflow cite this file and add only their own
invariant, modes, options, and domain rules.

## Passive install, explicit opt-in

Installing the plugin is passive and never enforces anything by itself. A
consuming repository — or, where a skill supports it, a user's global guidance
file — opts in through its own guidance, such as `AGENTS.md` or `CLAUDE.md`,
with an initialization line naming the policy.

## The standing line is the enforcement authority

Once initialized, that guidance line (always in context) is standing enforcement
authority before the skill's matching actions. Enforcement lives in the standing
line, not in the skill firing: the skill supplies procedure, config, adoption,
and opt-out handling on demand.

## The standing line carries the invariant

`adopt-guidance` and the default init block MUST write a standing line that
carries the policy's invariant inline, not a bare pointer. Design test: a model
must be able to enforce the core behavior from that line alone, with the skill
unloaded. If it cannot, the line is underspecified — expand it.

## Opt-out is where user choice lives

Keep opt-out low-friction: a disable line, a one-phrase per-task override
(applied and logged, never silent), and scope/exception globs. Enforcement is
hard once adopted; choice lives at the on-switch and the opt-out, never in
enforcement leniency.

## Honest about enforcement limits

Enforcement is honest about its limits: phase-1 is an enforced-by-default
posture, not a mechanical guarantee (standing instructions decay; the trigger is
fuzzy). Any mechanical gate (a PreToolUse backstop) is a possible phase-2 and is
deferred unless a skill states otherwise. Do not oversell.
