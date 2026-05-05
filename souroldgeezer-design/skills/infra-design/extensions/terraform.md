# Terraform Infrastructure Design Extension

Load this extension for Terraform infrastructure design when source contains
`.tf`, `.tfvars`, `.terraform.lock.hcl`, backend or provider blocks, module
blocks, Terraform Cloud/Enterprise configuration, plan/apply commands, or
state backend references.

This extension targets Terraform design only. Do not make OpenTofu
compatibility claims in v1.

## Source Anchors

- Terraform modules:
  https://developer.hashicorp.com/terraform/language/modules/develop
- Terraform state:
  https://developer.hashicorp.com/terraform/language/state
- Terraform dependency lock file:
  https://developer.hashicorp.com/terraform/language/files/dependency-lock
- Terraform module composition:
  https://developer.hashicorp.com/terraform/language/modules/develop/composition
- Terraform moved blocks:
  https://developer.hashicorp.com/terraform/language/modules/develop/refactoring

Use these anchors for Terraform facts only. Design quality is judged against
the core infrastructure reference.

## Project Assimilation Signals

Inspect:

1. Root modules, child modules, and local or remote module sources.
2. Backend configuration, state storage, locking support, and workspace use.
3. Provider constraints, `.terraform.lock.hcl`, and provider alias ownership.
4. Variable and output contracts, including cross-state dependencies.
5. Environment strategy: workspaces, tfvars, directory-per-environment, or
   pipeline-injected variables.
6. Plan/apply automation and saved plan review.
7. Import, `moved`, `removed`, and state-refactor records.

## Terraform Design Defaults

- Keep root modules aligned to ownership and blast radius.
- Create child modules only for higher-level infrastructure concepts.
- Keep provider configuration and aliases close to the boundary that owns them.
- Use remote state with locking for team-managed infrastructure.
- Prefer explicit environment inputs over ambient workspace or shell state.
- Keep outputs narrow; broad remote-state reads couple rollout order.
- Commit `.terraform.lock.hcl` for provider reproducibility.
- Record imports and address moves with source-visible migration constructs or
  reviewed plan notes.
- Review `terraform plan` before `apply`; unexpected destroy/replace actions
  are review stops.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `terraform.ID-IAC-1` | Thin wrapper module | Module only wraps one provider resource and adds no workload concept. | info; warn when mandatory |
| `terraform.ID-IAC-2` | Provider alias leakage | Child modules require callers to understand provider alias internals. | warn |
| `terraform.ID-IAC-3` | Module source drift | Remote module source lacks a stable version/ref where plan behavior can change. | warn |
| `terraform.ID-ENV-1` | Workspace-as-environment ambiguity | Workspace name controls environment without a source-visible promotion rule. | warn |
| `terraform.ID-STATE-1` | Local team state | Backend is local or absent for team-managed infrastructure. | block |
| `terraform.ID-STATE-2` | State dependency sprawl | Many root modules read each other's remote state outputs. | warn |
| `terraform.ID-STATE-3` | Missing moved/import record | Resource address or ownership changes without `moved`, import notes, or plan evidence. | warn; block for stateful resources |
| `terraform.ID-EVO-1` | Provider lock absent | Provider constraints exist without a committed `.terraform.lock.hcl`. | warn |
| `terraform.ID-OPS-1` | Apply without reviewed plan | Automation can apply without a saved or reviewable plan. | warn; block for production |

## Review Notes

- Terraform state can contain sensitive data; do not request or copy state
  contents into the skill output. Review state design, not secret values.
- Static Terraform can show intended resource graph and backend posture. It
  cannot prove cloud runtime behavior.
- Security posture from provider permissions, secrets, and CI credentials is a
  `devsecops-audit` delegation.

## Applies To Reference Sections

Core sections 3.2, 3.3, 3.4, 3.9, and 3.10.
