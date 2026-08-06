# Extension: azure-blob-storage review lane

Review classifications and carve-outs for [the azure-blob-storage core](../azure-blob-storage.md).

## Load condition

Load this file in Review mode. In Extract, load it only when the user explicitly
requests a debt or compliance verdict. For a narrow Lookup, load it only when
the question asks for a finding code or carve-out. Do not load it in Build.

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
- **`blob.HC-11`** — GET of an archived blob returns 500 or blocks the Function thread instead of 202 plus asynchronous rehydration. *Layer:* static.
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
