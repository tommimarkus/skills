# Lifting rules — .NET to ArchiMate® Application Layer

Rules for lifting ArchiMate® **Application Layer** elements from a .NET solution (Azure Functions isolated-worker + Blazor WebAssembly — the stack the sibling design skills produce). Invoked by Extract mode.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). This procedure cites §4.2 (Application Layer elements) and §7.1 (extractability per layer).

## Sources read

In order of authority:

1. `*.sln` — discovers project set and grouping.
2. `*.csproj` — discovers project SDK / output type / framework references / NuGet references / `<ProjectReference>` graph.
3. `Program.cs` — discovers hosting model (isolated-worker, Blazor WASM, Blazor Web App).
4. `host.json` — discovers Azure Functions runtime version, extension set, binding defaults.
5. `*.razor`, `*.razor.cs`, `@rendermode` directives — discovers Blazor component surface.
6. `staticwebapp.config.json` — discovers Static Web Apps routing + auth (relevant for Application Interfaces).
7. Class library projects without `Program.cs` — discovered as Application Component with `type=library` semantics, or as a shared Artifact.

Out of scope: `local.settings.json`, user secrets, bin / obj output.

## Mapping rules

### Projects → Application Components

| Detection | Maps to |
|---|---|
| `.csproj` with `Microsoft.Azure.Functions.Worker` + `Microsoft.Azure.Functions.Worker.Sdk` | **Application Component** — type *Azure Function App (isolated-worker)*. Alias: project name, snake-cased. Label: project name, title-cased ("Orders.Api" → "Orders Api"). |
| `.csproj` with `Sdk="Microsoft.NET.Sdk.BlazorWebAssembly"` | **Application Component** — type *Blazor WebAssembly (standalone)*. |
| Server `.csproj` calling `AddInteractiveWebAssemblyComponents()` / `AddInteractiveWebAssemblyRenderMode()` + sibling `.Client` project | Two Components: *Blazor Web App server* (server project) and *Blazor Web App Client* (`.Client` project), related by Composition from server to Client. |
| `.csproj` with `OutputType=Library` and no Azure Functions / Blazor SDK | **Application Component** — type *library*, or (if the project contains only DTOs / contracts) an **Artifact** referenced via Realisation. Judge by content; default to Component. |
| `.csproj` with `OutputType=Exe` that is not an Azure Function / Blazor host | **Application Component** — type *console / worker service*. |
| Test projects (`xunit`, `nunit`, `Microsoft.NET.Test.Sdk`) | **Not lifted.** Test projects are not architectural Components. |

### Project references → relationships

`<ProjectReference>` between two extracted projects maps to:

| Source project type | Target project type | ArchiMate relationship |
|---|---|---|
| App / Function App / Blazor WASM | Library | **Serving** from referenced library/provider to referencing app/consumer, unless Composition better reflects ownership |
| Function App | Function App | **Serving** from provider Function App to consumer Function App |
| Library | Library | **Composition** if the reference is "A composes B" in its readme/intent; else **Serving** from referenced library/provider to referencing library/consumer |
| App | DTO / Contract-only library | **Realisation** — the app realises the contract |

The skill defaults to **Serving** when intent is ambiguous; the architect overrides.

### Azure Functions bindings → Application Interfaces and relationships

Azure Functions bindings declared in function classes surface as Application Interfaces on the Function App Component, with relationships to Technology Layer resources (lifted by [lifting-rules-bicep.md](lifting-rules-bicep.md)):

| Binding attribute | Interface type on Component | Relationship emitted |
|---|---|---|
| `[HttpTrigger]` | **Application Interface** — type *HTTP endpoint*, label = route template | Exposes Application Service; Serving from the interface/service to an external Actor (forward-only Business Layer stub) |
| `[TimerTrigger]` | **Application Interface** — type *Timer*, label = cron expression | Triggered-by Business Event (forward-only stub — Timer is behaviour trigger) |
| `[CosmosDBTrigger]` / `[CosmosDBInput]` / `[CosmosDBOutput]` | (binding, not an Interface) | **Access** to Data Object + **Serving** from the Cosmos Technology Node to the Component |
| `[BlobTrigger]` / `[BlobInput]` / `[BlobOutput]` | (binding, not an Interface) | **Access** to Data Object + **Serving** from the Storage Technology Node to the Component |
| `[EventGridTrigger]` | **Application Interface** — type *Event subscription* | Triggered-by Application Event / Business Event (stub) |
| `[ServiceBusTrigger]` / `[ServiceBusOutput]` | (binding) | **Flow** to/from Application Event; **Serving** from the Service Bus Technology Node to the Component |
| `[QueueTrigger]` / `[QueueOutput]` | (binding) | **Flow** to/from Application Event; **Serving** from the Storage Queue Technology Node to the Component |
| `[DurableClient]` | (runtime wiring) | No direct element; flags the Component as *Durable orchestration host* |
| `[OrchestrationTrigger]` | **Application Function** — durable orchestrator | Composition to the containing Component |
| `[ActivityTrigger]` | **Application Function** — activity | Composition to the containing Component; Called-by the orchestrator Function |

### Blazor surface → Application Services and Interfaces

| Detection | Maps to |
|---|---|
| Routable component (`@page` directive) in a Blazor project | **Application Service** on the Blazor Component — alias = route, label = route path |
| `@rendermode InteractiveWebAssembly` / `InteractiveServer` / `InteractiveAuto` on a component | Noted as a property of the containing Application Service (interaction style); does not create a separate ArchiMate element |
| `HttpClient.GetFromJsonAsync(...)` against a named service URL that resolves to another Component's Application Interface | **Serving** relationship from the target Component / Interface to the Blazor consumer Component |

