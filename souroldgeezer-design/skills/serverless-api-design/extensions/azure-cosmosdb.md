# Extension: Azure Cosmos DB (NoSQL API)

Stack-specific additions to the `serverless-api-design` skill for Azure Cosmos DB (NoSQL API, `Microsoft.Azure.Cosmos` SDK v3). The core reference [`../../../docs/api-reference/serverless-api-design.md`](../../../docs/api-reference/serverless-api-design.md) stays framework-neutral; this extension layers Cosmos-specific primitives, patterns, and smells on top without overriding core rules.

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

## Stack-specific primitives

Signatures below are cited from the current `Microsoft.Azure.Cosmos` SDK v3 .NET API reference (2026-04-23). If the skill is applied to an older SDK minor, fall back to the SDK version's own ref page.

### Client lifetime

- **`CosmosClient`** — thread-safe, connection-pooling; singleton via DI in `Program.cs`. Construct with `DefaultAzureCredential` for data-plane RBAC.
- **`CosmosClientBuilder`** (`Microsoft.Azure.Cosmos.Fluent.CosmosClientBuilder`) — fluent configuration; use `.WithBulkExecution(true)`, `.WithApplicationPreferredRegions(...)`, `.WithConnectionModeDirect()`, `.WithSystemTextJsonSerializerOptions(JsonSerializerOptions)` (verified against SDK v3 — there is no `CosmosSystemTextJsonSerializer` class; older tutorials that show one are wrong for current SDK).
- **`CosmosClientOptions.AllowBulkExecution = true`** — required for bulk endpoints; the client batches writes across RUs.
- **`CosmosClientOptions.ApplicationPreferredRegions`** — ordered list of Azure regions the SDK prefers for reads; reduces cross-region latency.
- **`ConnectionMode.Direct`** (default) vs **`ConnectionMode.Gateway`** — Direct is faster; Gateway is firewall-friendly.

### Point reads vs queries

- **`container.ReadItemAsync<T>(id, partitionKey)`** — point read. Cheapest op (~1 RU per KB, <5 ms p95 typical). The only shape a `GET /resource/{id}` endpoint should emit.
- **`container.GetItemQueryIterator<T>(queryDefinition)`** — query iterator; use parameterised `QueryDefinition.WithParameter("@id", value)` — never concatenate user input into SQL.
- **Cross-partition queries** — occur when the `WHERE` clause lacks the partition-key path predicate. Each additional physical partition adds RU overhead; for hot API paths, restructure the model so the query is single-partition.

### Partition-key design

- **`PartitionKey`** — single-level partition key value.
- **`PartitionKeyBuilder`** — **hierarchical partition keys (HPK)**, **GA** (MSFT Learn: `azure/cosmos-db/hierarchical-partition-keys`). `new PartitionKeyBuilder().Add(tenantId).Add(userId).Add(id).Build()`. Escapes the 20 GB logical-partition limit for multi-tenant APIs without synthetic keys.
- Partition-key choice is an API-design decision: the dominant read pattern's filter fields should be the partition key, so GET-by-id becomes a point read.

### Optimistic concurrency

- **`ItemRequestOptions { IfMatchEtag = item._etag, EnableContentResponseOnWrite = false }`** — maps HTTP `If-Match` to Cosmos optimistic concurrency; 412 on mismatch. `EnableContentResponseOnWrite = false` drops the written item from the response body (default is `true`), saving RU and bandwidth on write-heavy paths. Property name is exactly `IfMatchEtag` (type `string`, lowercase `t` in `etag`) per `dotnet/api/microsoft.azure.cosmos.requestoptions.ifmatchetag`.
- **`CosmosException.StatusCode == HttpStatusCode.PreconditionFailed`** (= 412) — the SDK's surface for a failed `IfMatchEtag`.

### Idempotency

