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
