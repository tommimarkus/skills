# Extension: azure-functions-dotnet build lane

Implementation detail for [the azure-functions-dotnet core](../azure-functions-dotnet.md).

## Load condition

Load this file only in Build mode, or for a narrow Lookup that explicitly asks
for an implementation primitive or pattern from this stack. Do not load it in
Review or factual Extract.

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

- **`DefaultAzureCredential`** — the primary credential type. Tries a fixed chain in order — environment → workload identity → managed identity (in Azure) → Visual Studio / VS Code / Azure CLI / Azure PowerShell / Azure Developer CLI (local dev) — stopping at the first that yields a token; tokens cached by the SDK. `InteractiveBrowserCredential` is **excluded by default** (`ExcludeInteractiveBrowserCredential` defaults to `true`); enable it explicitly only for a deliberate interactive dev fallback.
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
Fan out N activities and wait for all. Cap width (`items.Chunk(50)`) to avoid saturating downstream. Maps §5.4.
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

### `afdotnet.PAT-durable-monitor` `[Both]`
Poll an external condition via activity + timer loop; call `ctx.ContinueAsNew(newState)` after a threshold (e.g., 60 iterations) to reset history (eternal-orchestration shape). Maps §5.4.
```csharp
// in loop body:
await ctx.CreateTimer(ctx.CurrentUtcDateTime.AddMinutes(1), CancellationToken.None);
```

### `afdotnet.PAT-durable-approval` `[Both]`
Await human decision with timeout; cancel the losing task's CTS to release resources. External systems POST via `sendEventPostUri`. Maps §5.4.
```csharp
using var cts = new CancellationTokenSource();
var approval = ctx.WaitForExternalEvent<Decision>("Approval");
var timeout  = ctx.CreateTimer(ctx.CurrentUtcDateTime.AddHours(24), cts.Token);
var winner   = await Task.WhenAny(approval, timeout);
if (winner == approval) { cts.Cancel(); /* proceed */ }
else                    { /* handle expiry */ }
```

### `afdotnet.PAT-durable-saga` `[Both]`
Sequential steps with per-step compensation; compensating activities must be idempotent (orchestrator may replay). Maps §5.4.
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
