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

## Strong defaults and reasoned exceptions

Apply the initialized policy as a strong default, with judgment proportionate to
the task. A bounded alternative that preserves the authorized outcome, essential
evidence, and user state may proceed with a brief reason. Do not manufacture a
blocker from a procedural preference, unavailable optional evidence, or routine
facts the agent can discover.

Explicit user or repository constraints remain authoritative, including plan-first
requests, hard ceilings, model pins, and approved immutable managed contracts.
Ask when authority or a material decision is missing; stop an action that would
cross those boundaries or create material unbounded risk. An exception never
authorizes publication, destructive work, weakened acceptance, or a fabricated
verification result. Continue useful independent work when one action is blocked.

Keep opt-out low-friction: a disable line, a one-phrase per-task override, and
scope/exception globs. Record a meaningful exception or opt-out once alongside
the result; routine compliance needs no policy footer or repeated `n/a` fields.

## Honest about enforcement limits

Enforcement is honest about its limits: phase-1 is an enforced-by-default
posture, not a mechanical guarantee (standing instructions decay; the trigger is
fuzzy). Any mechanical gate (a PreToolUse backstop) is a possible phase-2 and is
deferred unless a skill states otherwise. Do not oversell.
