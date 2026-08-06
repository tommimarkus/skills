# Extension: Azure Blob Storage (Block Blobs)

Stack-specific additions to the `api-design` skill for Azure Blob Storage (Block Blobs via `Azure.Storage.Blobs` SDK v12). The core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md) stays framework-neutral; this extension layers Blob-specific detection, hosting, assimilation, and shared safety rules on top without overriding core rules.

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

## Mode lanes

This core file is the always-loaded azure-blob-storage stack surface. Load exactly one
mode lane when the task requires it:

- **Build:** read [`azure-blob-storage/build.md`](azure-blob-storage/build.md) for detailed primitives and `*.PAT-*` implementation patterns.
- **Review:** read [`azure-blob-storage/review.md`](azure-blob-storage/review.md) for `*.HC-*`, `*.LC-*`, and `*.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Client lifetime and auth
- User-delegation SAS (the only SAS shape for added code)
- Block-blob upload shapes
- Range requests
- HTTP headers and metadata
- Conditional requests
- Pessimistic locking
- Access tiers and archive
- Event Grid and triggers
- Versioning, soft delete, immutable storage
- Blob change feed
- Network posture and encryption
- Integrity
- Blob copy

Detailed signatures and implementation guidance live in [`azure-blob-storage/build.md`](azure-blob-storage/build.md).

## Shared safety invariants

- Use managed identity and user-delegation SAS; do not add account keys or unrestricted service SAS.
- Prefer direct object-store transfer for large payloads and bound proxy streaming, range, and timeout behavior.
- Preserve ETag preconditions, content metadata, integrity validation, and asynchronous archive rehydration.
- Enable recovery controls appropriate to the data and keep public access disabled unless explicitly required.

## Project assimilation (Blob-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **`allowSharedKeyAccess`** — Bicep / Terraform `properties.allowSharedKeyAccess`. `true` (or absent) on an account referenced by added code → immediate debt.
2. **RBAC assignments** — `Microsoft.Authorization/roleAssignments` for Storage Blob Data Contributor / Reader / Delegator on the account or container. Present = compliant; absent + managed identity on Function app = broken posture.
3. **Account keys / service SAS in code** — grep for `StorageSharedKeyCredential`, `AccountKey=`, `new BlobServiceClient(connectionString)` where `connectionString` embeds a key, or `BlobSasBuilder.ToSasQueryParameters(sharedKeyCredential,...)`. Any hit → the matching review rule / the matching review rule.
4. **API-proxy uploads** — grep for `ReadAsStreamAsync` / form upload + `UploadAsync` on the Function side; typical shape of the matching review rule (large upload through the Function).
5. **API-proxy downloads** — grep for `BlobClient.DownloadAsync().Value.Content` → `MemoryStream` — the memory-exhaustion shape the matching review rule.
6. **Blob trigger source** — grep `[BlobTrigger(` for `Source = BlobTriggerSource.EventGrid` (modern) vs polling (legacy). Polling → the matching review rule.
7. **Public containers** — IaC `publicAccess: "Blob"` / `"Container"` on any container reachable from added code → the matching review rule.
8. **CORS rules** — IaC `corsRules[].allowedOrigins: ["*"]` on an account serving authenticated content → the matching review rule.
9. **Versioning / soft delete / immutability** — IaC `isVersioningEnabled`, `deleteRetentionPolicy`, `immutableStorageWithVersioning`. Record retention windows and whether they fit the API's compliance story.
10. **Network posture** — `publicNetworkAccess`, `networkAcls`, private endpoints. Record.
11. **API runtime memory / timeout vs largest payload accepted** — cross-check. If the API accepts 100 MB payloads through a memory-constrained runtime, flag the matching review rule / §3.12 — use direct-to-blob SAS.
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

## Applies to reference sections

§2.5, §2.6, §2.7, §2.8, §3.3, §3.5, §3.6, §3.9, §3.11, §3.12, §3.13, §3.14, §3.16, §3.17, §4.5, §5.3, §5.7, §5.11, §6, §7.
