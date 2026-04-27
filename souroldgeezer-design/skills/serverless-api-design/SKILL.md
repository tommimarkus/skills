---
name: serverless-api-design
description: Use when building, reviewing, or looking up modern serverless HTTP APIs — endpoints, services, or features built on Azure® Functions™ (.NET™) with Azure® Cosmos DB™ and/or Azure® Blob Storage™ data layers. Applies the bundled reference at souroldgeezer-design/docs/api-reference/serverless-api-design.md, enforcing security (Microsoft® Entra ID™ / managed identities / Azure® Key Vault™ / data-plane RBAC, `disableLocalAuth` on Azure® Cosmos DB™ and `allowSharedKeyAccess=false` on Azure® Blob Storage™), contract discipline (OpenAPI™ 3.1, RFC 9457 problem+json, explicit versioning, RFC 9110 conditional requests via ETag), reliability (idempotency on mutations, safe retries, 429 + Retry-After, poison / dead-letter), and observability (structured logs, W3C® traceparent, correlation ID, per-request RU / request-charge visibility) as hard baselines. Supports build, review, and lookup modes with a matching subagent and composable extensions for Azure® Functions™ on .NET™, Azure® Cosmos DB™, and Azure® Blob Storage™.
---

# Serverless API Design

## Overview

Help Claude produce and review serverless HTTP APIs that are correct by construction across contract, security, reliability, and observability — before the first load test, and regardless of which compute plan or data service sits underneath. The central problem, from §1 of the reference:

> Presence vs. efficacy — a function that responds to a curl command is not evidence that the API holds up under retries, ships a stable error contract, survives key rotation, emits correlated telemetry, handles 429 from its own data store, survives a cold start inside a p95 budget, or degrades sensibly when the downstream dependency is the one throttling. An HTTP status code is not a contract.

**The reference is [../../docs/api-reference/serverless-api-design.md](../../docs/api-reference/serverless-api-design.md)** (bundled with the plugin). This skill is the *workflow* for applying it. Generated code embodies the reference's defaults; review output cites reference sections and RFC / MSFT Learn sources by reference; the skill never duplicates reference prose.

## Non-goals

- **General .NET code quality** → out of scope; produce working API code, don't lint surrounding logic. The `test-quality-audit` and `devsecops-audit` skills in the `souroldgeezer-audit` plugin cover the audit side.
- **Verification of runtime SLIs** (p95 latency, cold-start, error rate, RU charge) → static signals only. Real numbers need load tests (Azure Load Testing / k6), RUM, Azure Monitor, and Application Insights; surface this honestly.
- **Wire-format choice** — gRPC, GraphQL, SOAP — reference §8 out-of-scope; decline and redirect.
- **AWS Lambda / Google Cloud Functions** — core principles port, but primitives and extensions do not; out-of-scope for now.
- **Data-model design / DDD / event-sourcing** — this skill handles the contract and runtime; modelling belongs elsewhere.

## Modes

### Build mode (primary)

**Use for:** creating an endpoint, service, API surface, or feature from scratch.

**Triggers:** "build an endpoint", "design an API for …", "create a serverless …", "how should I expose …", "implement this service", "make me a POST /…", "add a function for …".

### Review mode

**Use for:** reviewing existing API code against the reference checklist.

**Triggers:** "review this function", "is this API idempotent", "audit this endpoint", "does this meet the contract", "check this against §7", "API review", "review these endpoints".

### Lookup mode

**Use for:** a specific, narrow question — which status code, which header, which pattern, which binding.

**Triggers:** "which status code for X", "how do I version this", "should I use Durable or a queue", "what's the shape of problem+json", "which auth level here".

**Default:** If the request is ambiguous, ask the user which mode they want.

## Extensions

The core workflow is framework-neutral. Extensions are per-stack packs loaded on demand. **Multiple extensions compose on the same target** — an API on Azure Functions .NET that stores entities in Cosmos and blobs in Storage loads all three extensions at once, and each adds orthogonal guidance (compute + query patterns + object patterns) without colliding:

