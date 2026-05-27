# .NET Lifting Rules

Use for Extract when .NET projects, Azure Functions, Blazor/Web clients,
hosted workers, or typed clients are in scope. Load
`../source-weighting.md` before classifying ambiguous surfaces.

## Source Mapping

| Source evidence | Prefer | Avoid |
|---|---|---|
| `*.sln` | `*.sln` is repository/package context and source evidence grouping | Application Component by itself |
| Deployable `*.csproj`, Function App host, worker, API host, SPA | Application Component | Capability or Business Actor |
| Controller/function route, GUI route, SDK/client entrypoint, route or GUI surface | Application Interface | Application Service when the access surface is the concern |
| Exposed endpoint behavior consumed by another component | Application Service | Application Interface when behavior is the concern |
| handler/orchestrator behavior, internal computation, module-owned logic | Application Function; Application Process when ordered behavior/outcome is the concern | Application Service if not exposed or consumed |
| DTO, message, persisted model, API payload | Data Object | Business Object without business-source evidence |
| Durable orchestrator or UI/API flow | Business Process candidates only when outcome and participant context are clear | Final Business Process without confirmation |

## ASP.NET Core Evidence

ASP.NET Core evidence is additive. Use it only after the generic .NET rule has
established the source fact.

- Controllers, minimal APIs, Razor Pages, SignalR hubs, gRPC services, and
  endpoint route maps identify access surfaces.
- Middleware, filters, hosted handlers, and request pipeline internals can
  support Application Function unless the view concern is the exposed behavior.
- OpenAPI generation, endpoint metadata, and route groups can support
  Application Interface or service grouping, but do not create Business
  Capability or Product claims.

## Azure Functions Evidence

Azure Functions evidence is additive. Use it only after the generic .NET rule
has established the source fact.

- Function App or worker host is a deployable Application Component by concern.
- HTTP triggers identify access surfaces; queue, timer, service bus, event hub,
  blob, and durable triggers identify Application Events or Interfaces by view
  concern.
- Durable orchestrators can support Application Process; keep Business Process
  candidate until outcome and participant context are confirmed.
- Binding attributes and app settings support dependency, Access, Flow, or
  Triggering evidence only when the architectural claim is clear.

## Blazor Evidence

Blazor evidence is additive. Use it only after the generic .NET rule has
established the source fact.

- Blazor WebAssembly client, hosted client, server app, or Web App project can
  be an Application Component when it is a deployable/runtime boundary.
- Routes, pages, and routable components are GUI access surfaces when they are
  architecture-significant entry points.
- Component internals, render fragments, and local state stay out unless the
  package models a UI/API flow; use `app-design` for detailed UI behavior.
- Hosted Blazor should separate client app, server/API host, and shared
  contracts instead of flattening all projects into one component.

## EF Core Evidence

EF Core evidence is additive. Use it only after the generic .NET rule has
established the source fact.

- `DbContext`, entity types, migrations, query models, and persisted DTOs can
  support Data Object choices.
- Repositories, data services, and direct context usage support Access
  relationships when passive data use is identified.
- Migration files and generated model snapshots are Artifacts unless migration
  architecture is the requested concern.

## Worker Evidence

Worker and hosted service evidence is additive. Use it only after the generic
.NET rule has established the source fact.

- `IHostedService`, `BackgroundService`, worker templates, queue consumers,
  timers, and message handlers can support Application Function, Application
  Event, Application Process, Flow, or Triggering by concern.
- Long-running workers are Application Components only when the project or
  deployment boundary supports that claim.
- Do not infer a Business Process from a worker, queue, or topic name alone.

## Relationships

- `ProjectReference`: Composition for strong package/part ownership; Serving
  only when runtime dependency behavior is the claim.
- Host to internal function/process: Assignment when the host performs behavior.
- Component to exposed service: Realization when the component fulfills the
  service abstraction.
- Component/service to API or GUI surface: Composition or Aggregation for
  ownership; Realization only when the model intentionally says the component
  fulfills the interface abstraction.
- SDK/client data access: Access only when passive structure is identified.

## Package Output

Add source refs and only views with a clear question. Validate/render before
readiness. Use source-backed groups for solution folders, deployable hosts,
bounded contexts, or meaningful dependency clusters; avoid grouping generic
shared libraries.
