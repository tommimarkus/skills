# Extension: Azure Functions (.NET, isolated worker)

Stack-specific additions to the `api-design` skill for Azure Functions .NET. The core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md) stays framework-neutral; this extension layers Functions-specific primitives, patterns, and smells on top without overriding core rules.

> **Isolated worker only.** The in-process .NET Functions model reaches end of support on **2026-11-10** (MSFT Learn: `azure/azure-functions/migrate-dotnet-to-isolated-model`; `azure/azure-functions/functions-dotnet-class-library`). This extension refuses to author in-process code and flags existing in-process code as `afdotnet.HC-1`.

## Name and detection signals

The skill loads this extension when any of the following match:

- `.csproj` with `<PackageReference Include="Microsoft.Azure.Functions.Worker" ... />` OR `Microsoft.Azure.Functions.Worker.Sdk`.
- `host.json` at repo root.
- `[Function("...")]` attribute on a method in `.cs`.
- `FunctionsApplication.CreateBuilder(args)` OR `ConfigureFunctionsWebApplication()` OR `ConfigureFunctionsWorkerDefaults()` in `Program.cs`.
- `HttpRequestData` / `HttpResponseData` (built-in model) OR `HttpRequest` / `IActionResult` (ASP.NET Core integration) usage inside a function class.
- `<PackageReference Include="Microsoft.NET.Sdk.Functions" ... />` — legacy **in-process** model; the extension loads but immediately flags `afdotnet.HC-1` and blocks authoring.

## Hosting-model surface

Rules tagged `[Isolated]`, `[BuiltIn]`, `[AspNetCore]`, or `[Both]` depending on which shape applies.

- **`[Isolated]`** (only supported shape for added code) — separate worker process; full control over `Program.cs`; DI registered directly; .NET version independent of the Functions host runtime.
- **`[BuiltIn]`** — HTTP triggers use `HttpRequestData` / `HttpResponseData`; lightweight; no middleware pipeline; write JSON via `WriteAsJsonAsync`. Cannot stream request bodies.
- **`[AspNetCore]`** — HTTP triggers use `HttpRequest` / `IActionResult` via `ConfigureFunctionsWebApplication()` + `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore`. Supports middleware, `IProblemDetailsService`, streaming, `TypedResults.Problem(...)` (RFC 9457 out-of-box), `Results.Problem(...)`, `IActionResult` return types.
- Rules that apply in both shapes are tagged `[Both]`.

**Carve-out clarity.** `[BuiltIn]` idioms (`HttpResponseData` + `WriteAsJsonAsync` + hand-built problem+json) are not flagged against `[AspNetCore]` expectations, and vice versa. See *Carve-outs* below.

## Stack-specific primitives

Verify the exact current signatures against the cited MSFT Learn page at authoring time — some APIs have evolved between SDK releases.

### Program.cs and DI

- **`FunctionsApplication.CreateBuilder(args)`** — the preferred `IHostApplicationBuilder`-style entry (MSFT Learn: `dotnet-isolated-process-guide`). The legacy `Host.CreateDefaultBuilder(args).ConfigureFunctionsWorkerDefaults()` shape still works but the builder form is current.
- **`builder.ConfigureFunctionsWebApplication()`** — opts into ASP.NET Core integration. Required for `HttpRequest` / `IActionResult` and for middleware / `IProblemDetailsService` / `TypedResults.Problem(...)`. Also required for streaming request bodies. Requires package `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore`.
- **DI registrations in `Program.cs`** — `builder.Services.AddSingleton<T>`, `AddHttpClient<TClient, TImpl>(...)`, `AddOptions<T>().BindConfiguration("...")`, `AddApplicationInsightsTelemetryWorkerService()` + `ConfigureFunctionsApplicationInsights()` (the two Application Insights extension methods go together; the second wires the Functions worker into the Application Insights pipeline).
- **`<FrameworkReference Include="Microsoft.AspNetCore.App" />`** in `.csproj` — required for ASP.NET Core integration; also improves non-HTTP performance (MSFT Learn: `dotnet-isolated-process-guide` performance section).

### Function shape

