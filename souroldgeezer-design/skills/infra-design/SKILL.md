---
name: infra-design
description: Use when building, extracting, reviewing, or looking up infrastructure design for IaC, cloud resources, deployment topology, environment strategy, state, rollout, operations, or Azure, Terraform, and Bicep surfaces. Route endpoint contracts to api-design, code/module/script shape to software-design, architecture models to architecture-design, security posture to devsecops-audit, and test quality to test-quality-audit.
---

# Infra Design

## Overview

Use this skill for infrastructure design work: IaC boundaries, cloud resource
shape, deployment topology, environment strategy, state, rollout safety, and
operations handoff. It is a design workflow, not a security audit, test-quality
audit, API contract review, code-boundary review, or ArchiMate model workflow.

When changing trigger metadata, workflow behavior, extension selection, source
grounding, or evaluation coverage for this skill, read `references/evals` and
`references/source-grounding.md` first. Keep eval cases synthetic or originally
paraphrased; do not copy vendor docs, examples, code, schemas, tables, or
diagrams into this plugin.

## Modes

- **Build:** create or revise an infrastructure design for a service,
  environment, platform slice, or deployment path.
- **Extract:** establish the current infrastructure baseline from source-readable
  IaC, deployment configuration, state settings, and operations handoff signals.
- **Review:** produce actionable infrastructure-design findings from existing
  IaC or deployment topology evidence.
- **Lookup:** answer a narrow infrastructure design question without performing
  a full review.

Default to Extract when the user points at existing infrastructure without a
requested change. Default to Build for new platform or environment design.
Default to Review for "review", "check", or "audit design" wording. Ask only
when the requested outcome remains ambiguous after reading the available
evidence.

## Extension Selection

The core workflow is platform-neutral. Load narrow overlays only when their
signals are present:

- `extensions/azure.md` for Microsoft Azure resource, identity, observability,
  networking, or deployment-topology signals.
- `extensions/terraform.md` for Terraform modules, providers, backend settings,
  workspaces, plans, or `.tf` / `.tfvars` files.
- `extensions/bicep.md` for Bicep modules, parameters, deployments, or `.bicep`
  files.

Multiple extensions compose. Extensions add detection signals, source anchors,
design defaults, and finding namespaces; they do not replace the core
infrastructure-design workflow.

If a matching extension is not present yet, state the missing extension and
continue with the core workflow using only source-readable evidence.

## Workflow

1. Select the mode and loaded extensions.
2. Inspect only evidence available in the task context or repository: IaC,
   deployment scripts, environment config, backend/state settings, resource
   naming, identity assignments, observability wiring, rollout config, and
   operations handoff files.
3. Separate observed source evidence from inferred runtime behavior. Do not
   claim cloud-control-plane state, cost, performance, SLO, or incident-history
   proof from static IaC alone.
4. Map the infrastructure design: ownership boundaries, environments,
   topology, identity, state, rollout path, observability, recoverability, and
   handoff responsibilities.
5. Delegate out-of-scope findings instead of absorbing them:
   `api-design` for endpoint contracts, `software-design` for code and script
   structure, `architecture-design` for ArchiMate/OEF models and drift,
   `devsecops-audit` for secrets, least privilege, supply chain, and pipeline
   hardening, and `test-quality-audit` for test quality.
6. Report the next smallest design move that reduces infrastructure risk
   without pretending static review is runtime verification.

## Stop Conditions

Stop when the target environment, IaC source, state model, or expected output
cannot be identified from the request or repository evidence. Ask the user for
the missing input before continuing. Stop instead of guessing when a requested
conclusion needs live cloud state, cost telemetry, incident history, or runtime
SLO evidence that was not provided. If the task primarily asks for security
posture, API contract, code structure, architecture-model, or test-quality
findings, delegate to the owning skill and do not emit those findings as
infra-design results.

## Output Contract

For Build and Extract, include the mode, loaded extensions, infrastructure
baseline or target shape, evidence used, assumptions, design decisions,
delegations, and verification-layer limits.

For Review, lead with actionable infrastructure-design findings only. Each
finding should name evidence, impact, recommendation, and whether the issue is
observed or inferred. Put delegated security, API, code, architecture-model, and
test-quality concerns in a separate delegation section.

Always include a footer that discloses which verification layer was used:
static source review, generated design, local validation, cloud runtime probe,
or external operational evidence. If cloud runtime evidence was not inspected,
say so directly.
