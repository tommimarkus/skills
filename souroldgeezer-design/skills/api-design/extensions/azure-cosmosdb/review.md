# Extension: azure-cosmosdb review lane

Review classifications and carve-outs for [the azure-cosmosdb core](../azure-cosmosdb.md).

## Load condition

Load this file in Review mode. In Extract, load it only when the user explicitly
requests a debt or compliance verdict. For a narrow Lookup, load it only when
the question asks for a finding code or carve-out. Do not load it in Build.

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
