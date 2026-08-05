# Planning Policy Source Grounding

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

The delegation contract covers what the step is handed, not how the host is
tuned. Runtime knobs are deliberately out of scope: hosts default to inheriting
the session's model and reasoning effort, agent definitions already carry their
own model and tool set, and the parameter surface differs per host and moves
between releases. Enumerating knobs here would date quickly and drift across the
two runtimes, while the failure mode that actually costs a delegated step — an
under-specified handoff to a subagent with no conversation history — is squarely
plan content.

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

## IP provenance

The idea — a lightweight brainstorm that opens plan mode and hands the approach
to native plan-mode approval, with an additive explicit-approval fallback for
Codex — was described independently for this repository.
No prose, structure, checklist, or wording was copied from any third-party
brainstorming or planning skill; only the general concept informed it. The
execution-shape default likewise generalizes this maintainer's own working
practice — delegate decomposable steps, keep integration and verification in the
parent session — and not any third-party delegation or orchestration skill. The
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
