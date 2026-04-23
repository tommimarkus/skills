# Extension: Azure Blob Storage (Block Blobs)

Stack-specific additions to the `serverless-api-design` skill for Azure Blob Storage (Block Blobs via `Azure.Storage.Blobs` SDK v12). The core reference [`../../../docs/api-reference/serverless-api-design.md`](../../../docs/api-reference/serverless-api-design.md) stays framework-neutral; this extension layers Blob-specific primitives, patterns, and smells on top without overriding core rules.

Scope: **Block Blobs** (the common case for API payloads). Append Blobs and Page Blobs are out of scope. ADLS Gen2 hierarchical-namespace accounts (`isHnsEnabled=true`) are not covered here; the ACL surface differs and warrants a separate extension.

## Name and detection signals

The skill loads this extension when any of the following match:

- `.csproj` with `<PackageReference Include="Azure.Storage.Blobs" ... />`.
- `using Azure.Storage.Blobs;` / `Azure.Storage.Blobs.Models;` / `Azure.Storage.Sas;` OR `BlobServiceClient` / `BlobContainerClient` / `BlobClient` / `BlockBlobClient` / `BlobSasBuilder` / `UserDelegationKey` / `BlobRequestConditions` types used in `.cs`.
- `[BlobInput]` / `[BlobTrigger]` / `[BlobOutput]` attributes on a function parameter.
- `host.json` with an `extensions.blobs` block.
- `local.settings.json` / Bicep / Terraform containing `.blob.core.windows.net` or `BlobEndpoint=` patterns.
- Bicep / Terraform defining `Microsoft.Storage/storageAccounts` resources.
- IaC setting `allowSharedKeyAccess`, `supportsHttpsTrafficOnly`, `publicNetworkAccess`, or `minimumTlsVersion` on a storage account.

## Hosting-model surface

Rules tagged `[SAS-direct]`, `[API-proxy]`, or `[Both]`.

- **`[SAS-direct]`** — the API mints a scoped user-delegation SAS; the client uploads / downloads directly against Blob Storage; the Function never sees the payload. The default for uploads over ~25 MB or any download that can be offloaded. The escape hatch for §3.12 payload-size limits.
- **`[API-proxy]`** — the API streams the payload through the Function to / from Blob Storage. Only when the Function must transform or inspect the payload in flight (virus scan, watermark, format convert, auth-per-byte). Bounded by Function memory, timeout, and plan limits.
- Rules that apply to both shapes are tagged `[Both]`.

## Stack-specific primitives

Signatures and limits below are cited from the current `Azure.Storage.Blobs` v12 .NET API reference and `azure/storage/blobs/scalability-targets` (2026-04-23). Service-published values have historically been raised — re-check when a workload is near a ceiling.

### Client lifetime and auth

- **`BlobServiceClient`** — thread-safe; singleton via DI in `Program.cs`. Construct with `DefaultAzureCredential` and the service URI (e.g., `new BlobServiceClient(new Uri("https://<account>.blob.core.windows.net"), new DefaultAzureCredential())`). No connection strings with account keys.
- **`BlobClientOptions`** — tune retry (default exponential, 3 retries), transport pipeline, diagnostics; `BlobClientOptions.Retry.MaxRetries`, `BlobClientOptions.Diagnostics.IsLoggingEnabled`.
- **RBAC data-plane roles** — **Storage Blob Data Reader** (read-only), **Storage Blob Data Contributor** (read + write), **Storage Blob Data Owner** (full), **Storage Blob Delegator** (mints user-delegation SAS via `generateUserDelegationKey/action`). Storage Blob Data Contributor also includes the `generateUserDelegationKey/action` permission. Assigned via IaC.
- **`allowSharedKeyAccess: false`** at the account level (MSFT Learn: `azure/storage/common/shared-key-authorization-prevent`) — the hard kill-switch that blocks all account-key, service-SAS, and account-SAS auth. Only Microsoft Entra ID (OAuth) + user-delegation SAS work. The security baseline.

### User-delegation SAS (the only SAS shape for added code)