- **`[Function("OperationName")]`** — replaces the legacy `[FunctionName(...)]`. The operation name is the `Function` attribute argument and maps to observability (run logs, Application Insights), not the C# method name.
- **`[HttpTrigger(AuthorizationLevel.*, "get", "post", Route = "...")]`** — HTTP trigger. Authorization levels: `Anonymous`, `Function`, `Admin`. Route template supports ASP.NET Core route constraints (`{id:int}`, `{slug:regex(...)}`, `{year:min(2020)}`).
- **`HttpRequestData` / `HttpResponseData`** — `[BuiltIn]` shape. `await response.WriteAsJsonAsync(obj, HttpStatusCode.OK)`; set headers via `response.Headers.Add(...)`. No middleware, no streaming-in.
- **`HttpRequest` / `IActionResult`** — `[AspNetCore]` shape. Returns `Results.Ok(...)`, `Results.NotFound()`, `TypedResults.Problem(...)` (RFC 9457), `Results.Created(location, body)`, `Results.Accepted(location, body)`.
- **Multi-output** — custom return type with output-binding attributes on properties. Idiomatic and not flagged as "multi-return side-effect." Isolated worker does **not** use `IAsyncCollector<T>` (that is the in-process shape).

### Bindings

Input / output / trigger bindings for Cosmos, Service Bus, Blob, Queue, Table, SignalR, Event Hubs, Event Grid, Timer, Durable. Binding expressions (`{id}`, `{query.partitionKey}`, `{sys.UtcNow}`) resolve at invocation time and enable zero-boilerplate point reads (e.g., `[CosmosDBInput("db", "items", Id = "{id}", PartitionKey = "{partitionKey}")]`).

### Durable Functions

- **`[OrchestrationTrigger]`** — orchestrator function; MUST be deterministic. Use `context.CurrentUtcDateTime`, `context.NewGuid()`, `context.CallActivityAsync<T>(...)` instead of `DateTime.UtcNow`, `Guid.NewGuid()`, or direct I/O.
- **`[ActivityTrigger]`** — activity function; the place for non-deterministic work.
- **`[EntityTrigger]`** — stateful entities.
- **`[DurableClient]`** — the orchestration client; used in an HTTP starter to schedule orchestrations.
- **HTTP API response fields** — `id`, `statusQueryGetUri`, `sendEventPostUri`, `terminatePostUri`, `rewindPostUri`, `purgeHistoryDeleteUri` (MSFT Learn: `durable/durable-functions-http-api`). `statusQueryGetUri` is the polling endpoint for §5.3 / §5.4 patterns; `sendEventPostUri` is how external systems raise events to a waiting orchestrator (e.g., human approval).

### Observability

- **Application Insights** — `AddApplicationInsightsTelemetryWorkerService()` + `ConfigureFunctionsApplicationInsights()` in `Program.cs`.
- **OpenTelemetry** — `builder.Services.AddOpenTelemetry()` then tracing / logging / metrics per the current MSFT Learn `azure/azure-functions/functions-opentelemetry` page. The exact extension-method chain (`UseFunctionsWorkerDefaults` / `WithTracing` / `AddSource` / Azure Monitor exporter package name) has evolved between releases — cite the live page at authoring time.
- **`ILogger<T>` scopes** — `using var scope = logger.BeginScope(new Dictionary<string, object> { ... })`. Named fields, structured logging.
- **`traceparent`** — propagated automatically end-to-end when outbound HTTP uses `IHttpClientFactory`. Avoid handcrafted `HttpClient` instances.

### Managed identity and secrets

- **`DefaultAzureCredential`** — the primary credential type. Chains managed identity (in Azure) → Azure CLI / VS / environment (locally) → interactive (dev fallback). Tokens cached by the SDK.
- **Cosmos auth** — `new CosmosClient(accountEndpoint, new DefaultAzureCredential())`. No account keys.
- **SQL auth** — connection string `Server=...;Database=...;Authentication=Active Directory Default;`.
- **Service Bus auth** — `new ServiceBusClient(fqdn, new DefaultAzureCredential())`.
- **Key Vault references** — app setting value `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/<version>)`. The Function app's managed identity must have the **Key Vault Secrets User** role.

### Performance

