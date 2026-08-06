# Extension: Azure Functions (.NET, isolated worker)

Stack-specific additions to the `api-design` skill for Azure Functions .NET. The core reference [`../../../docs/api-reference/api-design.md`](../../../docs/api-reference/api-design.md) stays framework-neutral; this extension layers Functions-specific detection, hosting, assimilation, and shared safety rules on top without overriding core rules.

> **Isolated worker only.** The in-process .NET Functions model reaches end of support on **2026-11-10** (MSFT Learn: `azure/azure-functions/migrate-dotnet-to-isolated-model`; `azure/azure-functions/functions-dotnet-class-library`). This extension refuses to author in-process code and routes existing in-process code to the review lane.

## Name and detection signals

The skill loads this extension when any of the following match:

- `.csproj` with `<PackageReference Include="Microsoft.Azure.Functions.Worker" ... />` OR `Microsoft.Azure.Functions.Worker.Sdk`.
- `host.json` at repo root.
- `[Function("...")]` attribute on a method in `.cs`.
- `FunctionsApplication.CreateBuilder(args)` OR `ConfigureFunctionsWebApplication()` OR `ConfigureFunctionsWorkerDefaults()` in `Program.cs`.
- `HttpRequestData` / `HttpResponseData` (built-in model) OR `HttpRequest` / `IActionResult` (ASP.NET Core integration) usage inside a function class.
- `<PackageReference Include="Microsoft.NET.Sdk.Functions" ... />` — legacy **in-process** model; the extension loads the review lane and blocks added in-process code.

## Hosting-model surface

Rules tagged `[Isolated]`, `[BuiltIn]`, `[AspNetCore]`, or `[Both]` depending on which shape applies.

- **`[Isolated]`** (only supported shape for added code) — separate worker process; full control over `Program.cs`; DI registered directly; .NET version independent of the Functions host runtime.
- **`[BuiltIn]`** — HTTP triggers use `HttpRequestData` / `HttpResponseData`; lightweight; no middleware pipeline; write JSON via `WriteAsJsonAsync`. Cannot stream request bodies.
- **`[AspNetCore]`** — HTTP triggers use `HttpRequest` / `IActionResult` via `ConfigureFunctionsWebApplication()` + `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore`. Supports middleware, `IProblemDetailsService`, streaming, `TypedResults.Problem(...)` (RFC 9457 out-of-box), `Results.Problem(...)`, `IActionResult` return types.
- Rules that apply in both shapes are tagged `[Both]`.

**Carve-out clarity.** `[BuiltIn]` idioms (`HttpResponseData` + `WriteAsJsonAsync` + hand-built problem+json) are not flagged against `[AspNetCore]` expectations, and vice versa. Load the review lane for the exact carve-outs.

## Mode lanes

This core file is the always-loaded azure-functions-dotnet stack surface. Load exactly one
mode lane when the task requires it:

- **Build:** read [`azure-functions-dotnet/build.md`](azure-functions-dotnet/build.md) for detailed primitives and `*.PAT-*` implementation patterns.
- **Review:** read [`azure-functions-dotnet/review.md`](azure-functions-dotnet/review.md) for `*.HC-*`, `*.LC-*`, and `*.POS-*` classifications plus exact carve-outs.
- **Extract:** keep this core only for a factual baseline. Load the review lane only when the user explicitly requests a debt or compliance verdict.
- **Lookup:** keep this core for detection and factual mechanics; load at most the one lane needed by the narrow question.

The core and one selected lane form the extension contract. Build and Review
lanes are mutually exclusive unless the user explicitly changes mode.

## Stack-specific primitives

For factual Extract and core-only Lookup, recognize these stack surfaces:

- Program.cs and DI
- Function shape
- Bindings
- Durable Functions
- Observability
- Managed identity and secrets
- Performance
- Retry

Detailed signatures and implementation guidance live in [`azure-functions-dotnet/build.md`](azure-functions-dotnet/build.md).

## Shared safety invariants

- Author only the isolated-worker model; treat legacy in-process projects as migration debt.
- Use managed identity or workload identity for platform services and keep secrets out of source and committed settings.
- Reuse singleton SDK clients and bound every public HTTP body, timeout, retry, and long-running operation.
- Emit RFC 9457 problem details on error paths and keep required work durable before returning a response.

## Project assimilation (Azure Functions .NET-specific)

Run this after the core framework-agnostic discovery pass; results feed into the assimilation footer.

1. **Isolated vs in-process** — grep `.csproj` for `Microsoft.Azure.Functions.Worker` (isolated) vs `Microsoft.NET.Sdk.Functions` (in-process). In-process → legacy debt on any added code.
2. **ASP.NET Core integration** — grep `Program.cs` for `ConfigureFunctionsWebApplication()`. Present → use `[AspNetCore]` patterns; absent → use `[BuiltIn]` patterns or propose migration if the task adds streaming / middleware / problem-details needs.
3. **DI in `Program.cs`** — grep for `builder.Services.AddSingleton<`, `AddHttpClient<`, `AddOptions<`. Record the registered services; singleton data clients are compliant infrastructure to reuse.
4. **OpenTelemetry / App Insights** — grep for `AddApplicationInsightsTelemetryWorkerService`, `AddOpenTelemetry`, `UseAzureMonitorExporter`. Compliant → reuse; absent → registration is added in Build mode.
5. **`local.settings.json`** — must be `.gitignore`d or contain only non-secret scaffolding. Any committed secret is immediate legacy debt.
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
| §3.9 async 202 | `Results.Accepted(locationUri, body)` | `response.StatusCode = HttpStatusCode.Accepted; response.Headers.Add("Location",...)` |
| §3.14 observability | `ILogger<T>.BeginScope` + OpenTelemetry | Same |
| §3.16 data access | Singleton clients via DI in `Program.cs` | Same |
| §3.17 secrets | `@Microsoft.KeyVault(...)` + managed identity | Same |

## Applies to reference sections

§2.1, §2.3, §2.5, §2.6, §2.7, §2.8, §3.2, §3.3, §3.4, §3.5, §3.6, §3.9, §3.10, §3.11, §3.13, §3.14, §3.15, §3.16, §3.17, §4.5, §5.3, §5.4, §5.6, §5.8, §5.10, §5.11, §5.12, §6, §7.