- **`BlobServiceClient.GetUserDelegationKeyAsync(startsOn, expiresOn, ct)`** with positional `DateTimeOffset?` / `DateTimeOffset` arguments is the shape shown in the current `azure/storage/blobs/storage-blob-user-delegation-sas-create-dotnet` walkthrough; a `BlobGetUserDelegationKeyOptions` overload also exists for structured args. Both return a `Response<UserDelegationKey>`. Prefer the options form when composing non-trivial SAS issuance (IP range, start-time skew tolerance).
- **`UserDelegationKey`** — the returned key material; feeds into `BlobSasBuilder.ToSasQueryParameters(userDelegationKey, accountName)`.
- **`BlobSasBuilder`** — SAS parameters. Typical shape:
  ```csharp
  var sas = new BlobSasBuilder
  {
      BlobContainerName = container,
      BlobName          = blobName,
      Resource          = "b",                 // single blob
      StartsOn          = DateTimeOffset.UtcNow.AddMinutes(-1),
      ExpiresOn         = DateTimeOffset.UtcNow.AddMinutes(15),
      Protocol          = SasProtocol.Https,   // HTTPS-only
      IPRange           = new SasIPRange(...)  // optional, zero-trust
  };
  sas.SetPermissions(BlobSasPermissions.Write);  // or Read / Create / List
  var query = sas.ToSasQueryParameters(userDelegationKey, accountName);
  ```
- Expiry ≤ 15 minutes for uploads, ≤ 60 minutes for downloads (typical). Scope: single blob (`Resource = "b"`). Protocol: always `SasProtocol.Https`.
- Service SAS / account SAS (signed with `StorageSharedKeyCredential`) — **flagged** as `blob.HC-3`; the added code uses user-delegation only.

### Block-blob upload shapes

- **`BlobClient.UploadAsync(stream, options)`** — single-PUT for small payloads, auto-chunked for large ones via `StorageTransferOptions` (`InitialTransferSize`, `MaximumTransferSize`, `MaximumConcurrency`).
- **`BlockBlobClient.StageBlockAsync(blockId, stream)`** + **`CommitBlockListAsync(blockIds)`** — explicit Put Block / Put Block List for client-driven resumable uploads. Block IDs are stable and client-assigned; a retry of the same block ID is idempotent.
- Limits per `azure/storage/blobs/scalability-targets`: **block size ≤ 4000 MiB**, up to **50,000 blocks** per blob, max block blob size **~190.7 TiB** (50,000 × 4000 MiB).

### Range requests

- **`BlobClient.DownloadStreamingAsync(BlobDownloadOptions options = null, CancellationToken ct = default)`** with `BlobDownloadOptions { Range = new HttpRange(offset, length) }` — returns a partial stream. Service response: 206 Partial Content + `Content-Range`; 416 on invalid range. `BlobClient.DownloadAsync` materializes the full response; `BlockBlobClient` exposes the same download surface for block-blob-specific flows.

### HTTP headers and metadata

- **`BlobHttpHeaders { ContentType, CacheControl, ContentDisposition, ContentEncoding, ContentLanguage, ContentHash }`** — set on upload via `BlobUploadOptions.HttpHeaders`, or post-hoc via `BlobClient.SetHttpHeadersAsync(...)`. These become the downstream response headers when the blob is served via SAS or Front Door.
- Custom metadata — `x-ms-meta-<name>` headers; ASCII only; **up to 8 KB total per blob** per `rest/api/storageservices/setting-and-retrieving-properties-and-metadata-for-blob-resources`. Atomic replace via `SetMetadataAsync(...)` — no partial update.

### Conditional requests

- **`BlobRequestConditions { IfMatch, IfNoneMatch, IfModifiedSince, IfUnmodifiedSince }`** — optimistic concurrency. `IfMatch` accepts an `ETag` (Azure.ETag). Mismatch surfaces as `RequestFailedException { Status: 412 }`.
- Map HTTP `If-Match` → `BlobRequestConditions.IfMatch = new ETag(clientEtag)`; on 412 emit HTTP 412 + problem+json.
- `If-None-Match` + ETag on GET: returns 304 Not Modified on match (cache validation).

### Pessimistic locking

- **`BlobLeaseClient`** — acquire / renew / release lease (15–60 s or infinite). `x-ms-lease-id` header required on subsequent writes. Prefer optimistic ETag unless contention is genuinely high; leases add operational complexity.

### Access tiers and archive