- **`<PublishReadyToRun>true</PublishReadyToRun>`** — cold-start mitigation; produces pre-JIT'd binaries.
- **`WEBSITE_RUN_FROM_PACKAGE=1`** — read-only deployment from zip; improves cold start and removes a class of tampering.
- **`WEBSITE_USE_PLACEHOLDER_DOTNETISOLATED=1`** — placeholder warming; documented under Flex Consumption per `azure/azure-functions/flex-consumption-plan`. Older tutorials reference this setting under Consumption; the current canonical placement is Flex Consumption.
- **Flex Consumption always-ready instances** — per-trigger-type warm pool; the production default for public APIs. Configured in IaC.

### Retry

Binding-level retry attributes on triggers — **`[FixedDelayRetry(maxRetryCount, delayInterval)]`** and **`[ExponentialBackoffRetry(maxRetryCount, minimumInterval, maximumInterval)]`** (MSFT Learn: `azure/azure-functions/functions-bindings-error-pages`). Namespace: `Microsoft.Azure.Functions.Worker`. Supported triggers in isolated worker: **Timer, Event Hubs, Kafka, Azure Cosmos DB only** — HTTP, Queue, and Service Bus triggers do **not** support binding-level retry (Service Bus uses its own broker-side delivery-count + dead-letter; Queue triggers use `queuesOptions.maxDequeueCount`; HTTP triggers need client-side retry).

For outbound HTTP: typed `HttpClient` via `IHttpClientFactory` plus **`.AddStandardResilienceHandler()`** (from `Microsoft.Extensions.Http.Resilience`) for retry + circuit breaker + timeout + rate limiter. Requires .NET 8+; for .NET 6 / 7 projects, use Polly v7 via `.AddPolicyHandler(Policy.WrapAsync(retry, breaker, timeout))`.

## Stack-specific patterns

### `afdotnet.PAT-http-problem-details` `[AspNetCore]`
HTTP trigger with ASP.NET Core integration emitting RFC 9457 problem+json on error paths via `TypedResults.Problem(...)` / `Results.Problem(...)`. Map exception classes to stable `type` URIs in a single middleware / exception handler. Maps §3.5.

### `afdotnet.PAT-builtin-problem-details` `[BuiltIn]`
HTTP trigger using `HttpResponseData` hand-building problem+json: `response.Headers.Add("Content-Type", "application/problem+json")` then `await response.WriteAsJsonAsync(problem)`. Wrap in a helper so every error path is consistent. Maps §3.5.

### `afdotnet.PAT-idempotent-post` `[Both]`
HTTP POST trigger reads `Idempotency-Key` header, checks a replay cache, writes cached response or processes and stores. Pairs with `cosmos.PAT-idempotency-container` when the cache is Cosmos-backed. Maps §3.6 / §5.6.

### `afdotnet.PAT-durable-202` `[Both]`
HTTP starter with `[DurableClient]` schedules an orchestration via `ScheduleNewOrchestrationInstanceAsync(...)`; returns 202 + `Location: <statusQueryGetUri>` from `CreateCheckStatusResponse(...)`. The orchestrator coordinates activities; activities do the non-deterministic work. Maps §5.4.

### `afdotnet.PAT-durable-fanout` `[Both]`
Orchestrator fans out N activities and waits for all:
```csharp
[Function(nameof(ProcessBatch))]
public static async Task<Result> Run([OrchestrationTrigger] TaskOrchestrationContext ctx)
{
    var items = ctx.GetInput<List<Item>>()!;
    var tasks = items.Select(i => ctx.CallActivityAsync<ItemResult>(nameof(ProcessOne), i));
    var results = await Task.WhenAll(tasks);
    return new Result(results);
}
```
Cap fan-out width (`items.Chunk(50)`) to avoid saturating downstream. Maps §5.4.

### `afdotnet.PAT-durable-monitor` `[Both]`
Orchestrator polls an external condition via activity + timer loop, with an upper-bound iteration count. At each iteration, check the condition; if not met, `await ctx.CreateTimer(ctx.CurrentUtcDateTime.AddMinutes(1), CancellationToken.None);` and loop. Past a threshold (e.g., 60 iterations), the orchestrator calls `ctx.ContinueAsNew(newState)` to reset history — the eternal-orchestration shape. Maps §5.4.

