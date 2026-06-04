# Infrastructure Project Assimilation

Load when existing IaC, environment files, remote state, deployment workflows,
plan/what-if evidence, import/move records, generated artifacts, topology
documentation, architecture pairing, drift evidence, or diffs are in scope.

Direction is one-way: assimilate the project to the infra-design reference, not
the reference to the project. Reuse compliant infrastructure structure, flag
non-compliant structure as legacy debt, and never extend broken topology, IaC,
environment, state, identity, rollout, or drift practices into added code.

## Discovery

Inspect source-readable locations before deciding:

1. IaC roots and modules: Terraform roots/modules, Bicep entrypoints/modules,
   ARM templates, parameter/variable files, provider or module version pins,
   generated artifacts, and source-of-truth notes.
2. Environment strategy: environment directories, tfvars/bicepparam files,
   promotion workflows, subscription/resource-group selection, and defaults.
3. State and migration: backend config, state lock evidence, import blocks,
   moved blocks, state move notes, resource renames, and stateful replacement
   risks.
4. Deployment entrypoints: CI/CD workflows, scripts, plan/what-if gates,
   apply/deploy commands, approval gates, rollback hooks, and smoke checks.
5. Identity and configuration handoff: deployment identity, runtime identity,
   role-assignment ownership, secret references, app settings, and config
   ownership.
6. Operations and drift: telemetry sinks, alert/dashboard handoff,
   backup/restore expectation, cloud-control-plane evidence when supplied, and
   reconciliation process.
7. Architecture pairing: `docs/architecture/<feature>.dediren/` when topology,
   environment, identity, or rollout changes may affect architecture views.
8. Stack signals: load Azure, Terraform, or Bicep extensions when their files,
   resource names, manifests, or commands are present.

Loaded extensions own deeper platform/IaC-specific discovery and carve-outs.

## Reuse Or Migrate

| Asset | Reuse when | Flag or migrate when |
|---|---|---|
| IaC root / module | Matches ownership and lifecycle, exposes stable inputs/outputs, and keeps dependency direction visible | Thin resource wrapper, hidden platform dependency, or deep cascade that obscures blast radius |
| Environment model | Uses common source with declared parameter differences and promotion path | Copy-pasted topology forks or ambient subscription/workspace selection |
| State backend | Remote, locked, access-controlled, and owned by the team boundary | Local/committed state, unclear backend, or cross-state dependency sprawl |
| Migration record | Import/move/rename path is reviewable and protects stateful resources | Stateful replacement risk with no import/move note or rollback path |
| Deployment workflow | Runs plan/what-if before apply and names approval, verification, and rollback layer | Production apply without review, destructive change without approval, or no smoke/telemetry gate |
| Ops handoff | Telemetry sink, alert owner, dashboard/query, and restore expectation are source-visible | Observability afterthought, absent restore path, or portal-only drift |

## Conflict Handling

Classify conflicts as `reused`, `legacy debt`, `blocking debt`, or
`migration performed`.

- Added infrastructure changes must comply with the core reference and loaded
  extensions.
- Existing IaC can be reused only when it keeps source, state, rollout, and
  ownership reviewable.
- If requested work would depend on or extend blocking debt, stop and ask for
  migration scope or propose the smallest safe IaC/topology migration move.
- If a legacy pattern is not migrated, name the file, violated rule or finding
  code, and reason it remains out of scope.

## Footer Block

Use this shape when assimilation applies:

```text
Project assimilation:
  Reused: <compliant local IaC/env/state/rollout assets and evidence>
  Legacy debt: <file:line - rule or finding code - reason not migrated>
  Migrations performed: <file:line - rule or finding code fixed>
```