| Extension | Applies to | Loaded when target matches |
|---|---|---|
| `extensions/azure-functions-dotnet.md` | Azure Functions .NET isolated worker | `.csproj` with `Microsoft.Azure.Functions.Worker`, OR `host.json` at repo root, OR `[Function(...)]` attribute in `.cs`, OR `FunctionsApplication.CreateBuilder` / `ConfigureFunctionsWebApplication()` in `Program.cs`, OR `HttpRequestData` / `HttpResponseData` / `HttpRequest` (ASP.NET Core integration) usage in a function class |
| `extensions/azure-cosmosdb.md` | Azure Cosmos DB (NoSQL API) | `Microsoft.Azure.Cosmos` package ref in `.csproj`, OR `CosmosClient` / `Container` / `PartitionKey` / `PartitionKeyBuilder` in `.cs`, OR `[CosmosDBInput]` / `[CosmosDBTrigger]` / `[CosmosDBOutput]` attributes, OR `extensions.cosmosDB` / `cosmosDb` block in `host.json`, OR `AccountEndpoint=https://*.documents.azure.com` patterns in `local.settings.json` / Bicep / Terraform, OR `disableLocalAuth` / `capabilities: EnableServerless` on Cosmos accounts in IaC |
| `extensions/azure-blob-storage.md` | Azure Blob Storage (Block Blobs) | `Azure.Storage.Blobs` package ref in `.csproj`, OR `BlobServiceClient` / `BlobContainerClient` / `BlobClient` / `BlobSasBuilder` / `UserDelegationKey` in `.cs`, OR `[BlobInput]` / `[BlobTrigger]` / `[BlobOutput]` attributes, OR `extensions.blobs` block in `host.json`, OR `.blob.core.windows.net` / `BlobEndpoint=` patterns in settings / IaC, OR `allowSharedKeyAccess` / `supportsHttpsTrafficOnly` on storage accounts in IaC |

Multiple extensions load when the target matches multiple sets of signals. Unknown stacks proceed with only the core reference. See `extensions/README.md` for adding an extension.

Extensions **never override** core rules. They add stack-specific primitives, patterns, and smells (namespaced `<ext>.HC-N` / `<ext>.LC-N` / `<ext>.POS-N`), or carve out false positives for idiomatic stack patterns. Carve-outs win only for the exact pattern described. Smell-code namespaces (`afdotnet.*`, `cosmos.*`, `blob.*`, core `SAD-*`) are distinct by construction, so findings from multiple extensions never collide.

## Pre-flight (build & review)

Before writing or reviewing code, confirm the following. If the user hasn't supplied them, ask — don't invent answers:

1. **Consumer scope.** First-party UI, third-party partners, machine-to-machine only? Default: mixed; design for public-contract discipline (OpenAPI, stable error types, cursor pagination, 429 + `Retry-After`).
2. **Auth model.** Entra ID (OAuth 2.0 / OIDC) + managed identity, function keys, Easy Auth, Anonymous? Default: Entra ID + managed identity, no secrets in code.
3. **Framework / hosting stack.** Azure Functions (.NET)? Detect via `.csproj` + `host.json`; otherwise ask. Identify isolated worker vs the retiring in-process model; refuse to author in-process-model code (retired 2026-11-10).
4. **Hosting plan target.** Consumption / Flex Consumption / Premium / Dedicated? Default: Flex Consumption for public APIs; Consumption for internal low-traffic; Premium when p95 cold-start must be ~0.
5. **Reliability posture.** Idempotency required on mutations? Retry tolerance of clients? Default: idempotency on all mutations; safe retry + backoff on all outbound calls.
6. **Observability target.** Application Insights / OpenTelemetry exporter / team SLO? Default: register OpenTelemetry in `Program.cs` per the current `azure/azure-functions/functions-opentelemetry` page plus end-to-end `traceparent`.
7. **Architecture pairing.** Does a paired ArchiMate model exist at `docs/architecture/<feature>.oef.xml` for the feature in scope? If yes: in review mode, the skill auto-dispatches to `architecture-design` Review for drift detection (§ Review mode workflow step 6); in build mode, the architect can opt in ("also update the architecture diagram") to dispatch to `architecture-design` Extract after Build. Default: auto-detect the path for review mode; opt-in for build mode.

If any answer changes a decision's default (e.g., "internal only, no client SDKs generated" → §3.2 URI-path versioning becomes header versioning), state the deviation explicitly in the output.

## Project assimilation (before build & review)

