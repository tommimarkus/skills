# Bicep Lifting Rules

Use for Extract when Azure Bicep or ARM-style IaC is in scope. Load
`../source-weighting.md` before classifying ambiguous cloud/platform evidence.

## Source Mapping

| Source evidence | Prefer | Avoid |
|---|---|---|
| Compute resource, hosting plan, function app, static web app | Technology Node, System Software, Technology Service, or hosting boundary by concern | Application Component because a workload is hosted there |
| Storage, database, queue, secret store, identity, network, monitor | Technology layer element or service when in scope | Business, Motivation, or Strategy element |
| App settings, connection strings, identities, RBAC, and diagnostics | Evidence for dependency/access/trust/observability paths | Standalone architecture claims without connected element |
| Resource groups/modules/environments | Source-backed groups when they reflect hosting, ownership, trust, or environment boundaries | Decorative groups for every resource type |
| Tags, parameter names, and SKU names | Metadata or weak evidence | Motivation, Capability, or lifecycle claims without external evidence |

Azure resource type decides platform/technology context, not application
semantics. Parallel environments are not migration phases unless the source or
architect intent says one state becomes another.

Tags, parameter names, and SKU names do not create Motivation, Capability, or lifecycle claims.

## Relationships

- `dependsOn`, app settings, and connection strings can support Serving,
  Access, Assignment, or Realization only when the claim is clear.
- Identity assignments and RBAC-only data paths should show the identity access
  path, not only the data resource.
- Diagnostics and monitoring should be included when observability is an
  architecture concern; otherwise keep them out of application collaboration
  views.

## Package Output

Preserve source evidence. Keep future-state/policy intent architect-owned. Use
source-backed groups for modules, resource groups, environments, trust zones, or
hosting boundaries; do not group every resource type or tag.
