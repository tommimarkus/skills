---
name: infra-design
description: Use when building, extracting, reviewing, or looking up infrastructure design for IaC, cloud resources, deployment topology, environment strategy, state, identity boundaries, rollout/rollback, operations handoff, or Azure®, Terraform™, and Bicep™ surfaces without duplicating API, UI, code, architecture-model, security-audit, or test-quality specialist skills.
---

# Infra Design

## Overview

Shape infrastructure so deployments are understandable, recoverable, and cheap
to evolve. The skill applies the bundled reference at
[../../docs/infra-reference/infra-design.md](../../docs/infra-reference/infra-design.md).

This is the design companion for IaC, cloud topology, environments, state,
rollout, and operations handoff. It does not produce ArchiMate/OEF models,
security posture audits, API contracts, UI responsive behavior, code/module
design, or test-quality classifications.

When changing trigger metadata, workflow behavior, extension selection, source
grounding, or evaluation coverage for this skill, read `references/evals` and
`references/source-grounding.md` first. Keep eval cases synthetic or originally
paraphrased; do not copy external prompts, code, examples, diagrams, tables, or
docs into this plugin.

## Modes

### Build Mode

Use for new infrastructure, IaC modules, environments, deployment paths,
resource topology, release flow, or operational wiring before implementation.

Output a compact infrastructure design brief:

```text
Mode: Build
Scope:
Forces:
Recommended topology:
IaC structure:
Environment strategy:
State and identity boundaries:
Reliability and operations:
Validation step:
Delegations:
Footer:
```

### Extract Mode

Use when adapting to an existing repo or when the user asks what
infrastructure design already exists.

Output an infrastructure baseline:

```text
Mode: Extract
Scope:
Signals inspected:
Current topology:
IaC ownership map:
Environment and state model:
Operational dependencies:
Drift / legacy debt:
Next smallest move:
Delegations:
Footer:
```

### Review Mode

Use for IaC files, deployment proposals, CI/CD release shape, environment
layout, or infrastructure design review questions.

Per finding:

```text
[ID-<family>-<n>] <file>:<line>
  bucket:   topology | iac | environment | state | identity | reliability | operations | evolution
  layer:    static | iac | plan | runtime | cloud-control-plane | human
  severity: block | warn | info
  evidence: <short snippet or observed structure>
  action:   <smallest useful infrastructure-design correction>
  ref:      infra-design.md section <n.m> + extension code when applicable
```

Block only when the design likely creates unsafe deployment coupling,
environment/state ambiguity, irrecoverable drift, identity confusion, or an
operational path that cannot be validated before rollout.

### Lookup Mode

Use for narrow infrastructure design questions: module split, state ownership,
environment shape, deployment boundary, rollout, or infrastructure ownership.
Answer in two to six lines, cite the reference section, and emit a footer line.

## Default Dispatch

- Existing repo with no specific change: Extract.
- New infrastructure, IaC, environment, or rollout request: Build.
- Existing IaC, deployment proposal, or "review/audit/is this good" wording:
  Review.
- Narrow principle or tradeoff question: Lookup.
- Ambiguous request: ask the user to choose.

## Extensions

Load extensions only when source signals match. Multiple extensions compose on
the same target.

| Extension | Applies to | Loaded when target matches |
|---|---|---|
| [extensions/azure.md](extensions/azure.md) | Azure® infrastructure design | Azure resource types, Azure CLI/PowerShell deployment commands, Azure resource IDs, Azure Functions/App Service/Container Apps/AKS/Storage/Cosmos/Event Grid/Key Vault/Application Insights signals, Azure Pipelines, or Azure resource-group/subscription/tenant vocabulary |
| [extensions/terraform.md](extensions/terraform.md) | Terraform™ IaC design | `.tf`, `.tfvars`, `.terraform.lock.hcl`, backend/provider blocks, module blocks, Terraform Cloud/Enterprise config, plan/apply commands, or state backend references |
| [extensions/bicep.md](extensions/bicep.md) | Azure Bicep design | `.bicep`, `.bicepparam`, `bicepconfig.json`, ARM deployment commands, `module` declarations, `targetScope`, or Bicep parameter files |

Unknown stacks proceed with the core reference only. Azure Bicep targets load
`azure.md` and `bicep.md`; Azure Terraform targets load `azure.md` and
`terraform.md`. Extensions never override core rules.

## Pre-Flight

Before build, extract, or review:

1. Identify mode and scope. If the user supplied files, read only the relevant
   slice first.
2. Identify the infrastructure question: topology, IaC boundary, environment
   promotion, state, identity placement, rollout, operations, or drift.
3. Detect and load matching extensions. Announce loaded extensions.
4. Read the reference sections needed for the mode:
   - Principles and defaults: reference sections 2 and 3.
   - Primitives and patterns: sections 4 and 5.
   - Smells and checklist: sections 6 and 7.