**Direction is one-way: the project is assimilated to the reference, not the reference to the project.** The reference's security / contract / reliability / observability baselines are non-negotiable; its decision defaults (§3) are the target state. Assimilation means discovering what the project ships so output (a) reuses compliant infrastructure instead of duplicating it, and (b) surfaces non-compliant infrastructure as legacy debt rather than silently extending it.

Before emitting code or opening a review on an existing project, run the discovery pass below. Keep detection lightweight — canonical locations only. If nothing found, assume greenfield and emit the §4.5 baseline contract.

### Framework-agnostic discovery

Do this pass every time, regardless of stack:

1. **OpenAPI / contract** — grep for `swagger.json`, `openapi.yaml`, `openapi.json`, `*.openapi.*`, or OpenAPI-generating packages in `.csproj` (`Microsoft.Azure.Functions.Worker.Extensions.OpenApi`, `Swashbuckle.*`, `Microsoft.OpenApi.*`). If absent, treat as contract-first greenfield — the skill generates an OpenAPI document as part of Build mode.
2. **Error shape** — grep for `application/problem+json`, `ProblemDetails`, `TypedResults.Problem`, `Results.Problem`, custom error DTOs. Compliant → reuse; custom error shape → flag as legacy debt, emit problem+json in added code, never extend the custom shape.
3. **Versioning** — grep for `/v1/`, `/v2/`, `api-version=`, `Asp.Versioning`. Record the strategy; flag if two strategies coexist (URI path + query parameter on different endpoints is a §3.2 deviation).
4. **Auth config** — grep for `AuthorizationLevel.`, `[Authorize]`, Easy Auth settings (`authsettingsV2`), Entra ID app-registration references, managed identity usage in IaC, function-keys-only patterns. Record the approach.
5. **Secrets** — grep for `@Microsoft.KeyVault(`, raw connection strings or access keys in `local.settings.json` (especially committed), connection-string patterns in code literals, hardcoded keys. Flag hardcoded secrets as *immediate* legacy debt — not scope-dependent.
6. **Observability** — grep for `AddApplicationInsightsTelemetryWorkerService`, `AddOpenTelemetry`, `UseAzureMonitorExporter` / Azure Monitor exporter package references, `ILogger` scopes, `traceparent` / `Activity.Current` propagation on outbound `HttpClient`.
7. **Manifest signals only** — `.csproj` / `package.json` to identify framework, SDK, versions. Extension handles deep stack-specific config.

### Stack-specific discovery

Delegated to the matching extension(s). Each loaded extension covers its own stack's configuration surface:

- `azure-functions-dotnet.md` — isolated vs in-process model, ASP.NET Core integration opt-in, DI in `Program.cs`, singleton clients, OpenTelemetry setup, `local.settings.json` vs real settings vs Key Vault refs, IaC presence (Bicep/Terraform for Flex Consumption plan and managed-identity assignments), `host.json` retry and `functionTimeout` values.
- `azure-cosmosdb.md` — account capacity mode (serverless / provisioned / autoscale), partition-key strategy, consistency level, indexing policy, RBAC data-plane role assignments vs account-key-based legacy, `disableLocalAuth`, `AllowBulkExecution`, `EnableContentResponseOnWrite`, change-feed lease containers, preferred-regions list.
- `azure-blob-storage.md` — account-level `allowSharedKeyAccess`, RBAC role assignments (Storage Blob Data Contributor / Reader / Delegator), presence of account keys / service SAS in code, versioning / soft-delete / immutability, Event Grid subscriptions, Blob Trigger source mode (Event Grid vs legacy polling), CORS rules, public-container access levels, CMK vs Microsoft-managed keys.

See the loaded extension's **Project assimilation** section for the full mapping table.

### Mapping existing infrastructure to reference rules

Reuse is conditional on **substantive compliance**, not presence. For each discovered asset, judge it against the reference before deciding whether to reuse or replace:

| Discovered in project | Reuse when | Replace / migrate when |
|---|---|---|
| Auth module (§3.3) | Entra ID + managed identity; Key Vault refs for any secret | Function-keys-only on public endpoints; secrets in literals or committed `local.settings.json` |
| Error middleware (§3.5) | Emits `application/problem+json` with stable `type` URIs | Custom error shape, English-string messages, leaks stack traces |
| Versioning strategy (§3.2) | One strategy applied uniformly (URI path preferred) | Mixed strategies; "implicit v1"; version in domain name without path prefix |
| Pagination primitive (§3.7) | Cursor-based, opaque token, capped `limit` | Offset / `skip` on unbounded collections; no `limit` cap |
| Data client lifetime (§3.16) | Singleton via DI; managed-identity auth | Per-invocation construction; account keys; multiple client instances |
| Observability pipeline (§3.14) | OpenTelemetry / Application Insights registered in `Program.cs`; structured logs; `traceparent` end-to-end | Console logging; per-handler ad-hoc telemetry; missing outbound propagation |
| Rate-limiting / throttling (§3.10) | Edge-level (API Management / Front Door) with per-consumer quotas; 429 + `Retry-After` | Origin-only, no `Retry-After`, wildcard throttling |
| Hosting plan (§3.15) | Fits cold-start tolerance; documented | Consumption plan on p95-sensitive public API; Dedicated on genuinely sparse workload |

**Name adoption is always fine.** If the project calls its problem+json `type` URIs `https://api.example.com/errors/...` and the reference examples use `https://api.example.com/errors/...`, adopt the project's base URL — the rule is shape and stability, not spelling.

**Substantive non-compliance is never fine.** If auth is shared-key on a public endpoint, or errors are plain-text, or a `CosmosClient` is constructed per invocation, reuse is not an option: the rule is broken, and reuse propagates the break.

### Conflict handling

When the project's existing approach violates a reference rule:

1. **Flag it** — cite the reference rule (§n.m and RFC / MSFT Learn URL), the file / line evidence, and classify it as *legacy debt* (pre-existing) or *would-be-added-code* (about to be added or reviewed).
2. **Pick a path** based on task scope and which class the conflict is in:
   - **Added code must comply.** Emit reference-compliant output for anything the current task is adding. There is no "match the broken pattern" option for added code.
   - **Legacy debt: scope-dependent.**
     - If the task explicitly includes migration, fix in place and show the diff.
     - If the task does not include migration, leave the legacy untouched and add a `Legacy debt` entry to the footer naming file / line + the violated rule. Do not extend the legacy pattern into added files.
     - If the legacy is load-bearing for the task (e.g., added endpoint sits inside a shared-key-auth Function app), halt and ask the user which scope to take.
3. **Never silently propagate a violation.** If existing config uses `allowSharedKeyAccess=true`, generating an added Function that reads blobs quietly inherits the insecure posture; output a warning block naming the IaC file and `blob.HC-2`; let the user decide.

### Footer additions

Both build-mode and review-mode footers gain a `Project assimilation:` block listing: compliant infrastructure reused, non-compliant infrastructure flagged as legacy debt (with the violated rule cited), and any migration the task performed. Example:

```
Project assimilation:
  OpenAPI:       openapi.yaml present, OpenAPI 3.1 — compliant, reused
  Error shape:   ProblemDetailsService via ConfigureFunctionsWebApplication() — compliant, reused
  Auth:          Entra ID + managed identity (infra/auth.bicep) — compliant, reused
  Cosmos client: singleton via DI in Program.cs, DefaultAzureCredential — compliant, reused
  Legacy debt (not migrated in this task):
    - infra/storage.bicep:42 — allowSharedKeyAccess=true — violates §3.17 / blob.HC-2
    - Services/Legacy.cs:88 — HttpClient instantiated per invocation — violates §2.8 / SAD-G-httpclient-per-invocation
  Migrations performed:
    - Functions/OrderPost.cs: added Idempotency-Key support with Cosmos-backed replay cache — fixes §3.6 / §5.6 / SAD-G-post-no-idempotency
```

The legacy-debt list is the record of what the project violates; it is not a list of "matched conventions." Added code in the same task is always reference-compliant regardless of what the legacy looks like.

## Build mode workflow

0. **Dispatch.** Confirm build mode. Run the pre-flight above. Detect stack; announce which extensions load.