- **`AccessTier.Hot`** / **`Cool`** / **`Cold`** / **`Archive`** (MSFT Learn: `azure/storage/blobs/access-tiers-overview`).
- **Archive** blobs are offline; GET returns an error until rehydrated. Rehydration: **`SetAccessTierAsync(AccessTier.Hot, RehydratePriority.Standard)`** — per `azure/storage/blobs/archive-rehydrate-overview`: **standard** priority up to **15 hours** for objects under 10 GB; **high** priority **under 1 hour** for objects under 10 GB.
- **Rehydration as async API** — GET on archived blob returns 202 + `Location: /jobs/{id}`; the job polls `ArchiveStatus` or subscribes to `Microsoft.Storage.BlobTierChanged` Event Grid event to complete.

### Event Grid and triggers

- Event Grid events: `Microsoft.Storage.BlobCreated`, `Microsoft.Storage.BlobDeleted`, `Microsoft.Storage.BlobTierChanged`, `Microsoft.Storage.BlobRenamed`. These drive §3.9 async ingress and archive-rehydration-complete patterns.
- **`[BlobTrigger(..., Source = BlobTriggerSource.EventGrid)]`** in isolated worker — modern near-real-time trigger per `azure/azure-functions/functions-bindings-storage-blob-trigger`. The enum is `BlobTriggerSource`; members are `EventGrid` and `LogsAndContainerScan` (default, legacy polling — what `blob.HC-6` flags).
- Legacy `LogsAndContainerScan` polling — flagged `blob.HC-6`; migrate to Event Grid source.

### Versioning, soft delete, immutable storage

- **Versioning** (`versioning.enabled: true` in IaC) — every write creates a new version with `versionId`. Reads can include `?versionId=` to access prior versions.
- **Soft delete** — container-level + blob-level retention windows (default 7 days); `UndeleteAsync` restores.
- **Immutable storage** — container-level **time-based retention** (locked vs unlocked) and **legal hold**. Both forms are WORM — `[blob.HC-9]` write attempts during retention fail with 409.
- Versioning + legal hold combine; document the edge cases (some write shapes are blocked even with versioning enabled under legal hold).

### Blob change feed

- **`$blobchangefeed`** hidden container per `azure/storage/blobs/storage-blob-change-feed` — "Change feed records are stored in the `$blobchangefeed` container." Records are serialized as **Apache Avro** (compact binary format with inline schema). Use for audit / projection pipelines that must not miss events.

### Network posture and encryption

- **Private endpoint** (Azure Private Link) — blob service reachable only from a VNET; the Function app must be VNET-integrated. SAS URLs still work over the private endpoint.
- **Firewall** — IP allowlist on the storage account; secondary to private endpoint.
- **Encryption at rest** — Microsoft-managed keys (AES-256) default; customer-managed keys (CMK) via Key Vault optional. CMK rotation: document the key-vault-unreachable failure mode (blocks all data-plane ops).
- **Client-side encryption** — `Azure.Storage.Blobs.Specialized.ClientSideEncryptionOptions`; legacy, rarely justified when server-side encryption + TLS covers the threat model.

### Integrity

- **`Content-MD5`** / **`x-ms-content-crc64`** — integrity checksums on upload; the SDK computes and attaches them. Enforced by the service.
- Reject malformed uploads where `Content-Length` mismatches bytes or checksum fails.

### Blob copy

- **Sync copy** (same account, same region, small blob) — `BlobClient.StartCopyFromUriAsync` + immediate completion.
- **Async copy** (cross-account, large blob) — `StartCopyFromUriAsync` returns a `CopyFromUriOperation`; poll `GetProperties().Value.CopyStatus` or use `WaitForCompletionAsync()`.

## Stack-specific patterns

### `blob.PAT-direct-upload-sas` `[SAS-direct]`
Client calls `POST /uploads` → API mints a user-delegation SAS (write permission, ≤15-min expiry, HTTPS-only, single-blob scope) and returns `{ uploadUrl, blobUri, expiresAt }`. Client PUTs the payload directly to `uploadUrl`. API never sees the payload; Function memory and timeout irrelevant. The canonical escape hatch for §3.12 large payloads.

### `blob.PAT-direct-download-sas` `[SAS-direct]`
Client calls `GET /downloads/{id}` → API (after auth check) returns 302 redirect to a user-delegation SAS URL (read permission, narrow expiry), or 200 with JSON `{ downloadUrl, expiresAt }`. Client streams from Blob Storage, not from the Function.

