# Using skills

Install the plugin that matches the work, then state the desired outcome and the relevant repository or artifact. A skill owns a bounded kind of work; it does not replace the project’s own requirements. Read its linked `SKILL.md` when you need its exact workflow, evidence, or stop conditions.

## Choose by task

| Skill | Ask it to do | Expected result | Boundary |
|---|---|---|---|
| [devsecops-audit](../souroldgeezer-audit/skills/devsecops-audit/SKILL.md) | audit a Dockerfile, CI pipeline, IaC, release, or code-security smell | risk-ranked findings and `Quick gate: <status>` | Security review, not general design or test-quality review. |
| [test-quality-audit](../souroldgeezer-audit/skills/test-quality-audit/SKILL.md) | review flaky, weak, slow, or incomplete tests | findings; Deep includes suite health and setup/teardown lifecycle evidence | Audit only; it does not implement tests. |
| [ip-hygiene](../souroldgeezer-audit/skills/ip-hygiene/SKILL.md) | review copied material, notices, licences, marks, or source provenance | coded findings and `triage gate: <status>` or in-depth verdict | It is not legal clearance. |
| [lean-audit](../souroldgeezer-audit/skills/lean-audit/SKILL.md) | audit workflow prose or plugin surfaces for duplication and context waste | bounded findings and `limited-scope gate: <status>` when applicable | Read-only; hooks and tracing remain opt-in. |
| [software-design](../souroldgeezer-design/skills/software-design/SKILL.md) | design or review code/module boundaries and dependencies | ownership, coupling, and evolution decision | Not UI, API, infrastructure, architecture-model, security, or test audit work. |
| [app-design](../souroldgeezer-design/skills/app-design/SKILL.md) | design screens, navigation, forms, responsive behaviour, or a dashboard flow | route/screen and state-flow guidance | Not backend, API, infrastructure, or architecture-model design. |
| [api-design](../souroldgeezer-design/skills/api-design/SKILL.md) | design or review an HTTP API and consumers | versioned API contract with reliability and observability | Not general module or UI design. |
| [infra-design](../souroldgeezer-design/skills/infra-design/SKILL.md) | design topology, environments, identity, rollout, or Terraform/Bicep | operational infrastructure design and handoff | Not API, UI, or source-module design. |
| [architecture-design](../souroldgeezer-architecture/skills/architecture-design/SKILL.md) | build, inspect, render, or validate an ArchiMate®/UML® Dediren package | maintained package evidence and rendered output | Use another format for diagrams that must remain Mermaid, PlantUML, or draw.io®. |
| [git-workflow-policy](../souroldgeezer-policy/skills/git-workflow-policy/SKILL.md) | establish or inspect repository git workflow rules | explicit workflow policy and preflight | Not PR/MR or release operations. |
| [release-policy](../souroldgeezer-policy/skills/release-policy/SKILL.md) | establish or inspect version, release, tag, rollback, or exception policy | release policy guidance | Not general git workflow. |
| [tdd-policy](../souroldgeezer-policy/skills/tdd-policy/SKILL.md) | establish or enforce test-first work | RED→GREEN→REFACTOR record | Not overall test-quality assessment. |
| [planning-policy](../souroldgeezer-policy/skills/planning-policy/SKILL.md) | make an approved approach dispatch-ready | `contract_version: 5` plan from [plan-v5.json](../souroldgeezer-policy/skills/planning-policy/references/templates/plan-v5.json), with `capability_requirements` and exact `planning-capability-binding-v1` before dispatch | Planning does not authorize implementation. |
| [scope-policy](../souroldgeezer-policy/skills/scope-policy/SKILL.md) | keep an initialized change within a declared boundary | scope-level assessment and escalation record | Not solution minimalism. |
| [issue-ops](../souroldgeezer-ops/skills/issue-ops/SKILL.md) | triage, resume, implement, or close an issue/work item | provider-specific lifecycle progress | Not pull requests. |
| [pr-ops](../souroldgeezer-ops/skills/pr-ops/SKILL.md) | create, review, update, fix, merge, or close a PR/MR | provider-specific PR/MR lifecycle progress | Not issues. |

## Policies and audits

Policies are passive until repository guidance initializes them or you explicitly request enforcement. A bounded lane gate is mechanical, not a full assurance verdict; see the [audit craft core](../souroldgeezer-audit/docs/audit-reference/audit-craft.md). New plans use `contract_version: 5`; `version` is never the discriminator. A decision-complete plan is approval-ready, but dispatch-ready only after the exact capability binding. The complete contract remains in [planning-policy](../souroldgeezer-policy/skills/planning-policy/SKILL.md).

## Example requests

- “Check this release workflow for supply-chain risks.”
- “Why are these integration tests flaky?”
- “Review these examples and notices for copied material.”
- “Find duplication and unnecessary context in this skill.”
- “Propose module boundaries for this parser.”
- “Map the signup flow and its mobile layout.”
- “Design error responses for this public endpoint.”
- “Plan a safe Terraform rollout for two environments.”
- “Review this UML package and its source evidence.”
- “Adopt a feature-branch worktree policy here.”
- “Set a CalVer release and rollback policy.”
- “Enforce test-first work for this feature.”
- “Turn this approved approach into a dispatch-ready plan.”
- “Keep this change within the targeted scope level.”
- “Triage issue 42 and prepare it for implementation.”
- “Review the open pull request and address its comments.”

## More detail

See [runtime support](runtime-support.md) for installation and host behaviour. Contributors should use [contributing](contributing.md) and the [skill architecture standard](skill-architecture.md) before editing a skill or adapter.