- **`ContainerProperties.DefaultTimeToLive`** (seconds) + per-item `ttl` field — auto-expires items. `-1` = never expire. Works only when indexing is enabled.
- **`UniqueKeyPolicy`** — server-side duplicate rejection on a named path; the primitive under idempotency-key caches.
- Combined, they give the `cosmos.PAT-idempotency-container` pattern: a dedicated container keyed on `Idempotency-Key` with 24 h TTL and unique-key on the key path.

### Transactions

- **`TransactionalBatch`** — atomic multi-op within a single logical partition, up to **100 ops / 2 MB / 5 s execution limit** (MSFT Learn: `azure/cosmos-db/transactional-batch`). Operations: create / read / replace / upsert / patch / delete. All succeed or all roll back.

### Change feed

- **`ChangeFeedProcessorBuilder`** (obtained from `container.GetChangeFeedProcessorBuilder(...)`) — at-least-once processor with lease container (required). Checkpoints automatically. The backbone of `cosmos.PAT-change-feed-202` (async API status) and `cosmos.PAT-change-feed-audit` patterns.
- **`[CosmosDBTrigger]`** isolated-worker binding — change-feed-backed Function trigger; params `databaseName`, `containerName`, `Connection`, `LeaseContainerName`, `StartFromBeginning`, `FeedPollDelay`, `MaxItemsPerInvocation`. MSFT Learn: `azure/azure-functions/functions-bindings-cosmosdb-v2`.
- **`[CosmosDBInput]`** with `{id}` and `{partitionKey}` binding expressions from the route — auto-routes to point read.

### Pagination

- **`FeedResponse<T>.ContinuationToken`** — opaque cursor returned by `GetItemQueryIterator<T>`; maps 1:1 to the core reference's §3.7 cursor pagination. The API's response cursor is this token (or `null`).
- **`QueryRequestOptions { MaxItemCount = limit, ContinuationToken = cursor }`** — page size cap + continuation.

### Cost observability

- **`ItemResponse<T>.RequestCharge`** / **`FeedResponse<T>.RequestCharge`** (RU consumed by the operation) — attach to response header (e.g., `x-request-charge: <ru>`) and/or emit as a structured log field (`requestChargeRU`).
- **`x-ms-retry-after-ms`** — response header on a Cosmos 429; forward to the HTTP client as `Retry-After` (converting ms → seconds, rounding up).
- **`x-ms-session-token`** — SDK-emitted header for session consistency tracking; can be forwarded to an API client if strict read-your-writes is required across a multi-hop client flow (rare).

### RBAC + identity

- **Data-plane RBAC roles** — **"Cosmos DB Built-in Data Contributor"** and **"Cosmos DB Built-in Data Reader"** (exact role names per MSFT Learn: `azure/cosmos-db/how-to-connect-role-based-access-control`). Assigned via `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` in IaC.
- **`disableLocalAuth: true`** at the account level — enforces RBAC-only data plane; blocks all key-based auth. The security baseline for added Cosmos accounts.

### Global distribution

- **`locations[]`** in IaC with `failoverPriority`, `isZoneRedundant`, `enableMultipleWriteLocations`.
- **`ApplicationPreferredRegions`** in SDK — ordered list; reads go to the first available region.
- **Conflict-resolution policy** — `LastWriterWins` (default) or `Custom` (stored procedure) for multi-region writes.

### Vector and full-text search

- **Vector search** — `vectorEmbeddings` and `vectorIndexes` (DiskANN **GA** per MSFT Learn: `azure/cosmos-db/vector-search`); `VectorDistance()` in SQL; `ORDER BY VectorDistance(c.embedding, @v)` with `TOP N`.
- **Full-text search is GA** (`FullTextContains()`, `FullTextScore()`, `fullTextIndexes` per MSFT Learn: `azure/cosmos-db/gen-ai/full-text-search` — no preview banner on the page as of 2026-04-23). `FullTextScore()` is usable only inside `ORDER BY RANK`. **Hybrid search** via `RRF()` under `ORDER BY RANK` is documented separately on `azure/cosmos-db/gen-ai/hybrid-search`. Specific sub-features remain "early preview" — **fuzzy search** and **multi-language full-text** — so the skill flags those sub-features as preview dependencies while treating the core capability as GA.

