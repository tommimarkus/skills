# Bicep Infrastructure Design Extension

Load this extension for Azure Bicep infrastructure design when source contains
`.bicep`, `.bicepparam`, `bicepconfig.json`, ARM deployment commands, `module`
declarations, `targetScope`, or Bicep parameter files.

This extension covers Bicep design shape. Azure platform topology findings use
`azure.ID-*` when the Azure extension also loads.

## Source Anchors

- Bicep documentation:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/
- Bicep modules:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/modules
- Bicep CLI:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-cli
- Bicep parameters:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/parameters
- Deployment what-if:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if

Use these anchors for Bicep facts only. Design quality is judged against the
core infrastructure reference.

## Project Assimilation Signals

Inspect:

1. `targetScope` in each deployable file.
2. Module declarations, module paths, and module output usage.
3. Parameter files and environment-specific `.bicepparam` files.
4. `@secure()` parameters or outputs and Key Vault reference handoff.
5. `bicepconfig.json` analyzer settings and module aliases.
6. Generated ARM JSON files and source-of-truth rules.
7. Validation commands: `bicep build`, `bicep lint`, and deployment what-if.

## Bicep Design Defaults

- Set `targetScope` deliberately and keep deployment-scope ownership visible.
- Split modules by workload/platform concept, not by every resource type.
- Keep module parameters and outputs narrow and stable.
- Use `.bicepparam` or explicit deployment parameters for environment
  differences.
- Mark sensitive parameters or outputs with secure decorators where the
  platform supports them, and delegate secret hardening to `devsecops-audit`.
- Treat generated ARM JSON as rebuildable unless a repository rule states it is
  the reviewed artifact.
- Run `bicep build` and `bicep lint` before what-if; run what-if before apply.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `bicep.ID-SCOPE-1` | Ambiguous target scope | File omits or obscures deployment scope where module/resource ownership depends on it. | warn |
| `bicep.ID-IAC-1` | Resource-type module split | Modules mirror single Azure resource types instead of workload/platform concepts. | info; warn when mandatory |
| `bicep.ID-IAC-2` | Broad module output | Module outputs whole resource objects or sensitive values when callers need narrow fields. | warn |
| `bicep.ID-ENV-1` | Parameter copy drift | Environment parameter files duplicate values with unexplained structural differences. | warn |
| `bicep.ID-SEC-1` | Secret handoff unclear | Secure parameter or Key Vault handoff is missing for values shaped like secrets. | warn; delegate hardening |
| `bicep.ID-EVO-1` | Generated ARM source ambiguity | Generated ARM JSON is committed without a rebuild or source-of-truth rule. | warn |
| `bicep.ID-OPS-1` | What-if absent | Deployment path can apply without what-if review. | warn; block for production |

## Review Notes

- Use `bicep.ID-SEC-*` only for design handoff. Concrete secret exposure or
  least-privilege findings belong to `devsecops-audit`.
- Bicep source can show deployment intent. It cannot prove cloud runtime
  behavior, backup success, failover behavior, or cost.
- When Azure-specific topology is also at issue, load `azure.md` and use both
  namespaces.

## Applies To Reference Sections

Core sections 3.2, 3.3, 3.5, 3.7, 3.9, and 3.10.
