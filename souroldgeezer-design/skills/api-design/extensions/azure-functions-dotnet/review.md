# Extension: azure-functions-dotnet review lane

Review classifications and carve-outs for [the azure-functions-dotnet core](../azure-functions-dotnet.md).

## Load condition

Load this file in Review mode. In Extract, load it only when the user explicitly
requests a debt or compliance verdict. For a narrow Lookup, load it only when
the question asks for a finding code or carve-out. Do not load it in Build.

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