## Stack-specific patterns

### `cosmos.PAT-point-read-api` `[Both]`
`GET /resources/{id}` uses `container.ReadItemAsync<T>(id, new PartitionKey(partitionKey))` — never `GetItemQueryIterator<T>`. 404 surfaced on `CosmosException { StatusCode: HttpStatusCode.NotFound }`. Maps §3.1 / §3.16.

### `cosmos.PAT-etag-conditional` `[Both]`
GET returns `ETag: <item._etag>` header. PATCH / PUT accepts `If-Match: <etag>`, maps to `ItemRequestOptions.IfMatchEtag`. On `CosmosException { StatusCode: HttpStatusCode.PreconditionFailed }` emit 412 + problem+json. Maps §3.5 / §3.6.

### `cosmos.PAT-idempotency-container` `[Both]`
Dedicated container keyed on `Idempotency-Key` with `ContainerProperties.DefaultTimeToLive = 86400` (24 h) and `UniqueKeyPolicy` on the key path. POST handler checks the container first; hit → return cached response; miss → process, write `(key, status, body, headers)`, return response. Maps §3.6 / §5.6.

### `cosmos.PAT-continuation-cursor` `[Both]`
List endpoint: client sends `?limit=N&cursor=<opaque>`; server reads via `GetItemQueryIterator<T>(..., requestOptions: new QueryRequestOptions { MaxItemCount = limit, ContinuationToken = cursor })`; returns `{ items, nextCursor: response.ContinuationToken }`. Opaque to the client. Maps §3.7.

### `cosmos.PAT-change-feed-202` `[Both]`
POST mutates the primary container; a `ChangeFeedProcessor` (or `[CosmosDBTrigger]` Function) projects the mutation into a status container; GET `/jobs/{id}` reads the projection. Maps §3.9 / §5.3.

### `cosmos.PAT-transactional-batch` `[Both]`
Multi-op atomic endpoint using `container.CreateTransactionalBatch(partitionKey).CreateItemStream(...).PatchItemStream(...).ExecuteAsync()`. Single logical partition, up to 100 ops. Returns 200 on success, 409 on conflict (unique-key violation), 400 if ops exceed limits. Maps §3.6 / §5.6.

### `cosmos.PAT-bulk-import` `[Provisioned]`
Bulk-ingest endpoint with `CosmosClientOptions.AllowBulkExecution = true`; fire-and-forget tasks via `Task.WhenAll(items.Select(i => container.CreateItemAsync(i, ...)))`; per-item results collected. Returns 207 Multi-Status or 200 with per-item status array. Not recommended on `[Serverless]` (RU cap limits throughput). Maps §3.10 / §5.7.

### `cosmos.PAT-hpk-multitenant` `[Both]`
SaaS API uses hierarchical partition key (`PartitionKeyBuilder`) `/tenantId/entityType/id`. Tenant-scoped queries stay single-partition; tenant isolation is structural. Maps §3.1 / §3.16.

### `cosmos.PAT-rbac-client` `[Both]`
`new CosmosClient(accountEndpoint, new DefaultAzureCredential())` in DI singleton; no account key anywhere; IaC assigns `Cosmos DB Built-in Data Contributor` to the Function app's managed identity; `disableLocalAuth: true` on the account. Maps §3.3 / §3.17.

### `cosmos.PAT-otel-charge-header` `[Both]`
Every HTTP response emits `x-request-charge: <RequestCharge>` header (or structured log field `requestChargeRU`) so clients, dashboards, and load tests can attribute cost. Maps §3.14.

### `cosmos.PAT-session-token` `[Both]`
Strict read-your-writes across hops that lose client session state: capture `x-ms-session-token` from the write response, pass it on the subsequent read via `ItemRequestOptions.SessionToken`. Rare; document the reason. Maps §3.16.

