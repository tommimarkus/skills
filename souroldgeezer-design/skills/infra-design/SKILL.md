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
When a paired architecture model exists, the coupling path is
`docs/architecture/<feature>.dediren/`.

Inputs: files, diffs/proposals, topology, IaC roots/modules, env/state
constraints, deployment evidence, rollout policy, and ops signals. Do not infer
runtime/cost/quota/backup/failover/restore/rollout facts from static source. If
ambiguous, ask the user when mode/scope/env/source/evidence cost/destructive
edits/sibling ownership lacks a safe default; otherwise continue.

Modes: Build new/refactored infra; Extract existing design; Review IaC,
deployment proposals/PRs/plans; Lookup narrow infra-design tradeoffs.

## Load Map

Read [references/procedures/project-assimilation.md](references/procedures/project-assimilation.md) when existing IaC, state, environments, deployment/drift evidence, or diffs are in scope; that procedure lists the full trigger set.
Load [extensions/azure.md](extensions/azure.md) for Azure® resource/service/
subscription/tenant/RG/CLI/PowerShell/pipeline signals;
[extensions/terraform.md](extensions/terraform.md) for `.tf`, `.tfvars`,
backend, provider, module, plan/apply, or state; and
[extensions/bicep.md](extensions/bicep.md) for `.bicep`, `.bicepparam`,
`bicepconfig.json`, ARM, `module`, or `targetScope`. Azure+Bicep and
Azure+Terraform compose. Load [extensions/README.md](extensions/README.md) only
when editing extensions.

Detection identifies available guidance. In every mode, read only relevant core
and extension sections; expand for dependencies, uncertainty, or material risk.
Lookup may combine multiple needed stack excerpts without changing mode or
asking merely because more than one stack is involved. Azure+Bicep and Azure+Terraform may compose when the question needs both.

Before editing triggers/workflow/extensions/grounding/evals, load `references/evals` and `references/source-grounding.md`; keep evals synthetic/paraphrased.

## Workflow

1. Select mode/scope/question/env/evidence.
2. Prefer `rg`; inspect IaC roots/modules, deployment entrypoints/workflows,
   env/state files, generated artifacts, identity/config/observability/rollback
   signals, and architecture model pairing; apply project assimilation before
   choosing reuse, migration, drift/debt handling, or the next topology/IaC
   move.
3. Check for a paired `docs/architecture/<feature>.dediren/` package when
   topology, environment, identity, or rollout changes may affect architecture
   views.
4. Select relevant guidance, separate fact from inference, name verification
   layers, choose the smallest topology/IaC/env/state/rollout move, then report
   the result and material limits.

## Mode Outputs

- Build: scope/forces, topology, IaC structure, environment strategy,
  state/identity, ops, validation, delegations.
- Extract: relevant topology, IaC ownership, env/state, operations, and drift
  facts. Add debt or compliance judgments only when requested.
- Review: actionable findings about deployment coupling, state loss, authority,
  environment, identity, or operations. Gate the affected unsafe deployment or
  unsupported readiness claim; continue independent source-only review.
- Lookup: direct rule, exception, citation, delegation, one-line footer.

Lead with the result, relevant findings or changes, validation, and material
limits. Keep Lookup direct. Give a detailed mode/extension/layer/assimilation
inventory only when requested or needed by an actual consumer. Formal findings
retain their defined codes, file evidence, severity, consequence, and action;
omit unused fields and routine negative disclosures.

## Stop Conditions

<!-- lean-audit:sync-intentional: App and infra entries each retain the capability/evidence boundary inline so independently selected skills need not load one another. -->

Stop the affected action when authority or essential evidence is missing, or
when it would introduce a concrete unsafe or incompatible change. Disclose the
limited conclusion and continue useful independent work. Missing runtime,
visual, a11y, performance, or cloud evidence limits only the claim requiring it;
a reference difference or unavailable optional tool is not itself a task stop.