### Static Web App routing → Application Interfaces

| `staticwebapp.config.json` fragment | Maps to |
|---|---|
| `routes[]` entry with `"allowedRoles": ["authenticated"]` | **Application Interface** on the hosting SWA Component; labelled by the `route` value |
| `auth` block with `identityProviders` | Application Service *Authentication* on the SWA Component, linked to the Technology Layer via a Serving relationship from the identity provider to the service (forward-only stub unless the provider is explicit) |
| `navigationFallback` for SPA routing | Not lifted — client-side detail |

### External services → Application Components + trust-boundary Grouping

External Application Components are discovered when any of these signals are present:

- Documentation or comments mark a dependency as `External`, `third-party`, or vendor-owned.
- `AddHttpClient(...)`, typed clients, or configuration set a `BaseAddress` outside the local origin and outside known project-hosted endpoints from Bicep parameters.
- `staticwebapp.config.json` CSP allowlists (`connect-src`, `img-src`, `script-src`, etc.) name third-party domains.
- OAuth / API integration patterns identify providers such as identity, payment, email, telemetry, CDN, or product API vendors.

Emit trust-boundary Groupings:

| Detection | Emit |
|---|---|
| `*.csproj`-derived internal Components | `Grouping` named `{Project} (internal)` with Composition membership to internal Application Components |
| External provider Components | One `Grouping` per provider, named `{Provider} (external)`, with Composition membership to that provider's Application Components |

Application Cooperation views place Components visually inside their Grouping. Composition edges used only for the Grouping membership are hidden via the existing ARM hide property when nested. Review emits `AD-21` when an external Application Component is present without an external Grouping.

## Naming conventions

- **Component identifier** — `id-<slug>` where `<slug>` is the project name lowercased with dots replaced by hyphens: `Orders.Api` → `id-orders-api`. Identifiers are stable across re-extracts per reference §6.6.
- **Component `<name>`** — project name with dots replaced by spaces: `Orders.Api` → `Orders Api`. Architects commonly override to a friendlier name (`Orders API`); Extract preserves architect overrides across re-runs (see [drift-detection.md](drift-detection.md)).
- **Service identifier** — `id-<component-slug>-svc-<service-slug>`. `<name>`: short human phrase derived from the route or binding.
- **Interface identifier** — `id-<component-slug>-if-<slug>`. `<name>`: the route template or binding type.

## Output shape

Lifted elements are emitted as OEF XML into the canonical file at `docs/architecture/<feature>.oef.xml`. Fragment from a Build-/Extract-produced file:

```xml
<!-- ==== Application Layer (lifted from .NET solution) ==== -->

<elements>
  <element identifier="id-orders-api" xsi:type="ApplicationComponent">
    <name xml:lang="en">Orders API</name>
    <documentation xml:lang="en">Azure Functions isolated-worker; Orders.Api.csproj</documentation>
  </element>
  <element identifier="id-orders-api-if-post-orders" xsi:type="ApplicationInterface">
    <name xml:lang="en">POST /orders</name>
  </element>
  <element identifier="id-orders-api-svc-place-order" xsi:type="ApplicationService">
    <name xml:lang="en">Place Order</name>
  </element>
  <element identifier="id-orders-core" xsi:type="ApplicationComponent">
    <name xml:lang="en">Orders Core (library)</name>
  </element>
  <element identifier="id-blazor-client" xsi:type="ApplicationComponent">
    <name xml:lang="en">Blazor Client</name>
  </element>
  <element identifier="id-group-orders-internal" xsi:type="Grouping">
    <name xml:lang="en">Orders (internal)</name>
  </element>
  <element identifier="id-group-payment-external" xsi:type="Grouping">
    <name xml:lang="en">Payment provider (external)</name>
  </element>
</elements>

<relationships>
  <relationship identifier="id-rel-compose-api-if"
                source="id-orders-api" target="id-orders-api-if-post-orders"
                xsi:type="Composition"/>
  <relationship identifier="id-rel-realize-svc-if"
                source="id-orders-api-svc-place-order" target="id-orders-api-if-post-orders"
                xsi:type="Realization"/>
  <relationship identifier="id-rel-api-uses-core"
                source="id-orders-api" target="id-orders-core"
                xsi:type="Serving"/>
  <relationship identifier="id-rel-client-calls-api"
                source="id-blazor-client" target="id-orders-api-if-post-orders"
                xsi:type="Serving"/>
  <relationship identifier="id-rel-group-internal-api"
                source="id-group-orders-internal" target="id-orders-api"
                xsi:type="Composition"/>
</relationships>
```

The `Realization` and `Serving` `xsi:type` values are the exact ArchiMate 3.2 relationship names per reference §6.3. `Realization` uses the American spelling — that is the OEF schema's spelling, not an editorial choice.

## What this procedure does not do

- Lift **Business Layer** elements from code. Business Services, Processes, Actors, Roles, Objects are forward-only per reference §7.2. Extract emits them as typed stubs with the `FORWARD-ONLY` marker; this procedure's Application Component `<name>` values are the inference source for stub placeholders.
- Lift **Motivation** or **Strategy** layers. Same — forward-only.
- Produce Archi-native `.archimate` XML. That is a different format; this procedure emits OEF XML only.
- Enforce Appendix B well-formedness. That is Review mode's job. This procedure emits relationships that *should* be valid; Review verifies they *are*.
- Run XSD schema validation. The emitted file references The Open Group's canonical schema URL via `xsi:schemaLocation`; validation is delegated to Archi's import or to `xmllint`.
