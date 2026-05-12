# Bicep Lifting Rules

Use for Extract when Azure Bicep or ARM-style IaC is in scope.

## Elements

- Compute: Technology Node/System Software by hosting role.
- Storage, database, queue, secret, identity, network: model only when in scope.
- Environments/stages/migration resources: Implementation & Migration only with
  clear evidence.

## Relationships

- `dependsOn`, identity assignments, connection strings, and app settings can
  support Serving, Assignment, Realization, or Access.
- RBAC-only data paths should show the identity access path, not only the data
  resource.
- Parallel environments are not migration phases unless the source or architect
  intent says one state becomes another.

## Package Output

Preserve source evidence. Keep future-state/policy intent architect-owned. Use
source-backed groups for modules, resource groups, environments, trust zones, or
hosting boundaries; do not group every resource type or tag.