### `blob.PAT-resumable-upload` `[SAS-direct]`
Large-file upload with client-driven resumability: `POST /uploads/init` → session ID + block-size recommendation + user-delegation SAS; client chunks, uploads blocks with stable IDs via `StageBlockAsync`; `POST /uploads/{session}/finalize` commits via `CommitBlockListAsync`. Per-block retry is idempotent. Maps §5.7.

### `blob.PAT-eventgrid-async` `[SAS-direct]`
Client uploads via SAS; Event Grid fires `Microsoft.Storage.BlobCreated`; `[BlobTrigger(Source = EventGrid)]` Function (isolated worker) projects the blob into an API resource; GET `/status/{id}` returns state. Maps §3.9 / §5.11.

### `blob.PAT-etag-conditional` `[Both]`
GET returns `ETag: <blob.ETag>`; PUT / DELETE accepts `If-Match: <etag>`; map to `BlobRequestConditions.IfMatch`. `RequestFailedException { Status: 412 }` → HTTP 412 + problem+json. Maps §3.5 / §3.6.

### `blob.PAT-range-download` `[API-proxy]`
API forwards `Range` header to `BlobClient.DownloadStreamingAsync(new BlobDownloadOptions { Range = new HttpRange(offset, length) })`; returns 206 + `Content-Range`; 416 on bad range. Use only when the API must mediate (auth-per-byte, watermarking) — otherwise prefer `blob.PAT-direct-download-sas`.

### `blob.PAT-archive-rehydrate` `[Both]`
GET on archived blob → 202 + `Location: /jobs/{id}`; `SetAccessTierAsync(AccessTier.Hot, RehydratePriority.Standard)` starts rehydration; `BlobTierChanged` Event Grid event fires the status record update. Clients poll the status endpoint. Maps §3.9.