1. **Principles scan.** Read reference [§2 Principles](../../docs/api-reference/serverless-api-design.md#2-principles). The skill's output must not violate any principle silently — violations require an explicit, justified deviation in a comment or an OpenAPI extension.

2. **Decision defaults.** For each API choice the endpoint needs, pull the corresponding default from reference §3:
   - Resource model → §3.1.
   - Versioning → §3.2.
   - Auth model → §3.3 / §3.4.
   - Error contract → §3.5.
   - Idempotency → §3.6.
   - Pagination / filtering → §3.7 / §3.8.
   - Sync vs async → §3.9.
   - Throttling → §3.10.
   - Input / size / CORS → §3.11 / §3.12 / §3.13.
   - Observability → §3.14.
   - Hosting plan → §3.15.
   - Data access / secrets → §3.16 / §3.17.

3. **Start from the baseline contract.** If the output is a greenfield API or endpoint set, open with §4.5 (OpenAPI 3.1 fragment + problem+json shape + `traceparent` propagation sketch). If it's a single endpoint added to an existing service, skip the full baseline but assume its behaviour.

4. **Compose with primitives (§4) and patterns (§5).** Pick the closest §5 pattern as the structural template — §5.1 CRUD, §5.2 search/list, §5.3 long-running 202+poll, §5.4 Durable orchestration, §5.5 webhook delivery, §5.6 idempotent POST, §5.7 bulk / partial-success, §5.8 fan-out, §5.9 BFF, §5.10 versioned rollout, §5.11 event-driven ingress, §5.12 OAuth-protected endpoint. Cite and adapt; do not reinvent.

5. **Apply extensions.** Each loaded extension's stack-specific primitives, patterns, and carve-outs layer on top of the core. For an Azure-Functions-.NET + Cosmos + Blob target:
   - `afdotnet.*` contributes `[Function]` attribute shape, isolated-worker HTTP response style ([BuiltIn] vs [AspNetCore]), DI in `Program.cs`, `TypedResults.Problem()` for RFC 9457 under `[AspNetCore]`, Durable trigger attributes, managed-identity via `DefaultAzureCredential`, Key Vault references, Flex Consumption always-ready instances, `IHttpClientFactory` + Polly / standard resilience handler.
   - `cosmos.*` contributes point-read vs query shape, `IfMatchEtag` → 412, `Idempotency-Key` container with TTL + unique-key, `ContinuationToken` for cursor pagination, change-feed processor, data-plane RBAC, `disableLocalAuth=true`, `x-ms-retry-after-ms` passthrough to HTTP `Retry-After`.
   - `blob.*` contributes direct-to-blob upload via user-delegation SAS, `BlobSasBuilder` with `SasProtocol.Https`, Event-Grid-sourced blob trigger, RBAC (Storage Blob Data Contributor / Delegator), `allowSharedKeyAccess=false`, range requests, ETag-based optimistic concurrency, archive rehydration as async 202.

6. **Self-check against §7 before declaring done.** Each checklist item carries a verification-layer tag (`[static]`, `[iac]`, `[contract]`, `[runtime]`, `[security-tool]`, `[load]`). Walk the five buckets — Contract discipline, Security, Reliability, Observability, Performance — and:
   - `[static]` items: verify against the code you wrote; pass / fail with confidence.
   - `[iac]` items: verify against IaC in the project; if IaC is out of scope, mark as "source-aligned; IaC verification required."
   - `[contract]` items: verify against the OpenAPI document you emitted.
   - `[runtime]` / `[load]` / `[security-tool]` items: **never** claim a pass from static analysis; report as "not statically verifiable — run load test / RUM / API scanner for ground truth."
   If any `[static]` / `[iac]` / `[contract]` item fails, fix it and re-check.

7. **Architecture diagram refresh (optional).** If the architect opted in during pre-flight (step 7), dispatch to `architecture-design` Extract targeting the feature just built. The canonical path `docs/architecture/<feature>.oef.xml` is updated with any new or changed Application Layer elements — added Azure Functions projects become Application Components, `[HttpTrigger]` routes become Application Interfaces, and `CosmosClient` / `BlobServiceClient` usage becomes Used-by relationships to Technology Nodes lifted from Bicep. If not opted in, skip silently.

8. **Emit footer disclosure.**

## Review mode workflow

0. **Dispatch.** Confirm review mode. Run pre-flight. Detect stack; announce extensions.

1. **Structural scan.** Read the target file(s). Identify whether the scope is a single endpoint, a controller / function class, a full API, or an entire service. Record the trigger types and binding sets present.

2. **Walk §7 checklist bucket by bucket.** For each item, inspect the code and record: pass / fail / not-applicable / not-statically-verifiable. Failures become findings.

3. **Per-finding format.** Match the devsecops-audit style:

   ```
   [<code>] <file>:<line>
     bucket:   contract | security | reliability | observability | performance
     layer:    static | iac | contract | runtime | security-tool | load
     severity: block | warn | info
     evidence: <quoted snippet or grep match>
     action:   <suggested fix template>
     ref:      serverless-api-design.md §<n.m> + (RFC <n> | MSFT Learn: <slug> | extension code)
   ```

   Codes are drawn from the extensions (`afdotnet.HC-1`, `cosmos.HC-4`, `blob.HC-2`, etc.), from the core `SAD-G-*` labels in reference §6 when a finding matches a named gotcha, and by reference section + RFC / MSFT Learn when there's no narrower code.

4. **Runtime is layer-capped.** Static signals only — singleton-client wiring, attribute presence, problem+json shape, ETag handling, OpenAPI completeness. **Never assert p95 / cold-start / error-rate / RU-charge from static review.** Flag this in the footer.

5. **Rollup.** After per-finding output, one paragraph per bucket summarising severity counts and the top fix.

6. **Architecture drift check (conditional).** If a paired diagram exists at `docs/architecture/<feature>.oef.xml` (discovered in pre-flight step 7), dispatch to `architecture-design` Review with the drift-detection sub-behaviour. Include any `AD-DR-*` findings in a dedicated "Architecture drift" section of the output, after the serverless-api-design rollup. If no matching diagram exists, skip silently.

7. **Emit footer disclosure.**

## Lookup mode workflow

0. **Dispatch.** Confirm lookup.

1. **Locate.** Grep reference for the concept (status code, header, pattern, RFC, MSFT Learn slug, extension primitive). Load only the matched section plus its immediate context.

2. **Answer concisely.** One or two sentences, citing the reference section and (if applicable) RFC / MSFT Learn source. Include the default rule if it's a §3 decision.

3. **Footer disclosure** (single line in lookup mode).

## Output format

### Build mode

```
<code blocks — OpenAPI fragments / C# handlers / Program.cs / Bicep / host.json as applicable>

Self-check:
  Contract discipline:   <n>/<n>  [static / contract verified]
                         <n> item(s) need the full OpenAPI validated by a linter
  Security:              <n>/<n>  [static / iac verified]
                         <n> item(s) need IaC review / security scanner
  Reliability:           <n>/<n>  [static / contract verified]
                         <n> item(s) need load test / chaos drill
  Observability:         <n>/<n>  [static verified]
                         <n> item(s) need runtime trace verification (Application Insights)
  Performance:           <n>/<n>  [static / iac verified]
                         <n> item(s) require Azure Load Testing / App Insights p95 metrics

Deviations from defaults (if any): <list with reason>
```

### Review mode

Per-finding block for each failure, then rollup. All findings cite reference section + RFC / MSFT Learn source / extension code where applicable. Each finding includes a `layer:` field so the reader knows how to confirm: `static` (grep / lint / source inspection), `iac` (Bicep / Terraform / ARM review), `contract` (OpenAPI document review), `runtime` (RUM / Azure Monitor / Application Insights), `security-tool` (OWASP ZAP / Burp / API Management policies), `load` (Azure Load Testing / k6 / JMeter). Only `static` / `iac` / `contract` findings are definitively pass / fail from the review alone; the rest are "source-aligned, verification deferred to <layer>".

### Lookup mode

Two to four lines of prose + one footer line.

### Footer (all modes)

```
Mode: build | review | lookup
Extensions loaded: <space-separated subset of {azure-functions-dotnet, azure-cosmosdb, azure-blob-storage} or "(none)">
Reference: souroldgeezer-design/docs/api-reference/serverless-api-design.md
Self-check: pass | <n failures> | n/a
Runtime-verified metrics: none — use Azure Load Testing / App Insights / Azure Monitor for p95, error rate, cold-start, RU charge, storage latency
Architecture pairing: drift-check clean | <n> drift findings | extract refreshed | none (no paired diagram)
```

## Red flags — stop and re-run

Output contains any of the following? Stop; fix before delivering:

- In-process .NET Functions model in added or modified code. Fix: isolated worker per `afdotnet.HC-1`; cite 2026-11-10 retirement.
- `[FunctionName(...)]` attribute in isolated-worker code. Fix: `[Function(...)]` per `afdotnet.HC-11`.
- Secrets in app-settings literals, `local.settings.json` committed to git, or code literals. Fix per §3.17 — Key Vault references + managed identity.
- Per-invocation `HttpClient` construction inside a handler body. Fix per §3.16 — `IHttpClientFactory` + singleton typed client.
- `AuthorizationLevel.Anonymous` on a non-public endpoint. Fix per §3.3 / §3.4.
- Error path returns plain JSON / string rather than `application/problem+json`. Fix per §3.5.
- POST mutation without `Idempotency-Key` support where retries matter. Fix per §3.6 / §5.6.
- 429 response without `Retry-After`. Fix per §3.10.
- Outbound `HttpClient` call without `traceparent` propagation (non-`IHttpClientFactory`-backed client). Fix per §3.14.
- Durable orchestration used where a queue + HTTP 202 would suffice. Fix per §5.4 / §5.8.
- Long-running work on an HTTP trigger past the plan timeout. Fix per §3.9.
- Missing OpenAPI for an added endpoint. Fix per §2.1 / §3.2.
- CORS wildcard on an authenticated endpoint. Fix per §3.13.
- Cosmos `CosmosClient` constructed per invocation, or account key in code. Fix per §3.16 / `cosmos.HC-1` / `cosmos.HC-2`.
- Cosmos GET-by-id performed as a cross-partition query. Fix per `cosmos.HC-4` — `ReadItemAsync(id, partitionKey)`.
- Storage `allowSharedKeyAccess=true` on a newly-deployed account, or service-SAS signed with an account key. Fix per §3.17 / `blob.HC-2` / `blob.HC-3`.
- API streams a large upload through the Function (re-uploading to blob). Fix per §3.12 — direct-to-blob user-delegation SAS per `blob.PAT-direct-upload-sas`.
- Claiming p95 / cold-start / error-rate / RU-charge pass from static review. Fix: restate as "static signals aligned; runtime metrics require load test / RUM."
- Non-Baseline / preview-only feature used without fallback (e.g., Cosmos hybrid-search RRF when GA status is uncertain). Fix: feature-detect and fall back, or document the preview dependency.

## Complementary skills

- `responsive-design` (same plugin `souroldgeezer-design`) — if the API is paired with a web UI, that skill covers the UI contract (WCAG 2.2 AA, i18n, CWV). The two skills compose; neither duplicates the other.
- `architecture-design` (same plugin) — paired ArchiMate model at `docs/architecture/<feature>.oef.xml`. Review mode auto-dispatches to `architecture-design` for drift detection when a paired diagram exists (see Review mode step 6); Build mode optionally dispatches to `architecture-design` Extract to keep the Application and Technology Layers of the diagram current (see Build mode step 7). The canonical path is the coupling mechanism; neither skill reaches into the other's surface.
- `devsecops-audit` (plugin `souroldgeezer-audit`) — pipeline, release, secrets scanning, IaC posture, CSP / CORS / cookie attributes on the hosting tier. This skill proves the *code and contract* are compliant; the audit skill proves the *pipeline* is compliant.
- `test-quality-audit` (plugin `souroldgeezer-audit`) — integration / E2E test quality for the endpoints this skill produces (Node.js + .NET + Next.js extensions available).

## Honest limits

- **Runtime SLIs (p95 latency, cold-start, error rate, RU charge, storage latency) cannot be asserted from static analysis.** Static signals (singleton-client wiring, retry configuration, plan selection, ReadyToRun / Placeholder opt-ins, binding retry attributes) are necessary but not sufficient. Point at Azure Load Testing, Application Insights / Azure Monitor, and CrUX / RUM for the client side.
- **Verification layers `[runtime]` / `[load]` / `[security-tool]` are deferred from the skill itself** to a load test, observability pipeline, or API security scanner. The skill reports "source-aligned; final verification requires <layer>" rather than claiming unverified passes.
- **Preview-status features** (Cosmos full-text search / hybrid search, some OpenTelemetry extension surface) — the skill cites the MSFT Learn page for the feature; if the page still marks the feature preview on 2026-04-23, the skill flags that and requires a feature-detection fallback or a documented preview dependency.