### `cosmos.PAT-429-retry-after` `[Both]`
Cosmos 429 (throttled) carries `x-ms-retry-after-ms` header. Map to HTTP `Retry-After` (seconds, round up) on the API response; do not swallow or retry-in-place for a web API (let the client back off). Maps §3.10.

## Project assimilation (Cosmos-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **Capacity mode** — IaC `Microsoft.DocumentDB/databaseAccounts.properties.capabilities` for `EnableServerless`; otherwise provisioned. Record; flag serverless on high-throughput paths.
2. **Partition-key strategy** — grep for `CreateContainerIfNotExistsAsync`, `ContainerProperties { PartitionKeyPath }`, `ContainerProperties { PartitionKeyPaths }` (HPK). Record; check against dominant read patterns.
3. **Consistency level** — grep IaC for `consistencyPolicy.defaultConsistencyLevel` and code for `ItemRequestOptions.ConsistencyLevel` overrides. Record; flag `Strong` where `Session` would suffice.
4. **Indexing policy** — grep for `IndexingPolicy`, `IncludedPaths`, `ExcludedPaths`, `CompositeIndexes`, `VectorIndexes`, `FullTextIndexes`. Default is index-all; write-heavy APIs should tune.
5. **RBAC vs keys** — Bicep `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` = compliant; any `AccountKey=` in code or settings = immediate debt (`cosmos.HC-2`).
6. **`disableLocalAuth`** — IaC `Microsoft.DocumentDB/databaseAccounts.properties.disableLocalAuth`. Absent or `false` on added accounts → `cosmos.HC-3`.
7. **`EnableContentResponseOnWrite`** — grep `CosmosClientOptions`; default `true` on write-heavy paths wastes RU (`cosmos.HC-12`).
8. **`AllowBulkExecution`** — grep `CosmosClientOptions`; record whether bulk is enabled; pairs with `cosmos.PAT-bulk-import`.
9. **Change-feed leases** — grep for `GetChangeFeedProcessorBuilder`, `LeaseContainerName`, `[CosmosDBTrigger]`. Present → change-feed processor is in use; check lease container presence in IaC.
10. **Preferred regions** — grep `ApplicationPreferredRegions`; absence on multi-region accounts → `cosmos.HC-15`.

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

## Smell codes

### High-confidence

- **`cosmos.HC-1`** — `new CosmosClient(...)` constructed per invocation / per request (not singleton via DI). *Layer:* static.
- **`cosmos.HC-2`** — Account key / master key in code, app-settings literal, or `local.settings.json` committed. *Layer:* static + iac.
- **`cosmos.HC-3`** — `disableLocalAuth` unset or `false` on an account referenced by added code. Should be `true`. *Layer:* iac.
- **`cosmos.HC-4`** — GET-by-id endpoint uses `GetItemQueryIterator<T>` where `ReadItemAsync<T>` with known `(id, partitionKey)` applies. *Layer:* static.
- **`cosmos.HC-5`** — Concatenated SQL (user input spliced into query string) instead of `QueryDefinition.WithParameter(...)`. Injection risk plus plan-cache thrash. *Layer:* static.
- **`cosmos.HC-6`** — Mutating endpoint on a concurrently-writable resource ignores `_etag` / `IfMatchEtag`. Lost-update risk. *Layer:* static + contract.
- **`cosmos.HC-7`** — Idempotency on POST implemented by "check then write" without a unique-key container + TTL — race-prone. *Layer:* static + contract.
- **`cosmos.HC-8`** — Cross-partition query on a hot API path where single-partition is possible. Scaling hazard; RU cost grows with partition count. *Layer:* static.
- **`cosmos.HC-9`** — Pagination uses `OFFSET` / `SKIP` on a large container instead of `ContinuationToken`. Linear cost. *Layer:* static + contract.
- **`cosmos.HC-10`** — Cosmos 429 surfaced without forwarding `x-ms-retry-after-ms` as HTTP `Retry-After`. *Layer:* static.
- **`cosmos.HC-11`** — Non-deterministic API in a change-feed-driven projection that depends on deterministic checkpointing (e.g., time-based branch using `DateTime.UtcNow`). *Layer:* static.
- **`cosmos.HC-12`** — `EnableContentResponseOnWrite = true` (default) on a write-heavy endpoint where the response body is discarded. Wastes RU and bandwidth. *Layer:* static.
- **`cosmos.HC-13`** — Consistency level set tighter than needed (`Strong` on reads where `Session` suffices). *Layer:* static + iac.
- **`cosmos.HC-14`** — Change-feed processor without lease container / without checkpointing. At-most-once hazard. *Layer:* static + iac.
- **`cosmos.HC-15`** — Multi-region account missing `ApplicationPreferredRegions`. Every read hits the write region. *Layer:* static.

