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

## IP provenance

The idea — a lightweight brainstorm that opens plan mode and hands the approach
to native plan-mode approval, with an additive explicit-approval fallback for
Codex — was described independently for this repository.
No prose, structure, checklist, or wording was copied from any third-party
brainstorming or planning skill; only the general concept informed it. All eval
cases are original synthetic prompts. If external material is ever referenced,
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
