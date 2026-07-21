---
name: planning-policy
description: "Use when loaded repo or user guidance initializes planning-policy, or when asked to inspect, adopt, or enforce plan-first discipline — brainstorm an approach in plan mode and get it approved before implementing new feature or build work. Not for domain design, writing code, or one-off diagrams; defer those to the design, audit, and ops skills."
---

# Planning Policy

Own standing plan-first discipline for repositories — or a user's global guidance
file — that explicitly initialize this policy, and answer explicit "plan this
first" requests. Installing the plugin is passive; a consuming repo or user must
opt in through its own guidance, such as `AGENTS.md` or `CLAUDE.md`. Once
initialized, that standing line is enforcement authority before new feature or
build work: the model brainstorms an approach in plan mode and gets it approved
before implementing. Enforcement lives in that standing line (always in context),
not in this skill firing; this skill supplies the cycle, config, adoption, and
opt-out handling on demand.

Inputs: request, repo/user guidance, initialized options/exceptions, the work
about to start, relevant files and recent history.
Evidence: cite the initialization source or explicit request, the scope/options
in force, exceptions/opt-outs applied, and the brainstorm → approved-plan cycle
(or the blocker).

Read [references/core-workflow.md](references/core-workflow.md) before real
enforcement, guidance edits, or adoption. When editing triggers, behavior, or
evals, also read the eval packs under `references/evals/` and
`references/source-grounding.md`.

Modes: default `enforce-initialized` when loaded repo/user guidance initializes
this policy and the model is about to start new feature or build work, or on an
explicit plan-first request; otherwise default `lookup`. Narrower modes:
`inspect` (report initialization, scope, and whether the current approach
complied), `adopt-guidance` (write the standing line — MUST embed the invariant
per the reference template). Modes scope work; the standing line and repo/user
guidance remain authoritative.

Enforcement cycle (see the reference for the full form): if the session is not
already in plan mode, call `EnterPlanMode` before asking anything; orient
briefly; ask clarifying questions, one focused question per message, covering the
goal, its constraints, and what a good result looks like; converge on an approach
in one or two sentences, naming a tradeoff and your pick when real alternatives
exist; present it with `ExitPlanMode` for approval.
Native plan mode owns the plan — write no spec file, commit nothing, and do not
hand to a separate planning skill. Implementation is a fresh action after
approval.

Rules: do not enforce just because the plugin is installed. Enforce when loaded
repo/user guidance initializes `planning-policy`, or the user explicitly asks to
plan first. Treat an initialization line as current-task authority before new
build work; the invariant is "new feature or build work is preceded by a brief
brainstorm in plan mode that converges on an approach the user approves before
implementation." Apply initialized options; bare initialization uses the default
profile in [references/core-workflow.md](references/core-workflow.md). Keep
opt-out low-friction (disable line, one-phrase per-task override logged,
scope/exception globs) — opt-out is where user choice lives. Delegate domain
design and implementation once the plan is approved: code/module →
`software-design`; frontend → `app-design`; HTTP API → `api-design`; IaC →
`infra-design`; ArchiMate®/UML® → `architecture-design`; security →
`devsecops-audit`; test quality → `test-quality-audit`; test-first ordering while
implementing → `tdd-policy`; commit/branch preflight → `git-workflow-policy`;
PR/MR → `pr-ops`; issues → `issue-ops`.

Ask vs continue: continue when the goal, its constraints, and what a good result
looks like are clear enough to state an approach. Stop and ask on ambiguous or multi-subsystem
scope (flag decomposition first), a missing success criterion, or a request that
is really domain work a sibling owns. Never start implementing inside this skill;
approval via `ExitPlanMode` is the terminal step.

Enforcement is honest about its limits: phase-1 is an enforced-by-default
posture, not a mechanical guarantee (standing instructions decay; the
"about to build" trigger is fuzzy). A mechanical PreToolUse backstop is a
possible phase-2 and is deferred. Do not oversell.

Stop before letting new build work proceed with no approved plan unless an
explicit, logged opt-out applies. Stop if plan mode cannot be entered in the
current surface (for example a non-interactive one-shot run): produce the
proposed approach and open questions instead, and say plan mode was not entered.

After guidance edits, rerun structured-file checks, `git diff --check`, and the
repo's documented skill-architecture validation. End with the output footer from
[references/core-workflow.md](references/core-workflow.md).