### `afdotnet.PAT-durable-approval` `[Both]`
Orchestrator awaits a human decision with a timeout:
```csharp
using var cts = new CancellationTokenSource();
var approval = ctx.WaitForExternalEvent<Decision>("Approval");
var timeout  = ctx.CreateTimer(ctx.CurrentUtcDateTime.AddHours(24), cts.Token);
var winner   = await Task.WhenAny(approval, timeout);
if (winner == approval) { cts.Cancel(); /* proceed */ }
else                    { /* handle expiry */ }
```
External systems POST the decision via `sendEventPostUri`. The losing task's CTS is cancelled to release resources. Maps §5.4.

### `afdotnet.PAT-durable-saga` `[Both]`
Sequential steps with per-step compensation on failure:
```csharp
var completed = new Stack<Func<Task>>();
try
{
    await ctx.CallActivityAsync(nameof(ReserveInventory), order);
    completed.Push(() => ctx.CallActivityAsync(nameof(ReleaseInventory), order));
    await ctx.CallActivityAsync(nameof(ChargePayment), order);
    completed.Push(() => ctx.CallActivityAsync(nameof(RefundPayment), order));
    await ctx.CallActivityAsync(nameof(ShipOrder), order);
}
catch
{
    while (completed.TryPop(out var undo)) await undo();
    throw;
}
```
Compensating activities must themselves be idempotent — the orchestrator may replay during recovery. Maps §5.4.

### `afdotnet.PAT-webhook-receive` `[AspNetCore]`
Inbound webhook handler with raw-body signature verification, timestamp window, and dedup:

```csharp
[Function("ReceiveWebhook")]
public async Task<IResult> Run(
    [HttpTrigger(AuthorizationLevel.Function, "post", Route = "webhooks/{source}")] HttpRequest req,
    string source,
    [FromServices] IWebhookSecretCache secrets,
    [FromServices] Container idempotency)
{
    req.EnableBuffering();
    using var ms = new MemoryStream();
    await req.Body.CopyToAsync(ms);
    var body = ms.ToArray();
    req.Body.Position = 0;

    var sigHeader = req.Headers["X-Signature"].ToString();
    var eventId   = req.Headers["X-Event-Id"].ToString();
    if (!TryParseSignature(sigHeader, out var ts, out var sig)) return Results.Unauthorized();
    if (Math.Abs((DateTimeOffset.UtcNow - ts).TotalSeconds) > 300) return Results.Unauthorized();

    var secret   = await secrets.GetAsync(source);
    var expected = Hmac($"{ts.ToUnixTimeSeconds()}.{Encoding.UTF8.GetString(body)}", secret);
    if (!CryptographicOperations.FixedTimeEquals(sig, expected)) return Results.Unauthorized();

    try { await idempotency.CreateItemAsync(new { id = $"{source}:{eventId}", ttl = 86400 }); }
    catch (CosmosException e) when (e.StatusCode == HttpStatusCode.Conflict) { return Results.Accepted(); }

    await _queue.SendAsync(new WebhookJob(source, eventId, body));
    return Results.Accepted();
}
```

Key points:
- Buffer raw body *before* model binding (signature is over bytes).
- Constant-time compare via `CryptographicOperations.FixedTimeEquals`.
- Dedup via Cosmos unique-key + TTL; `409 Conflict` on the insert is the dedup hit → return the same 202.
- Cache the Key Vault secret with a short TTL; support previous-secret fallback during rotation.
- Acknowledge with 202 + enqueue; do not process synchronously. Maps §5.5b.

### `afdotnet.PAT-queue-async` `[Both]`
HTTP trigger writes to a Service Bus output binding and returns 202 + `Location: /jobs/{id}`. A Service Bus trigger processes; poison / dead-letter handled by the platform. Cheaper than Durable for single-step async. Maps §5.8 / §5.11.

### `afdotnet.PAT-otel-exporter` `[Both]`
`Program.cs` wires OpenTelemetry tracing + logging with Azure Monitor exporter (or OTLP); outbound HTTP uses `IHttpClientFactory` so `traceparent` is auto-propagated. Maps §3.14.

