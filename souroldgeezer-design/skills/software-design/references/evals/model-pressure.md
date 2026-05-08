# Software Design Model Pressure

Use this file when expanding `software-design` pattern guidance or adding a new
stack/model extension. It records the current calibration stance and the prompts
that should be replayed before adding more prose.

## Current Calibration

The skill should not teach generic pattern mechanics. Strong base models can
usually explain Adapter, Strategy, Repository, State Machine, and similar
patterns without bundled prose. The durable lift of `software-design` is the
repo-specific contract: Lean selection, evidence layers, smell-code output,
sibling-skill delegation, and stop conditions for speculative ceremony.

Do not add a new public skill or large extension for generic design-pattern
knowledge unless a fresh-agent comparison shows the base model misses one of
those repo-specific behaviors.

## Pressure Prompts

Run these as paired trials: once with no `software-design` context beyond the
user prompt, and once with the skill active.

| ID | Prompt | Skill must improve |
|---|---|---|
| SD-MP-1 | "Should this three-branch conditional become Strategy?" | Reject pattern shopping unless current variation or churn evidence exists; name the simpler rejected shape. |
| SD-MP-2 | "Review this repository/unit-of-work layer." | Distinguish pass-through ORM ceremony from a real persistence boundary using `SD-W-*` / `dotnet.SD-W-*` evidence. |
| SD-MP-3 | "Review this shell script for portability and design." | Separate shell design boundaries from security posture, then delegate `devsecops-audit` instead of absorbing it. |
| SD-MP-4 | "Design a repo-local Python tool." | Keep entrypoint, import-time behavior, stream/exit-code contract, and security delegation explicit without turning into a Python tutorial. |

## Expansion Gate

Before adding pattern entries, stack-specific prose, or a model/runtime split,
record:

- baseline failure observed without the skill;
- improved behavior with the skill;
- why a shorter generic rule or deterministic check is insufficient;
- how to rerun the comparison;
- the removal condition for the extra guidance.

If the comparison only shows that the skill repeats what the base model already
does well, delete or keep the guidance out of the bundle.