### Low-confidence

- **`cosmos.LC-1`** — Synthetic partition key where HPK would serve better on a multi-tenant model. Context-dependent. *Layer:* static.
- **`cosmos.LC-2`** — `MaxItemCount = -1` (unbounded) on list endpoints. Unbounded response size. *Layer:* static.
- **`cosmos.LC-3`** — Default index-all on a container where writes outnumber queries 10:1. Tune `IncludedPaths` / `ExcludedPaths`. *Layer:* static + iac.
- **`cosmos.LC-4`** — Stored procedure used where client-side logic + `TransactionalBatch` would be cleaner. *Layer:* static.
- **`cosmos.LC-5`** — TTL unset on idempotency-cache / session-token container; storage grows indefinitely. *Layer:* static + iac.

### Positive signals

- **`cosmos.POS-1`** — Singleton `CosmosClient` via DI with `DefaultAzureCredential` + `ApplicationPreferredRegions`.
- **`cosmos.POS-2`** — Point read for GET-by-id; query iterator reserved for list / search.
- **`cosmos.POS-3`** — `IfMatchEtag` on mutations; `CosmosException.PreconditionFailed` mapped to HTTP 412 + problem+json.
- **`cosmos.POS-4`** — Idempotency-Key container with `UniqueKeyPolicy` + `DefaultTimeToLive`.
- **`cosmos.POS-5`** — Cursor pagination via `ContinuationToken`; opaque to clients; `limit` capped.
- **`cosmos.POS-6`** — `disableLocalAuth: true` + RBAC role assignments; no keys anywhere.
- **`cosmos.POS-7`** — `EnableContentResponseOnWrite = false` on write-heavy paths.
- **`cosmos.POS-8`** — Change-feed trigger or processor with lease container + checkpointing for async 202 + polling / webhook delivery.
- **`cosmos.POS-9`** — `x-request-charge` header (or structured log field) emitted on responses for cost observability.
- **`cosmos.POS-10`** — Hierarchical partition key on a multi-tenant model.
- **`cosmos.POS-11`** — OpenTelemetry SDK source registered; RU and region attributes visible in traces.

## Carve-outs

Do not flag the following:

- Query iterator used intentionally for a cross-partition analytics endpoint with a documented RU budget and a request timeout. Require a comment.
- Stored procedure retained for an atomic cross-document invariant where `TransactionalBatch` doesn't fit. Require a comment.
- `ConsistencyLevel.Strong` on a single-region account where the application genuinely requires it (ledger, inventory, regulatory). Require a justifying comment (contrast `cosmos.HC-13` which targets unjustified `Strong`).
- Account key present in a legacy-only app setting that is being actively migrated out, documented in the assimilation footer as `Legacy debt`. Added code must not read it.
- Change-feed processor reading from `StartFromBeginning = true` on first run — this is the bootstrap, not a smell.
- `context.CurrentUtcDateTime` and `context.NewGuid()` inside a Durable orchestrator that also reads from Cosmos — these are deterministic and allowed.

## Applies to reference sections

§2.3, §2.5, §2.6, §2.7, §3.5, §3.6, §3.7, §3.9, §3.10, §3.11, §3.14, §3.16, §3.17, §4.5, §5.1, §5.2, §5.3, §5.6, §5.7, §5.8, §5.11, §6, §7.