### `afdotnet.PAT-flex-always-ready` `[Both]`
Bicep or Terraform for Flex Consumption plan with per-trigger-type always-ready instances (e.g., `alwaysReady: [{ name: 'http', instanceCount: 1 }]`). The production default for public APIs. Maps §3.15.

### `afdotnet.PAT-keyvault-config` `[Both]`
App-setting value `@Microsoft.KeyVault(SecretUri=...)`; managed identity on the Function app; Key Vault Secrets User role assignment in IaC. No secrets in literals. Maps §3.17.

### `afdotnet.PAT-resilient-outbound` `[Both]`
`builder.Services.AddHttpClient<IMyClient, MyClient>(...).AddStandardResilienceHandler()` (or `.AddResilienceHandler("name", pipeline => ...)` with Polly v8). Retry + circuit breaker + timeout + rate limiter on every outbound call. Maps §2.6 / §3.14.

### `afdotnet.PAT-openapi` `[Both]`
OpenAPI 3.1 document is the contract. Three generator paths for isolated-worker Functions, roughly in order of preference:

1. **`Microsoft.Azure.Functions.Worker.Extensions.OpenApi` (attribute-driven)** — the canonical isolated-worker package. Decorate handlers with `[OpenApiOperation]`, `[OpenApiParameter]`, `[OpenApiRequestBody]`, `[OpenApiResponseWithBody]`; the package generates `/api/swagger.json` at runtime and can serve Swagger UI. Pros: one source of truth, generated at build. Cons: verbose on large surfaces; evolves with Microsoft's sample repo rather than a formal SLA.
2. **Hand-authored YAML** at `openapi.yaml` in the repo root, served via a static-file Function or fronted by API Management. Pros: full control; easy to lint (Spectral); easy to diff in code review. Cons: drift between code and spec unless CI enforces contract-tests against the spec.
3. **Swashbuckle** — **not natively supported in isolated-worker Functions** (it's ASP.NET Core host-bound). Can be made to work under `ConfigureFunctionsWebApplication()` with `.AddEndpointsApiExplorer()` + `.AddSwaggerGen()`, but it's an off-label configuration — prefer path 1 or 2.

**Recommendation:** path 1 for greenfield; path 2 when the API surface is stable and the team prefers spec-first review. Whichever path, add CI steps to (a) lint the spec (Spectral with the `spectral:oas` ruleset), (b) validate handlers against the spec (Schemathesis or Dredd), and (c) publish the spec as a build artefact. Maps §2.1 / §3.2.

### `afdotnet.PAT-ratelimit-edge` `[Both]`
Azure Front Door or API Management in front, with rate-limit policy per consumer + WAF rules. The Function app itself is a backend origin; rate-limiting lives at the edge. Maps §3.10 / §3.13.

## Project assimilation (Azure Functions .NET-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **Isolated vs in-process** — grep `.csproj` for `Microsoft.Azure.Functions.Worker` (isolated) vs `Microsoft.NET.Sdk.Functions` (in-process). In-process → legacy debt, `afdotnet.HC-1` on any added code.
2. **ASP.NET Core integration** — grep `Program.cs` for `ConfigureFunctionsWebApplication()`. Present → use `[AspNetCore]` patterns; absent → use `[BuiltIn]` patterns or propose migration if the task adds streaming / middleware / problem-details needs.
3. **DI in `Program.cs`** — grep for `builder.Services.AddSingleton<`, `AddHttpClient<`, `AddOptions<`. Record the registered services; singleton data clients are compliant infrastructure to reuse.
4. **OpenTelemetry / App Insights** — grep for `AddApplicationInsightsTelemetryWorkerService`, `AddOpenTelemetry`, `UseAzureMonitorExporter`. Compliant → reuse; absent → registration is added in Build mode.
5. **`local.settings.json`** — must be `.gitignore`d or contain only non-secret scaffolding. Any committed secret is immediate legacy debt (`afdotnet.HC-3`).
6. **App settings vs Key Vault** — IaC (`Microsoft.Web/sites` in Bicep / `azurerm_linux_function_app` in Terraform) shows app settings. Any literal secret is debt; `@Microsoft.KeyVault(...)` references are compliant.
7. **Hosting plan** — IaC shows the `serverfarms` / `Microsoft.Web/serverfarms` SKU. Consumption (`Y1`), Premium (`EP1`/`EP2`/`EP3`), Flex Consumption (`FC1`), Dedicated (`P1v3` etc.). Record; match against §3.15.
8. **`host.json`** — `functionTimeout`, `extensions.serviceBus.*`, `extensions.http.*`, per-extension retry. Record.
9. **Durable lease storage** — grep for `[DurableClient]` / `[OrchestrationTrigger]`. Present → Durable is in use; check lease storage posture.

### Mapping reference defaults to Azure Functions .NET idioms

| Reference default | `[AspNetCore]` | `[BuiltIn]` |
|---|---|---|
| §3.5 problem+json | `TypedResults.Problem(...)` | Hand-built via `HttpResponseData.WriteAsJsonAsync(problem, "application/problem+json")` |
| §3.6 idempotency | Middleware + Cosmos replay cache | Helper + Cosmos replay cache |
| §3.7 cursor pagination | `Results.Ok(new { items, nextCursor })` | `HttpResponseData` with same shape |
| §3.9 async 202 | `Results.Accepted(locationUri, body)` | `response.StatusCode = HttpStatusCode.Accepted; response.Headers.Add("Location", ...)` |
| §3.14 observability | `ILogger<T>.BeginScope` + OpenTelemetry | Same |
| §3.16 data access | Singleton clients via DI in `Program.cs` | Same |
| §3.17 secrets | `@Microsoft.KeyVault(...)` + managed identity | Same |

## Smell codes

### High-confidence

- **`afdotnet.HC-1`** — In-process .NET Functions model in added or modified code (MSFT Learn: `migrate-dotnet-to-isolated-model`; retired 2026-11-10). *Layer:* static.
- **`afdotnet.HC-2`** — Per-invocation `HttpClient` construction inside a function body (not via `IHttpClientFactory`). Connection-exhaustion under load. *Layer:* static.
- **`afdotnet.HC-3`** — Hardcoded connection string or access key in `local.settings.json` being committed, or in a `.cs` literal. *Layer:* static.
- **`afdotnet.HC-4`** — `AuthorizationLevel.Anonymous` on a trigger that handles non-public data (no Entra ID validator, no managed-identity-authenticated caller). *Layer:* static.
- **`afdotnet.HC-5`** — Error path returns bare JSON / plain string rather than `application/problem+json`. *Layer:* static.
- **`afdotnet.HC-6`** — POST mutation without `Idempotency-Key` support when retries are expected; or retries without dedup. *Layer:* static + contract.
- **`afdotnet.HC-7`** — 429 emitted without `Retry-After`. *Layer:* static.
- **`afdotnet.HC-8`** — Outbound `HttpClient` call without `traceparent` propagation (handcrafted client, not via `IHttpClientFactory`). *Layer:* static.
- **`afdotnet.HC-9`** — Long-running work on an HTTP trigger past the plan's function timeout or past the platform HTTP-trigger cap. Consumption plan: default 5 min, hard max 10 min. Premium / Flex Consumption / Dedicated: default 30 min, hard max unbounded — but HTTP triggers are capped at **230 seconds** across all plans by the Azure Load Balancer idle timeout (MSFT Learn: `functions-scale`). *Layer:* static + iac.
- **`afdotnet.HC-10`** — Secrets read via raw connection string where Key Vault reference + managed identity applies. *Layer:* static + iac.
- **`afdotnet.HC-11`** — `[FunctionName(...)]` attribute in isolated-worker code (should be `[Function(...)]`). *Layer:* static.
- **`afdotnet.HC-12`** — Missing Application Insights / OpenTelemetry registration in `Program.cs`. *Layer:* static.
- **`afdotnet.HC-13`** — Non-deterministic API inside an orchestrator function (`DateTime.UtcNow`, `Guid.NewGuid()`, direct I/O) — violates Durable determinism. *Layer:* static.
- **`afdotnet.HC-14`** — Missing OpenAPI annotations / document for an added endpoint. *Layer:* static + contract.
- **`afdotnet.HC-15`** — CORS wildcard (`allowedOrigins: ["*"]`) on an authenticated Function app. CORS on Azure Functions is configured at the **platform tier** — `Microsoft.Web/sites` `cors.allowedOrigins` in Bicep / Terraform, Azure portal, or `az functionapp cors` CLI — **not in code**. Source-only grep cannot find this; IaC review is required. *Layer:* iac.

### Low-confidence

- **`afdotnet.LC-1`** — Function-level keys on an endpoint where Entra ID + managed identity would be simpler. Context-dependent. *Layer:* static.
- **`afdotnet.LC-2`** — Durable orchestration used where a single queue trigger + HTTP 202 + `Location` would suffice. *Layer:* static.
- **`afdotnet.LC-3`** — `HttpRequestData` / `HttpResponseData` used in a function that needs streaming or middleware; `[AspNetCore]` integration would be clearer. *Layer:* static.
- **`afdotnet.LC-4`** — Missing ReadyToRun / Placeholder opt-ins on a latency-sensitive app. *Layer:* static + iac.
- **`afdotnet.LC-5`** — Non-`IHttpClientFactory` typed client (still singleton but not registered via the factory); works but misses the resilience pipeline. *Layer:* static.

### Positive signals

- **`afdotnet.POS-1`** — Isolated worker + `ConfigureFunctionsWebApplication()` with `TypedResults.Problem(...)` on error paths.
- **`afdotnet.POS-2`** — Singleton data client (Cosmos / SQL / Service Bus / Blob) registered in DI with `DefaultAzureCredential`.
- **`afdotnet.POS-3`** — Typed `HttpClient` via `IHttpClientFactory` with `.AddStandardResilienceHandler()` (or Polly v8 equivalent).
- **`afdotnet.POS-4`** — Key Vault references in app settings; no secrets in code or literals.
- **`afdotnet.POS-5`** — OpenTelemetry registered with Azure Monitor exporter and `traceparent` propagation.
- **`afdotnet.POS-6`** — Flex Consumption plan with always-ready instances configured for the HTTP trigger type.
- **`afdotnet.POS-7`** — OpenAPI document generated from annotations and published at a stable URL.
- **`afdotnet.POS-8`** — `Idempotency-Key` support on non-idempotent POST mutations with replay cache and TTL.
- **`afdotnet.POS-9`** — Binding-level retry (`[FixedDelayRetry]` / `[ExponentialBackoffRetry]`) configured on a supported trigger (Timer, Event Hubs, Kafka, Cosmos DB); plus broker-side delivery-count + dead-letter on Service Bus triggers, `queuesOptions.maxDequeueCount` + poison queue on Queue triggers.
- **`afdotnet.POS-10`** — ReadyToRun + Placeholder opt-ins on latency-sensitive app.

## Carve-outs

Do not flag the following:

- `HttpRequestData` / `HttpResponseData` / `WriteAsJsonAsync` usage under `[BuiltIn]` — idiomatic, not a smell (contrast `afdotnet.LC-3` which only applies when streaming or middleware is genuinely needed).
- Custom return type with output-binding attributes on properties — idiomatic multi-output, not a "multi-return side-effect."
- Direct SDK usage when the SDK capability exceeds the binding's (e.g., Cosmos change-feed processor with continuation tokens; Blob `OpenReadAsync` streaming). Require a code comment stating the reason.
- Function keys on a tightly-scoped internal service-to-service hop with a single trusted caller, where Entra ID setup overhead is not justified. Require a justifying comment and a documented rotation policy (`afdotnet.LC-1` is deliberate low-confidence to allow this with justification).
- `context.CurrentUtcDateTime` and `context.NewGuid()` inside an orchestrator — these are deterministic and allowed (contrast `afdotnet.HC-13` which targets `DateTime.UtcNow` / `Guid.NewGuid()` / direct I/O).
- `[Function]` attribute name that does not match the C# method name — the attribute argument is the operation identifier for observability; method name is for C# readability. Not a smell.

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.3, §3.4, §3.5, §3.6, §3.9, §3.10, §3.11, §3.13, §3.14, §3.15, §3.16, §3.17, §4.5, §5.3, §5.4, §5.6, §5.8, §5.10, §5.11, §5.12, §6, §7.
