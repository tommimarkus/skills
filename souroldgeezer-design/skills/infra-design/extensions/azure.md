# Azure Infrastructure Design Extension

Load this extension for Azure infrastructure design when source contains Azure
resource types, Azure CLI or PowerShell deployment commands, Azure resource IDs,
Azure Functions/App Service/Container Apps/AKS/Storage/Cosmos/Event Grid/Key
Vault/Application Insights signals, Azure Pipelines, or Azure resource-group,
subscription, tenant, or management-group vocabulary.

This extension adds Azure platform design evidence. It does not audit security
posture; delegate least privilege, exposed secrets, policy hardening, and
supply-chain concerns to `devsecops-audit`.

## Source Anchors

- Azure Well-Architected Framework:
  https://learn.microsoft.com/en-us/azure/well-architected/
- Azure architecture framework:
  https://learn.microsoft.com/en-us/azure/architecture/framework/
- Azure resource groups and resources:
  https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/manage-resource-groups-portal
- Azure managed identities:
  https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview
- Azure Monitor overview:
  https://learn.microsoft.com/en-us/azure/azure-monitor/overview

Use these anchors for platform facts only. Design quality is judged against the
core infrastructure reference.

## Project Assimilation Signals

Inspect:

1. Subscription, management-group, tenant, and resource-group structure in IaC
   and deployment commands.
2. Region and availability-zone placement for workload resources.
3. Managed identity assignments and Key Vault references as design
   dependencies.
4. Network boundaries: virtual networks, subnets, private endpoints, DNS zones,
   public ingress, and egress controls.
5. Observability wiring: Log Analytics workspaces, Application Insights, Azure
   Monitor alerts, diagnostic settings, and dashboard/query handoff.
6. Service-specific lifecycle boundaries for Functions, App Service, Container
   Apps, AKS, Storage, Cosmos, Event Grid, Service Bus, and Key Vault.
7. Azure Pipelines or GitHub Actions deployment identity and target
   subscription selection.

## Azure Design Defaults

- Put resource groups on lifecycle and operational ownership boundaries, not
  merely on resource type.
- Keep subscription and management-group placement explicit for production
  workloads.
- Treat region and zone choices as reliability and data-residency decisions;
  do not inherit defaults silently.
- Prefer managed identity as the runtime dependency boundary where supported.
- Keep Key Vault and secret references visible as configuration handoff, while
  delegating hardening findings to `devsecops-audit`.
- Declare observability resources and diagnostic routing before rollout.
- Keep private networking, DNS, and ingress decisions close to the workload or
  platform layer that owns them.
- Use Azure Well-Architected pillars as tradeoff lenses, not as generic review
  filler.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `azure.ID-TOP-1` | Resource group by resource type | Resource groups collect all storage, all compute, or all networking without lifecycle ownership. | warn |
| `azure.ID-TOP-2` | Implicit subscription target | Deployment relies on current CLI subscription or pipeline default. | warn; block for production |
| `azure.ID-TOP-3` | Region default by omission | Production resources omit region intent or mix regions without a data/resiliency reason. | warn |
| `azure.ID-ID-1` | Identity boundary hidden | Runtime access to dependencies is not represented by managed identity or another named actor. | warn |
| `azure.ID-NET-1` | Network dependency orphan | Private endpoint, DNS, subnet, ingress, or egress config lives outside workload/platform ownership. | warn |
| `azure.ID-OPS-1` | Diagnostic routing absent | Resource deploys without diagnostic setting, telemetry sink, or operations handoff. | warn |
| `azure.ID-EVO-1` | Portal-only platform drift | Source assumes resources or settings created only in the Azure portal. | warn |

## Review Notes

- Do not report least-privilege or secret exposure as `infra-design` findings;
  record a `devsecops-audit` delegation.
- Static IaC can show topology intent. It cannot prove availability, latency,
  cost, failover, backup success, or alert usefulness.
- When paired with Bicep or Terraform, report IaC-tool findings under the tool
  namespace and Azure topology findings under `azure.ID-*`.

## Applies To Reference Sections

Core sections 3.1, 3.5, 3.6, 3.7, 3.8, 3.9, and 3.10.
