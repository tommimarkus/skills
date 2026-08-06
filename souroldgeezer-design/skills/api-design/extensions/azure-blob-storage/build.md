# Extension: azure-blob-storage build lane

Implementation detail for [the azure-blob-storage core](../azure-blob-storage.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

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
- Service SAS / account SAS (signed with `StorageSharedKeyCredential`) — rejected for added code; use user delegation only.

### Block-blob upload shapes

- **`BlobClient.UploadAsync(stream, options)`** — single-PUT for small payloads, auto-chunked for large ones via `StorageTransferOptions` (`InitialTransferSize`, `MaximumTransferSize`, `MaximumConcurrency`).
- **`BlockBlobClient.StageBlockAsync(blockId, stream)`** + **`CommitBlockListAsync(blockIds)`** — explicit Put Block / Put Block List for client-driven resumable uploads. Block IDs are stable and client-assigned; a retry of the same block ID is idempotent.
- Service limits: see `azure/storage/blobs/scalability-targets` for current block size, block count, and max blob size ceilings (historically raised; re-check when a workload is near a ceiling).

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
- **`[BlobTrigger(..., Source = BlobTriggerSource.EventGrid)]`** in isolated worker — modern near-real-time trigger per `azure/azure-functions/functions-bindings-storage-blob-trigger`. The enum is `BlobTriggerSource`; members are `EventGrid` and `LogsAndContainerScan` (default, legacy polling).
- Legacy `LogsAndContainerScan` polling — migrate to Event Grid source when it applies.

### Versioning, soft delete, immutable storage

- **Versioning** (`versioning.enabled: true` in IaC) — every write creates a new version with `versionId`. Reads can include `?versionId=` to access prior versions.
- **Soft delete** — container-level + blob-level retention windows (default 7 days); `UndeleteAsync` restores.
- **Immutable storage** — container-level **time-based retention** (locked vs unlocked) and **legal hold**. Both forms are WORM; write attempts during retention fail with 409.
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
