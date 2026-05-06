---
name: infra-design
description: >-
  Use when building, extracting, reviewing, or looking up infrastructure/IaC design: topology, environments, state, identity, rollout/rollback, operations handoff, and Azure®, Terraform™, or Bicep™. Defer API, UI, code, architecture, security, and test-quality work.
---

# Infra Design

Shape infrastructure/IaC so deployments are understandable, recoverable,
observable, and evolvable, using
[../../docs/infra-reference/infra-design.md](../../docs/infra-reference/infra-design.md).

## Contract

Own Build/Extract/Review/Lookup for topology, IaC, envs, state, identity,
rollout/rollback, drift, and ops handoff. Delegate API/UI/code/ArchiMate/
security/test-quality to `api-design`, `app-design`, `software-design`,
`architecture-design`, `devsecops-audit`, and `test-quality-audit`.

Inputs: files, diffs/proposals, topology, IaC roots/modules, env/state
constraints, deployment evidence, rollout policy, and ops signals. Do not infer
runtime/cost/quota/backup/failover/restore/rollout facts from static source. If
ambiguous, ask the user when mode/scope/env/source/evidence cost/destructive
edits/sibling ownership lacks a safe default; otherwise continue.

Modes: Build new/refactored infra; Extract existing design; Review IaC,
deployment proposals/PRs/plans; Lookup narrow infra-design tradeoffs.

## Load Map

Load [extensions/azure.md](extensions/azure.md) for Azure® resource/service/
subscription/tenant/RG/CLI/PowerShell/pipeline signals;
[extensions/terraform.md](extensions/terraform.md) for `.tf`, `.tfvars`,
backend, provider, module, plan/apply, or state; and
[extensions/bicep.md](extensions/bicep.md) for `.bicep`, `.bicepparam`,
`bicepconfig.json`, ARM, `module`, or `targetScope`. Azure+Bicep and
Azure+Terraform compose. Load [extensions/README.md](extensions/README.md) only
when editing extensions.

Before editing triggers/workflow/extensions/grounding/evals, load
[references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md); keep evals
synthetic/paraphrased.

## Workflow

1. Select mode/scope/question/env/evidence.
2. Prefer `rg`; inspect IaC roots/modules, deployment entrypoints/workflows,
   env/state files, generated artifacts, identity/config/observability/rollback
   signals, and architecture model pairing.
3. Detect/announce extensions, separate fact from inference, name verification
   layers, choose the smallest topology/IaC/env/state/rollout move, then emit
   contract/footer.

## Mode Outputs

- Build: scope/forces, topology, IaC structure, environment strategy,
  state/identity, ops, validation, delegations.
- Extract: signals, topology, IaC ownership, env/state, ops, drift/debt, next
  move.
- Review: findings only; `block` unsafe deployment coupling, state loss,
  production apply without review, env/state ambiguity, identity confusion, or
  unvalidated ops path.
- Lookup: direct rule, exception, citation, delegation, one-line footer.

Every answer reports mode, extensions, reference path, layers (`static`, `iac`,
`plan`, `runtime`, `cloud-control-plane`, `human`), assimilation, delegations,
and limits. Findings use
`[ID-<family>-<n>] <file>:<line>` with bucket, layer, severity, evidence,
action, and citation. If none, say so with limits.

## Stop Conditions

Stop when source/scope/env is missing, sibling ownership dominates, non-static
evidence is needed but absent, load-bearing drift has no smaller move, extension
validation is unavailable, or output extends local/committed state, ambient env
selection, portal-only drift, or prose architecture modeling.

Rerun `scripts/skill-architecture-report.sh .` after skill edits.