### `blob.PAT-rbac-no-keys` `[Both]`
`new BlobServiceClient(serviceUri, new DefaultAzureCredential())`; storage account has `allowSharedKeyAccess: false`; RBAC role assignments in IaC (Storage Blob Data Contributor on the container for the Function app's managed identity; Storage Blob Delegator if minting user-delegation SAS). Maps §3.3 / §3.17.

### `blob.PAT-http-headers-on-upload` `[Both]`
Upload endpoint sets `BlobHttpHeaders { ContentType = <validated>, CacheControl = "...", ContentDisposition = "..." }`; these become the response headers when the blob is served via SAS or Front Door. API-layer content-type validation prevents stored-XSS vectors. Maps §3.11 / §3.13.

### `blob.PAT-change-feed-audit` `[Both]`
Audit / compliance endpoint reads `$blobchangefeed` via the change-feed client; immutable log of writes feeds a downstream projection or audit UI. Maps §3.14 / §5.11.

### `blob.PAT-cdn-front` `[SAS-direct]`
Public read-only content served via Azure Front Door or Azure CDN with the storage account as origin. SAS origin auth or managed-identity origin (Front Door → Storage via private link). CORS on the storage account (never wildcard on authenticated content). Maps §3.13.

### `blob.PAT-streaming-download` `[API-proxy]`
When the API must mediate (token introspection, watermarking, per-byte auth), stream via `BlobClient.OpenReadAsync(new BlobOpenReadOptions { BufferSize = ... })` — never `DownloadAsync().Value.Content` into a `MemoryStream`. Pair with a bounded `buffer-size` to keep Function memory predictable. Maps §3.12.

## Project assimilation (Blob-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **`allowSharedKeyAccess`** — Bicep / Terraform `properties.allowSharedKeyAccess`. `true` (or absent) on an account referenced by added code → immediate debt, `blob.HC-2`.
2. **RBAC assignments** — `Microsoft.Authorization/roleAssignments` for Storage Blob Data Contributor / Reader / Delegator on the account or container. Present = compliant; absent + managed identity on Function app = broken posture.
3. **Account keys / service SAS in code** — grep for `StorageSharedKeyCredential`, `AccountKey=`, `new BlobServiceClient(connectionString)` where `connectionString` embeds a key, or `BlobSasBuilder.ToSasQueryParameters(sharedKeyCredential, ...)`. Any hit → `blob.HC-1` / `blob.HC-3`.
4. **API-proxy uploads** — grep for `ReadAsStreamAsync` / form upload + `UploadAsync` on the Function side; typical shape of `blob.HC-4` (large upload through the Function).
5. **API-proxy downloads** — grep for `BlobClient.DownloadAsync().Value.Content` → `MemoryStream` — the memory-exhaustion shape `blob.HC-5`.
6. **Blob trigger source** — grep `[BlobTrigger(` for `Source = BlobTriggerSource.EventGrid` (modern) vs polling (legacy). Polling → `blob.HC-6`.
7. **Public containers** — IaC `publicAccess: "Blob"` / `"Container"` on any container reachable from added code → `blob.HC-7`.
8. **CORS rules** — IaC `corsRules[].allowedOrigins: ["*"]` on an account serving authenticated content → `blob.HC-8`.
9. **Versioning / soft delete / immutability** — IaC `isVersioningEnabled`, `deleteRetentionPolicy`, `immutableStorageWithVersioning`. Record retention windows and whether they fit the API's compliance story.
10. **Network posture** — `publicNetworkAccess`, `networkAcls`, private endpoints. Record.
11. **Function memory / timeout vs largest payload accepted** — cross-check. If the API accepts 100 MB payloads on a Consumption-plan 1.5 GB-memory Function, flag `blob.HC-4` / §3.12 — use direct-to-blob SAS.
12. **Event Grid subscriptions** — any subscription to blob events on the account; record.

### Mapping reference defaults to Blob idioms

| Reference default | Blob idiom |
|---|---|
| §3.5 error contract | `RequestFailedException.Status` → HTTP (404, 409, 412, 416); emit problem+json |
| §3.6 idempotency (PUT / DELETE) | `BlobRequestConditions.IfMatch` → 412 |
| §3.6 idempotency (bulk upload) | Block-ID-stable Put Block / Put Block List |
| §3.9 async patterns | Event Grid trigger + 202; archive rehydration as async |
| §3.11 input validation | Content-Type allowlist on upload SAS request; `Content-Length` / checksum checks |
| §3.12 payload size | Direct-to-blob user-delegation SAS escape hatch |
| §3.14 observability | SDK OpenTelemetry (via `Azure.Core` diagnostics); `x-ms-client-request-id` propagation |
| §3.16 data access | Singleton `BlobServiceClient` with `DefaultAzureCredential` |
| §3.17 secrets | `allowSharedKeyAccess: false` + user-delegation SAS + RBAC role assignments |

## Smell codes

### High-confidence

- **`blob.HC-1`** — Storage account key in code, app-settings literal, or committed `local.settings.json`. *Layer:* static + iac.
- **`blob.HC-2`** — `allowSharedKeyAccess: true` (or unset) on an account referenced by added code. Should be `false`. *Layer:* iac.
- **`blob.HC-3`** — Service SAS or account SAS minted via `StorageSharedKeyCredential`. Should be user-delegation SAS via `GetUserDelegationKeyAsync`. *Layer:* static.
- **`blob.HC-4`** — API reads a large upload (form / multipart / request body) into memory, then re-uploads to Blob. Violates §3.12; memory-exhaustion risk; should be direct-to-blob SAS. *Layer:* static.
- **`blob.HC-5`** — API streams a large download by loading the blob into a `MemoryStream` before returning. Should be `OpenReadAsync` streaming or SAS redirect. *Layer:* static.
- **`blob.HC-6`** — `[BlobTrigger]` using legacy polling source mode where Event-Grid source applies. *Layer:* static.
- **`blob.HC-7`** — Public-read container access level (`Blob` / `Container`) on content that has any user identity or tenancy. *Layer:* iac.
- **`blob.HC-8`** — CORS `AllowedOrigins: ["*"]` on a storage account backing authenticated API reads. *Layer:* iac.
- **`blob.HC-9`** — Mutating blob endpoint on a concurrently-writable resource ignores `ETag` / `If-Match`. Lost-update risk. *Layer:* static + contract.
- **`blob.HC-10`** — SAS expiry absent, far-future (> 24 h for write, > 7 days for read), not scoped to a single blob (`Resource != "b"`), or missing a permission narrow (e.g., `All`). *Layer:* static.
- **`blob.HC-11`** — GET of an archived blob returns 500 or blocks the Function thread instead of 202 + rehydration pattern (`blob.PAT-archive-rehydrate`). *Layer:* static.
- **`blob.HC-12`** — Upload endpoint accepts any `Content-Type` without an allowlist, enabling stored-XSS or malicious-file delivery. *Layer:* static + contract.
- **`blob.HC-13`** — Missing `x-ms-client-request-id` / `traceparent` propagation to blob SDK calls; breaks correlation between API traces and storage traces. *Layer:* static.
- **`blob.HC-14`** — User-delegation SAS minted without `SasProtocol.Https`; allows HTTP in the SAS URL. *Layer:* static.
- **`blob.HC-15`** — Isolated-worker blob output uses `IAsyncCollector<>` shape; that is the in-process-model idiom. Use a return-type with output-binding attribute on a property or `[BlobOutput]` multi-output. *Layer:* static.

### Low-confidence

- **`blob.LC-1`** — Upload endpoint uses single-PUT for large payloads where Put Block + Put Block List would give resumability. *Layer:* static.
- **`blob.LC-2`** — `Cache-Control` / `Content-Disposition` not set on upload; downstream CDN / browser caches incorrectly or serves blobs with wrong disposition. *Layer:* static.
- **`blob.LC-3`** — Pessimistic blob lease where optimistic ETag would suffice; contention is typically rare. *Layer:* static.
- **`blob.LC-4`** — Archive tier on data that is read within the API's SLA window; read-on-archive is effectively 404. *Layer:* iac.
- **`blob.LC-5`** — Soft-delete retention unset, or versioning enabled without a retention / cleanup budget. Cost drift. *Layer:* iac.

### Positive signals

- **`blob.POS-1`** — Singleton `BlobServiceClient` via DI with `DefaultAzureCredential`; no keys.
- **`blob.POS-2`** — Account-level `allowSharedKeyAccess: false` in IaC.
- **`blob.POS-3`** — User-delegation SAS, ≤ 15 min expiry, `SasProtocol.Https`, single-blob resource, minimum-viable permission.
- **`blob.POS-4`** — Direct-to-blob upload pattern: client PUTs to SAS; Function never touches the payload.
- **`blob.POS-5`** — Event-Grid-sourced `[BlobTrigger]` in isolated worker.
- **`blob.POS-6`** — `BlobRequestConditions.IfMatch` on mutations; 412 mapped to problem+json.
- **`blob.POS-7`** — `BlobHttpHeaders` set on upload for `ContentType`, `CacheControl`, `ContentDisposition`.
- **`blob.POS-8`** — Archive rehydration exposed as async 202 + status pattern, driven by `BlobTierChanged` Event Grid event.
- **`blob.POS-9`** — Content-Type allowlist + `Content-Length` cap on upload SAS request.
- **`blob.POS-10`** — OpenTelemetry `Azure.Core` diagnostics registered; blob traces carry `traceparent` and `x-ms-client-request-id`.

## Carve-outs

Do not flag the following:

- Public-read container when content is genuinely public static assets (marketing images, public-release documents) and a CDN is in front. Require a justifying comment and a documented content-type allowlist.
- `[API-proxy]` upload when the Function must inspect the payload (virus scan, format convert, watermark, auth-per-byte). Document the memory / timeout budget in a comment; flag only if the budget is not documented.
- Service SAS retained for a legacy third-party integration that cannot use OAuth / user-delegation. Document as legacy debt in the assimilation footer; do not extend to new integrations.
- Container-scoped SAS (`Resource = "c"`) instead of blob-scoped (`Resource = "b"`) when the API genuinely hands a client a container write area for a batch operation. Require a comment documenting the expiry (≤ 1 h) and the specific permission set.
- ETag check skipped on append-only / write-once resources (audit-entry writes where the blob is WORM by design). Must be documented in a comment.
- Polling blob trigger retained for a local dev / emulator workflow where Event Grid is not configured. Document and replace in production IaC.

## Applies to reference sections

§2.5, §2.6, §2.7, §2.8, §3.3, §3.5, §3.6, §3.9, §3.11, §3.12, §3.13, §3.14, §3.16, §3.17, §4.5, §5.3, §5.7, §5.11, §6, §7.
