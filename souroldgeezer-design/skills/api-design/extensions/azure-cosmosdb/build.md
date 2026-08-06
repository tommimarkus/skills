# Extension: azure-cosmosdb build lane

Implementation detail for [the azure-cosmosdb core](../azure-cosmosdb.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

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
