# Bicep Lifting Rules

Use for Extract when Azure Bicep or ARM-style IaC is in scope.

## Elements

- Compute resources become Technology Nodes or System Software according to
  their hosting role.
- Storage, database, queue, secret, identity, and network resources become
  Technology or passive-structure elements when they are part of the modeled
  feature.
- Environments, deployment stages, and migration resources can support
  Implementation & Migration elements when the workflow/IaC evidence is clear.

## Relationships

- `dependsOn`, explicit identity assignments, connection strings, and app
  settings can support Serving, Assignment, Realization, or Access
  relationships.
- RBAC-only data paths should show the identity access path, not only the data
  resource.
- Parallel environments are not migration phases unless the source or architect
  intent says one state becomes another.

## Package Output

Preserve source evidence on lifted elements. Keep future-state or policy intent
architect-owned unless the user supplies evidence.

Use source-backed groups for deployment modules, resource groups, environments,
network/trust zones, or hosting boundaries when the IaC expresses them. Do not
turn every resource type or tag value into a visual group.
