# Extension: Azure Cosmos DB (NoSQL API)

Stack-specific additions to the `api-design` skill for Azure Cosmos DB (NoSQL API, `Microsoft.Azure.Cosmos` SDK v3). The core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md) stays framework-neutral; this extension layers Cosmos-specific detection, hosting, assimilation, and shared safety rules on top without overriding core rules.

Scope: the **NoSQL (Core SQL) API** only. Cosmos MongoDB, Cassandra, Gremlin, and Table APIs have different SDK surfaces and idioms; they are not covered here.

## Name and detection signals

The skill loads this extension when any of the following match:

- `.csproj` with `<PackageReference Include="Microsoft.Azure.Cosmos" ... />`.
- `using Microsoft.Azure.Cosmos;` OR `CosmosClient` / `Container` / `Database` / `PartitionKey` / `PartitionKeyBuilder` / `FeedResponse` / `QueryDefinition` types used in `.cs`.
- `[CosmosDBInput]` / `[CosmosDBTrigger]` / `[CosmosDBOutput]` attributes on a function parameter.
- `host.json` with an `extensions.cosmosDB` or `extensions.cosmosDb` block.
- `local.settings.json` or Bicep / Terraform containing `AccountEndpoint=https://*.documents.azure.com` or `.documents.azure.com` patterns.
- Bicep / Terraform defining `Microsoft.DocumentDB/databaseAccounts` with `kind: GlobalDocumentDB` (NoSQL API).
- IaC setting `disableLocalAuth: true` on a Cosmos account, or `capabilities: [{ name: EnableServerless }]`.

## Hosting-model surface

Rules tagged `[Provisioned]`, `[Serverless]`, or `[Both]`.

- **`[Provisioned]`** — fixed or autoscale RU/s; multi-region capable; multi-region writes supported; full feature set (stored procedures, change-feed full-fidelity, Synapse Link, etc.). The production-grade default.
- **`[Serverless]`** — consumption-style billing; **5000 RU/s maximum per container** and **20 GB per logical partition** (MSFT Learn: `azure/cosmos-db/concepts-limits`, `azure/cosmos-db/serverless-performance`); single-region; no multi-region writes. Cheapest for intermittent / bursty workloads; not suitable for steady high-throughput or multi-region. Caps are service-published and have historically been adjusted upward — re-check the limits page if the workload is near the ceiling.
- Rules that apply to both are tagged `[Both]`.

Pairing: Flex Consumption + Cosmos `[Serverless]` is the cheapest all-serverless API stack; Flex Consumption + Cosmos `[Provisioned]` (autoscale) is the production-grade default for public APIs.

## Mode lanes

This core file is the always-loaded azure-cosmosdb stack surface. Load exactly one
mode lane when the task requires it:

- **Build:** read [`azure-cosmosdb/build.md`](azure-cosmosdb/build.md) for detailed primitives and `*.PAT-*` implementation patterns.
- **Review:** read [`azure-cosmosdb/review.md`](azure-cosmosdb/review.md) for `*.HC-*`, `*.LC-*`, and `*.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Client lifetime
- Point reads vs queries
- Partition-key design
- Optimistic concurrency
- Idempotency
- Transactions
- Change feed
- Pagination
- Cost observability
- RBAC + identity
- Global distribution
- Vector and full-text search

Detailed signatures and implementation guidance live in [`azure-cosmosdb/build.md`](azure-cosmosdb/build.md).

## Shared safety invariants

- Reuse a singleton client, prefer point reads when id and partition key are known, and make partition strategy explicit.
- Use data-plane RBAC with managed identity and disable local/key authentication for added infrastructure.
- Preserve ETag preconditions, bounded continuation-token pagination, and measured request-charge evidence.
- Make retryable mutations idempotent and keep cross-partition or unbounded queries out of request hot paths.

## Project assimilation (Cosmos-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **Capacity mode** — IaC `Microsoft.DocumentDB/databaseAccounts.properties.capabilities` for `EnableServerless`; otherwise provisioned. Record; flag serverless on high-throughput paths.
2. **Partition-key strategy** — grep for `CreateContainerIfNotExistsAsync`, `ContainerProperties { PartitionKeyPath }`, `ContainerProperties { PartitionKeyPaths }` (HPK). Record; check against dominant read patterns.
3. **Consistency level** — grep IaC for `consistencyPolicy.defaultConsistencyLevel` and code for `ItemRequestOptions.ConsistencyLevel` overrides. Record; flag `Strong` where `Session` would suffice.
4. **Indexing policy** — grep for `IndexingPolicy`, `IncludedPaths`, `ExcludedPaths`, `CompositeIndexes`, `VectorIndexes`, `FullTextIndexes`. Default is index-all; write-heavy APIs should tune.
5. **RBAC vs keys** — Bicep `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` = compliant; any `AccountKey=` in code or settings = immediate debt.
6. **`disableLocalAuth`** — IaC `Microsoft.DocumentDB/databaseAccounts.properties.disableLocalAuth`. Absent or `false` on added accounts → the matching review rule.
7. **`EnableContentResponseOnWrite`** — grep `CosmosClientOptions`; default `true` on write-heavy paths wastes RU.
8. **`AllowBulkExecution`** — grep `CosmosClientOptions`; record whether bulk is enabled; the Build lane owns the matching bulk-import pattern.
9. **Change-feed leases** — grep for `GetChangeFeedProcessorBuilder`, `LeaseContainerName`, `[CosmosDBTrigger]`. Present → change-feed processor is in use; check lease container presence in IaC.
10. **Preferred regions** — grep `ApplicationPreferredRegions`; absence on multi-region accounts → the matching review rule.

### Mapping reference defaults to Cosmos idioms

| Reference default | Cosmos idiom |
|---|---|
| §3.5 error contract | `CosmosException.StatusCode` → HTTP (404 NotFound, 409 Conflict, 412 PreconditionFailed, 429 with `x-ms-retry-after-ms` → `Retry-After`); emit problem+json |
| §3.6 idempotency (PUT / DELETE) | `IfMatchEtag` → 412 |
| §3.6 idempotency (POST) | Dedicated container + `Idempotency-Key` + `DefaultTimeToLive` + `UniqueKeyPolicy` |
| §3.7 cursor pagination | `ContinuationToken` (opaque) |
| §3.10 rate limiting | 429 + forward `x-ms-retry-after-ms` as `Retry-After` (ms → seconds) |
| §3.14 observability | `ItemResponse.RequestCharge` / `FeedResponse.RequestCharge` → `x-request-charge` header + structured log field; SDK emits OpenTelemetry spans on ActivitySource `Azure.Cosmos.Operation` per `azure/cosmos-db/sdk-observability` |
| §3.16 data access | Singleton `CosmosClient` with `DefaultAzureCredential` + `ApplicationPreferredRegions` |
| §3.17 secrets | No account keys; RBAC role assignments; `disableLocalAuth: true` |

## Applies to reference sections

§2.3, §2.5, §2.6, §2.7, §3.5, §3.6, §3.7, §3.9, §3.10, §3.11, §3.14, §3.16, §3.17, §4.5, §5.1, §5.2, §5.3, §5.6, §5.7, §5.8, §5.11, §6, §7.
