# Lifting rules — Bicep to ArchiMate® Technology Layer

Rules for lifting ArchiMate® **Technology Layer** elements from Bicep IaC (the dialect the sibling design skills produce). Invoked by Extract mode.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). This procedure cites §4.3 (Technology Layer elements) and §7.1 (extractability per layer).

## Sources read

- `*.bicep` files across the repository (typically under `infra/`, `deploy/`, or repo-root).
- `bicepconfig.json` for module resolution (non-authoritative for ArchiMate content; used only to resolve cross-module references).
- Parameter files (`*.bicepparam`, `*.parameters.json`) — read for SKUs and region names where they affect System Software / Node stereotype labels.

Out of scope: ARM JSON templates (if the project uses ARM directly rather than Bicep, flag as a stack the procedure doesn't support in v1); Terraform; Pulumi.

## Mapping rules — resource types to ArchiMate elements

### Compute / hosting → Node + System Software

| Bicep resource | ArchiMate element | Notes |
|---|---|---|
| `Microsoft.Web/serverfarms` | **Node** — *App Service Plan* | Record SKU (`Y1` / `EP1–3` / `FC1` / `P*`) as a label suffix |
| `Microsoft.Web/sites` with `kind: 'functionapp'` or `kind: 'functionapp,linux'` | **Node** — *Function App*; + **System Software** — *Azure Functions runtime* with `FUNCTIONS_WORKER_RUNTIME` as version label (default: dotnet-isolated) | Composed on the serverfarm Node via Composition |
| `Microsoft.Web/sites` with `kind: 'app'` or `kind: 'app,linux'` | **Node** — *App Service (Web App)* | Composed on serverfarm Node |
| `Microsoft.Web/staticSites` | **Node** — *Static Web App* | Hosts the Blazor WASM / static Application Component; relationship to the Component is **Assignment** |
| `Microsoft.App/managedEnvironments` | **Node** — *Container Apps Environment* | |
| `Microsoft.App/containerApps` | **Node** — *Container App* | Composed on the environment Node |
| `Microsoft.ContainerService/managedClusters` (AKS) | **Node** — *AKS cluster* | |
| `Microsoft.Compute/virtualMachines` | **Node** — *Virtual Machine* | |

### Data services → Node (+ System Software) + Artifact

| Bicep resource | ArchiMate element |
|---|---|
| `Microsoft.DocumentDB/databaseAccounts` | **Node** — *Cosmos DB account*; System Software — *Cosmos DB NoSQL* (or Mongo / Cassandra / Gremlin based on `properties.kind`) |
| `Microsoft.DocumentDB/databaseAccounts/sqlDatabases` | **Artifact** — *database* composed on the Cosmos Node |
| `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers` | **Artifact** — *container*; composed on the database Artifact |
| `Microsoft.Storage/storageAccounts` | **Node** — *Storage account* |
| `...storageAccounts/blobServices/containers` | **Artifact** — *blob container* |
| `...storageAccounts/queueServices/queues` | **Artifact** — *queue* |
| `Microsoft.Sql/servers` | **Node** — *Azure SQL server* |
| `Microsoft.Sql/servers/databases` | **Artifact** — *SQL database* composed on the server |
| `Microsoft.Cache/redis` | **Node** — *Azure Cache for Redis* |
| `Microsoft.ServiceBus/namespaces` | **Node** — *Service Bus namespace* |
| `Microsoft.EventGrid/topics` / `Microsoft.EventGrid/systemTopics` | **Node** — *Event Grid (custom)* / *Event Grid (system)* |

### Identity / secrets → Node + Technology Service

| Bicep resource | ArchiMate element |
|---|---|
| `Microsoft.KeyVault/vaults` | **Node** — *Key Vault* |
| `Microsoft.ManagedIdentity/userAssignedIdentities` | **Node** — *User-assigned Managed Identity*, labelled with identity name; also emits a **Technology Service** representing the identity principal when it participates in Access relationships |
| `identity: { type: 'SystemAssigned' }` on `Microsoft.Web/sites`, `Microsoft.App/containerApps`, or another supported resource | **Technology Service** — *{resource name} managed identity (system-assigned)*, composed on the owning resource Node |

Role assignments do not emit elements of their own; they emit **Access** relationships from the Managed Identity Technology Service to the protected resource Node / Artifact. Record the role name or role GUID in relationship documentation and set the Access relationship name to `Read`, `Write`, or `ReadWrite`.

### Network → Communication Network + Path

| Bicep resource | ArchiMate element |
|---|---|
| `Microsoft.Network/virtualNetworks` | **Communication Network** — *VNet* |
| `Microsoft.Network/virtualNetworks/subnets` | Composed on the VNet; rendered as a Communication Network subdivision |
| `Microsoft.Network/privateEndpoints` | **Path** between the consuming Node and the resource Node |
| `Microsoft.Network/networkSecurityGroups` | Not emitted as an ArchiMate element; NSG rules annotate the Path |
| `Microsoft.Cdn/profiles` / `Microsoft.Network/frontDoors` / `Microsoft.Network/applicationGateways` | **Node** — *CDN / Front Door / App Gateway* |

### Observability → Node

| Bicep resource | ArchiMate element |
|---|---|
| `Microsoft.Insights/components` (Application Insights) | **Node** — *Application Insights* |
| `Microsoft.OperationalInsights/workspaces` | **Node** — *Log Analytics workspace* |

### API surface → Application Interface + Application-to-Technology relationships

| Bicep resource | ArchiMate handling |
|---|---|
| `Microsoft.ApiManagement/service` | **Node** — *API Management service* |
| `Microsoft.ApiManagement/service/apis` | Not a Technology element — surfaces the Application Interface that the APIM exposes to consumers; emits an **Application Interface** on the corresponding Application Component (linked via [lifting-rules-dotnet.md](lifting-rules-dotnet.md)) with APIM as the **Used-by** intermediary |

## Relationships between Technology elements

- **Composition** — from plan Node to hosted Function App / App Service Node (serverfarm Composes Function App). From storage account Node to blob container / queue Artifact. From Cosmos Node to database → container Artifact chain.
- **Composition** — from a resource Node to its system-assigned Managed Identity Technology Service.
- **Assignment** — from a user-assigned Managed Identity Node / Technology Service to the Node that uses it (`identity: { type: 'UserAssigned', userAssignedIdentities: { ... } }` in a `Microsoft.Web/sites` resource emits Assignment from the identity to the site Node).
- **Access** — from a Managed Identity Technology Service to the protected Cosmos, Storage, Key Vault, Service Bus, or other RBAC-scoped resource. `Microsoft.Authorization/roleAssignments` and `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` are the primary source.
- **Flow** — from a source resource Node to Log Analytics when `Microsoft.Insights/diagnosticSettings` sends logs / metrics to a workspace.
- **Path** — between Nodes connected by a Private Endpoint or peered VNet.
- **Used-by** — from an Application Component (.NET project) to the Technology Node that hosts its runtime dependencies (Cosmos, Storage, Service Bus) — the cross-layer relationship is the whole point of a Technology Usage view (reference §9.4).

## Security relationship lifting

Apply these mappings before Application-to-Technology links are finalised:

| Bicep pattern | Emit |
|---|---|
| System-assigned identity on a resource | Technology Service named `{ResourceName} managed identity (system-assigned)`; Composition from the resource Node to that service |
| User-assigned identity resource referenced by another resource | Managed Identity Node plus Technology Service; Assignment from identity to each resource that uses it |
| `Microsoft.Authorization/roleAssignments` whose `principalId` resolves to a managed identity | Access from the identity service to the role scope resource; name `Read`, `Write`, or `ReadWrite` from role semantics |
| Cosmos `databaseAccounts/sqlRoleAssignments` built-in Reader / Contributor GUIDs | Access from the identity service to the Cosmos account or database/container Artifact; name `Read` for Reader and `ReadWrite` for Contributor |
| `Microsoft.Insights/diagnosticSettings` with `workspaceId` | Flow from the diagnostic source Node to the Log Analytics workspace Node |
| App setting value matching `@Microsoft.KeyVault(SecretUri=...)` | Access from the consuming resource's identity service to a Key Vault Secret Artifact |
| `disableLocalAuth: true`, `allowSharedKeyAccess: false`, `enableRbacAuthorization: true` | Property or documentation marker on the protected Node: `rbac-only=true` |
| `publicNetworkAccess: 'Disabled'` with private endpoints | Communication Network / Path elements linking the consuming Node and protected resource |

Review reports `AD-18` when a resource marked `rbac-only=true` is used by an Application Component but no Managed Identity Access path to that resource exists in the model.

## Application-to-Technology linking

The lifting procedure assumes the Application Layer has already been lifted by [lifting-rules-dotnet.md](lifting-rules-dotnet.md). The cross-layer relationships are emitted as:

| Detection in code + IaC | ArchiMate relationship |
|---|---|
| `.csproj` Azure Functions Component + a `Microsoft.Web/sites` resource in the same deployment | **Assignment** from the Function App Node to the Component (the Node hosts the Component) |
| `.csproj` Blazor WASM standalone + `Microsoft.Web/staticSites` | **Assignment** from the Static Web App Node to the Blazor Component |
| Component using `CosmosClient` / `Microsoft.Azure.Cosmos` + `Microsoft.DocumentDB/databaseAccounts` | **Used-by** from the Component to the Cosmos Node |
| Component using `BlobServiceClient` / `Azure.Storage.Blobs` + `Microsoft.Storage/storageAccounts` | **Used-by** from the Component to the Storage Node |
| Component using `SecretClient` / `Azure.Security.KeyVault.Secrets` + `Microsoft.KeyVault/vaults` | **Used-by** from the Component to the Key Vault Node |
| Component using `ServiceBusClient` + `Microsoft.ServiceBus/namespaces` | **Used-by** from the Component to the Service Bus Node |

Where the code evidence is absent, the relationship is not emitted — the skill does not invent links from IaC alone, because an IaC resource may exist to serve many Components or future Components.

## Naming conventions

- **Node identifier** — `id-<slug>` where `<slug>` is the Bicep symbolic name lowercased with dots/underscores replaced by hyphens.
- **Node `<name>`** — resource `name` property, or the architect's chosen name if already present in the canonical model.
- **Artifact identifier** — parent resource identifier + child name joined by hyphen (`id-cosmos-main-ordersdb-orders`).
- **Path identifier** — `id-path-<source>-<target>`.

## Output shape

Lifted elements are emitted as OEF XML into the canonical file at `docs/architecture/<feature>.oef.xml`. Fragment:

```xml
<!-- ==== Technology Layer (lifted from infra/main.bicep) ==== -->

<elements>
  <element identifier="id-funcapp-orders" xsi:type="Node">
    <name xml:lang="en">Orders Function App (FC1)</name>
  </element>
  <element identifier="id-funcapp-runtime-orders" xsi:type="SystemSoftware">
    <name xml:lang="en">Azure Functions runtime — dotnet-isolated 8.0</name>
  </element>
  <element identifier="id-cosmos-main" xsi:type="Node">
    <name xml:lang="en">Cosmos DB account — NoSQL, serverless</name>
  </element>
  <element identifier="id-cosmos-main-ordersdb" xsi:type="Artifact">
    <name xml:lang="en">orders database</name>
  </element>
  <element identifier="id-cosmos-main-ordersdb-orders" xsi:type="Artifact">
    <name xml:lang="en">orders container</name>
  </element>
  <element identifier="id-storage-main" xsi:type="Node">
    <name xml:lang="en">Storage account — StorageV2</name>
  </element>
  <element identifier="id-kv-main" xsi:type="Node">
    <name xml:lang="en">Key Vault</name>
  </element>
  <element identifier="id-mi-orders" xsi:type="Node">
    <name xml:lang="en">Managed Identity — orders-api</name>
  </element>
  <element identifier="id-mi-orders-service" xsi:type="TechnologyService">
    <name xml:lang="en">orders-api managed identity</name>
  </element>
</elements>

<relationships>
  <relationship identifier="id-rel-funcapp-runtime"
                source="id-funcapp-orders" target="id-funcapp-runtime-orders"
                xsi:type="Composition"/>
  <relationship identifier="id-rel-cosmos-db"
                source="id-cosmos-main" target="id-cosmos-main-ordersdb"
                xsi:type="Composition"/>
  <relationship identifier="id-rel-db-container"
                source="id-cosmos-main-ordersdb" target="id-cosmos-main-ordersdb-orders"
                xsi:type="Composition"/>
  <relationship identifier="id-rel-mi-funcapp"
                source="id-mi-orders" target="id-funcapp-orders"
                xsi:type="Assignment"/>
  <relationship identifier="id-rel-mi-cosmos-access"
                source="id-mi-orders-service" target="id-cosmos-main"
                xsi:type="Access">
    <name xml:lang="en">ReadWrite</name>
  </relationship>

  <!-- ==== Application-to-Technology (cross-layer links) ==== -->

  <relationship identifier="id-rel-funcapp-hosts-api"
                source="id-funcapp-orders" target="id-orders-api"
                xsi:type="Assignment"/>
  <relationship identifier="id-rel-api-uses-cosmos"
                source="id-orders-api" target="id-cosmos-main"
                xsi:type="Serving"/>
  <relationship identifier="id-rel-api-uses-kv"
                source="id-orders-api" target="id-kv-main"
                xsi:type="Serving"/>
</relationships>
```

The cross-layer `<relationship>`s reference `id-orders-api` — an Application Component emitted by [lifting-rules-dotnet.md](lifting-rules-dotnet.md). When both procedures run against the same feature, their element sets merge into a single `<elements>` block and their relationship sets into a single `<relationships>` block in the canonical file.

## What this procedure does not do

- Lift **Physical Layer** (Equipment / Facility / Distribution Network / Material). Forward-only in v1 — see reference §4.4 and §7.2.
- Infer relationships from IaC alone without code corroboration (see "Application-to-Technology linking" above).
- Produce Archi-native `.archimate` XML. That is a different format; this procedure emits OEF XML only.
- Validate that the Bicep itself is well-formed — that is the domain of [`devsecops-audit`](../../../../../souroldgeezer-audit/skills/devsecops-audit/SKILL.md) and of Bicep's own linter.
