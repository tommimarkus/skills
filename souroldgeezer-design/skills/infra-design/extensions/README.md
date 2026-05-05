# Infra Design Extensions

Extensions add platform and IaC-specific evidence to the core
`infra-design` workflow. They do not override the core reference at
`../../../docs/infra-reference/infra-design.md`.

## Load Order

1. Detect all matching signals in source files, manifests, deployment scripts,
   CI/CD workflows, and IaC roots.
2. Load every matching extension. Azure Bicep projects load both `azure.md` and
   `bicep.md`; Azure Terraform projects load both `azure.md` and
   `terraform.md`.
3. Apply extension design defaults, positive signals, and smell codes on top of
   the core reference.
4. Delegate security posture findings to `devsecops-audit` even when the source
   file is IaC.

## Current Extensions

| File | Applies to | Prefix |
|---|---|---|
| `azure.md` | Azure infrastructure design | `azure.ID-*` |
| `terraform.md` | Terraform IaC design | `terraform.ID-*` |
| `bicep.md` | Azure Bicep IaC design | `bicep.ID-*` |

## Adding an Extension

Add a new extension only when the platform or IaC tool has repeated design
signals that cannot be expressed cleanly by the core reference. Each extension
must include detection signals, source anchors, project assimilation signals,
design defaults, smell codes, review notes, and the reference sections it
augments.
