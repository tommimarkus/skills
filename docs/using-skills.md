# Using skills

Choose a skill by the result you need, install its plugin using the
[README commands](../README.md#install), and describe the work in your project.
Include the repository or artifact, the desired outcome, and any boundaries:
for example, “review only” or “implement the approved change.” You can name the
skill explicitly when several tasks overlap.

The examples below are starting requests. The linked `SKILL.md` files own the
complete workflows, evidence requirements, and stop conditions.

## Review risks and evidence

| Skill | Example request | What to expect |
|---|---|---|
| [devsecops-audit](../souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | “Run a Quick security audit of this Dockerfile and release workflow.” | Findings tied to file evidence and security criteria; Quick includes a bounded gate. Deep also assesses the wider posture. |
| [test-quality-audit](../souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | “Audit this test diff for assertions that could pass despite a broken feature.” | Per-test findings and a Quick gate. Deep also examines suite health and setup/teardown lifecycle evidence. |
| [ip-hygiene](../souroldgeezer-audit/skills/ip-hygiene/SKILL.md) | “Review these bundled examples and notices for source and licence hygiene.” | Provenance and notice findings, evidence gaps, and the applicable prospective decision, triage gate, or in-depth verdict. |
| [lean-audit](../souroldgeezer-audit/skills/lean-audit/SKILL.md) | “Audit this skill's workflow for repeated prose and unnecessary context.” | Deterministic duplication findings plus evidence-based waste observations. A bounded scope includes a limited-scope gate. |

Audits are read-only unless repairs are explicitly requested. Security,
software design, test quality, and source/IP hygiene are different questions;
one audit does not establish the others. Lean's mechanical code-duplication
check does not cover semantic DRY or source dead code. Its native-platform
comparison and minification proposal require explicit requests; minification
remains propose-only.

For bounded audits, `fail` means a substantiated in-scope blocker,
`not-evaluated` means required evidence cannot rule out blockers, and
`pass-limited` means that limited check found no blocker. A bounded lane gate
is mechanical, not a full assurance verdict. Deep/in-depth reviews disclose
broader coverage and remaining limits. IP-hygiene does not provide legal
clearance. See [audit craft](../souroldgeezer-audit/docs/audit-reference/audit-craft.md#4a-bounded-lane-gate)
for the shared gate rules.

## Design and maintain a system

| Skill | Example request | What to expect |
|---|---|---|
| [software-design](../souroldgeezer-design/skills/software-design/SKILL.md) | “Review this parser's module boundaries and where format changes would spread.” | Evidence about ownership, dependencies, coupling, and evolution, with bounded design recommendations. |
| [app-design](../souroldgeezer-design/skills/app-design/SKILL.md) | “Map this signup flow and propose a responsive layout for its three screens.” | User-flow and layout guidance, component/state decisions, and appropriate browser evidence. Unsettled material layouts include alternatives and a selection checkpoint. |
| [api-design](../souroldgeezer-design/skills/api-design/SKILL.md) | “Design a versioned HTTP API for creating and cancelling reservations.” | An API contract covering request/response behavior, errors, concurrency, security, reliability, and verification limits. |
| [infra-design](../souroldgeezer-design/skills/infra-design/SKILL.md) | “Review this Terraform environment's identity boundaries and rollback plan.” | Infrastructure findings and operational handoff guidance grounded in topology, state, deployment, and ownership. |
| [architecture-design](../souroldgeezer-architecture/skills/architecture-design/SKILL.md) | “Create a maintained UML deployment model for this service in the repository.” | A Dediren package and, for a build, validated/rendered evidence with readiness limits. A review assesses original evidence first. When reproducibility needs a build, it uses one retained isolated copy; successful rebuilding does not clear defects in the originals. |

Use software-design for code/module decisions, app-design for UI, api-design
for HTTP interfaces and consumers, infra-design for infrastructure, and
architecture-design for maintained architecture models. They support different
build, review, extraction, and lookup paths; a review request does not itself
authorize implementation.

Software-design also provides a bounded non-code File Edit lane and an additive
fragility review. Its [native-tool procedure](../souroldgeezer-design/skills/software-design/references/procedures/native-tool-evidence.md)
explains capability-based selection and optional evidence without making a new
tool installation mandatory. App-design's
[layout procedure](../souroldgeezer-design/skills/app-design/references/procedures/layout-and-flow.md)
explains when approved direction skips alternatives or a narrow edit skips the
whole procedure.

Architecture-design owns ArchiMate and UML Dediren packages. Diagrams that must
remain Mermaid, PlantUML, or draw.io belong to another workflow. See
[runtime support](runtime-support.md#dediren) for Dediren prerequisites and
export/rendering limits.

## Set repository policies

Installing a policy does not activate enforcement. Initialize it in your
repository guidance or explicitly request enforcement. A lookup or inspection
can explain a policy without adopting it. Keep options and task exceptions in
that repository's own guidance; the
[policy posture](../souroldgeezer-policy/docs/policy-reference/policy-posture-core.md)
owns this boundary.

| Skill | Example request | What to expect |
|---|---|---|
| [git-workflow-policy](../souroldgeezer-policy/skills/git-workflow-policy/SKILL.md) | “Adopt feature branches and persistent task worktrees for this repository.” | Standing Git rules and preflight guidance; PR/MR execution belongs to pr-ops. |
| [release-policy](../souroldgeezer-policy/skills/release-policy/SKILL.md) | “Establish CalVer release, verification, and rollback rules here.” | Release/version policy and authorized preparation guidance; publication needs its own authority. |
| [tdd-policy](../souroldgeezer-policy/skills/tdd-policy/SKILL.md) | “Enforce test-first implementation for this feature.” | A RED→GREEN→REFACTOR workflow with the applicable coverage and exception rules. Inspect existing tests before selecting the RED test. |
| [planning-policy](../souroldgeezer-policy/skills/planning-policy/SKILL.md) | “Plan this refactor for approval before implementation.” | An approval-ready approach and, when executable delegation is needed, a decision-complete plan and handoff. |
| [scope-policy](../souroldgeezer-policy/skills/scope-policy/SKILL.md) | “Keep this change at targeted scope and record unrelated findings.” | A declared boundary, recorded out-of-scope findings, and the applicable escalation decision. |

New executable plans start from
[plan-v5.json](../souroldgeezer-policy/skills/planning-policy/references/templates/plan-v5.json).
The discriminator is `contract_version: 5`, never `version`. Every leaf has
`capability_requirements`; approval-ready does not mean dispatch-ready. The
exact `planning-capability-binding-v1` is required before dispatch. The
[plan contract](../souroldgeezer-policy/skills/planning-policy/references/plan-contract.md),
[approval handoff](../souroldgeezer-policy/skills/planning-policy/references/approval-handoff.md),
and [ledger reference](../souroldgeezer-policy/skills/planning-policy/references/ledger-contract.md)
carry the full execution rules. Tracing is separately opt-in; ordinary planning
creates no usage telemetry. Scope policy bounds how far work may reach; it does
not prescribe the smallest possible solution.

## Handle tracked work

| Skill | Example request | What to expect |
|---|---|---|
| [issue-ops](../souroldgeezer-ops/skills/issue-ops/SKILL.md) | “Triage GitHub issue 42 and prepare its implementation plan.” | Provider-specific issue progress, with decisions and verification tied to the work item. |
| [pr-ops](../souroldgeezer-ops/skills/pr-ops/SKILL.md) | “Review this GitLab merge request and address the requested changes.” | Provider-specific PR/MR review or repair, followed by the requested lifecycle steps within your authority. |

Name the tracker and item where possible. These skills load GitHub or GitLab
support after identifying the provider; unavailable credentials or tools are
reported. A request to inspect does not authorize closing, merging, or
publishing. The repository's internal issue-lifecycle wrapper is contributor
tooling, not an additional published skill.

For missing skills, stale installations, hooks, or MCP failures, use
[runtime support](runtime-support.md). To edit the marketplace itself, start
with [contributing](contributing.md).