5. State verification layers available from the current evidence: `static`,
   `iac`, `plan`, `runtime`, `cloud-control-plane`, `human`.
6. Delegate instead of stretching this skill when the request belongs to a
   sibling skill.

If the user has not supplied environment, cloud, or operational constraints,
default to the smallest coherent infrastructure design that satisfies the
source-readable requirement and leaves deferred decisions explicit.

## Project Assimilation

Assimilation is one-way: the project is brought up to the reference; the
reference is not weakened to match local drift.

Before Build, Extract, or Review in an existing repo, inspect these signals:

1. IaC roots and module boundaries.
2. Deployment entrypoints and CI/CD workflows.
3. Environment names, parameter files, variable files, and promotion paths.
4. State backends, lock files, generated artifacts, and import/migration
   records.
5. Identity, secret, and configuration ownership signals.
6. Observability, backup, rollback, and runtime-verification hooks.
7. Architecture model pairing at `docs/architecture/<feature>.oef.xml` when
   present.

Reuse compliant infrastructure and names. Flag non-compliant infrastructure as
legacy debt. If legacy debt is load-bearing for the requested change, halt and
ask whether to expand scope or choose a smaller safe change.

## Build Workflow

1. Confirm Build mode and load extensions.
2. Frame scope as in/out. Name design forces using reference section 3.
3. Choose the smallest topology, IaC, environment, state, or rollout pattern
   from reference sections 4 and 5.
4. Define ownership boundaries, dependency direction, state ownership, and
   identity handoff.
5. Name deferred decisions and rejected abstractions.
6. Pick the cheapest validation step: source review, IaC validation, plan or
   what-if, smoke deployment, telemetry check, restore test, or human review.
7. Include `devsecops-audit` delegation when security posture, secrets,
   least privilege, CI/CD hardening, or supply-chain posture is in scope.
8. Emit the Build output contract and footer.

## Extract Workflow

1. Confirm Extract mode and load extensions.
2. Inspect source-readable structure first: IaC roots, modules, deployment
   commands, workflows, parameter files, state config, and generated artifacts.
3. Separate observed facts from inference. Mark inferred runtime behavior
   explicitly.
4. Produce a current infrastructure map: topology, IaC ownership, environment
   strategy, state model, operational dependencies, drift, and legacy debt.
5. Identify the next smallest useful design move.
6. Emit the Extract output contract and footer.

## Review Workflow

1. Confirm Review mode and load extensions.
2. Walk reference section 7 and loaded extension smells.
3. Emit only actionable infrastructure-design findings. Do not pad with
   generic best-practice commentary.
4. Use severity consistently:
   - `block`: unsafe deployment coupling, state loss risk, production apply
     without review, or mandatory new work routed through bad infrastructure
     design.
   - `warn`: maintainability, rollback, drift, or operations risk with a clear
     smaller correction.
   - `info`: useful design note or deferred validation.
5. Keep layer claims honest. Static review cannot prove runtime, cost, latency,
   quota, backup success, failover behavior, or rollout safety.
6. Follow findings with a short rollup and footer.

## Lookup Workflow

1. Locate the relevant reference section or extension note.
2. Answer directly with the default rule and exception boundary.
3. Recommend a sibling skill only when the question crosses into that sibling's
   scope.
4. Emit a one-line footer.

## Delegation Boundaries

- HTTP API contract, auth behavior, retries, API observability, and data-service
  API patterns: `api-design`.
- Code/module/script design: `software-design`.
- Web frontend app and UI concerns, including routes/screens, component
  architecture, responsive behavior, accessibility, i18n, visual behavior, and
  Core Web Vitals: `app-design`.
- ArchiMate models, OEF XML, rendered architecture diagrams, and
  code-to-architecture drift: `architecture-design`.
- Pipeline/IaC/application security posture, secrets, least privilege,
  dependency/supply-chain posture, and release hardening: `devsecops-audit`.
- Unit/integration/E2E test quality or mutation-testing worklists:
  `test-quality-audit`.

## Footer

Every mode emits:

```text
Mode:
Extensions loaded:
Reference path: souroldgeezer-design/docs/infra-reference/infra-design.md
Verification layers used:
Project assimilation:
Delegations:
Limits:
```

`Limits` must disclose when source review cannot prove cloud runtime behavior,
cost, latency, quota, backup success, failover behavior, restore success, or
rollout safety.

## Red Flags

Stop and revise before delivering if output:

- Turns security posture or least privilege into infra-design findings instead
  of delegating to `devsecops-audit`.
- Claims runtime behavior, availability, cost, quota, backup, or failover facts
  from static source alone.
- Extends local/committed state, ambient environment selection, or portal-only
  resource drift into new infrastructure.
- Adds modules or environments without a current ownership, lifecycle, or
  blast-radius force.
- Replaces `architecture-design` by inventing prose diagrams or model drift
  findings.
