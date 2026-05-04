# .NET Software Design Extension

Load this extension for .NET solutions and projects: `.sln`, `.slnx`, `.csproj`, `.cs`, `Directory.Build.*`, `global.json`, `InternalsVisibleTo`, `IServiceCollection`, `DbContext`, `BackgroundService`, or package references commonly used in .NET applications.

This extension covers design signals, not API runtime, security, or test-quality minutiae. Delegate endpoint contract and API runtime concerns to `api-design`, security posture to `devsecops-audit`, and test quality to `test-quality-audit`.

## Platform Sources

Use Microsoft Learn for platform facts:

- .NET project SDK and SDK-style project facts: https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview
- MSBuild `ProjectReference` and `InternalsVisibleTo` item facts: https://learn.microsoft.com/en-us/visualstudio/msbuild/common-msbuild-project-items
- C# access modifiers and `internal` visibility: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/access-modifiers
- .NET dependency injection fundamentals: https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/basics
- EF Core model/entity facts: https://learn.microsoft.com/en-us/ef/core/ and https://learn.microsoft.com/en-us/ef/core/modeling/entity-types

Any claim about whether those constructs are good design must cite the core software-design reference and, where relevant, the smell catalog.

## Project Assimilation Signals

Inspect:

1. `.sln` / `.slnx` project list and folder grouping.
2. `<ProjectReference>` direction in `.csproj`.
3. `Directory.Build.props` / `Directory.Build.targets` for shared references and visibility changes.
4. Namespaces vs folders.
5. `public` / `internal` surface area and `InternalsVisibleTo`.
6. `IServiceCollection` registration shape and lifetimes.
7. `DbContext`, EF entity classes, migrations, and where entities are referenced.
8. Hosted services, workers, handlers, mediators, repositories, specifications, and background adapters.
9. Packages named `MediatR`, `FluentValidation`, `AutoMapper`, `Ardalis.Specification`, or equivalent as design signals, not automatic smells.

## .NET Design Defaults

- Project references should point toward stable policy or explicit contracts, not from policy into infrastructure.
- Use `internal` to hide implementation details when the assembly boundary is real.
- Treat `InternalsVisibleTo` as a narrow test or friend-assembly exception, not a general escape hatch.
- Register dependencies where composition belongs; avoid resolving services from arbitrary domain code.
- Keep EF Core entities inside the owning persistence/domain boundary unless they are intentionally the domain model for that boundary.
- Do not add repository, unit-of-work, mediator, CQRS, or specification layers unless they reduce real complexity for the known change.
- Prefer vertical slices when feature workflow locality matters more than cross-feature domain reuse.
- Prefer a layered core when shared domain policy is stable and dependency direction is clean.

## Smells

| Code | Name | Signal | Default |
|---|---|---|---|
| `dotnet.SD-C-1` | Project reference cycle | `.csproj` references create a direct or indirect cycle. | block |
| `dotnet.SD-C-2` | Policy depends on infrastructure | Domain/application project references EF, hosting, HTTP, queue, or vendor adapter project without an explicit boundary reason. | block when new |
| `dotnet.SD-C-3` | Shared project gravity | `Shared`, `Common`, `Core`, or `Abstractions` project accumulates unrelated domain policy. | warn |
| `dotnet.SD-C-4` | Service locator by provider | `IServiceProvider` or scoped service resolution is used outside composition/infrastructure code to drive domain flow. | warn |
| `dotnet.SD-B-1` | Namespace/folder drift | Namespace, folder, and project names tell different boundary stories. | info |
| `dotnet.SD-B-2` | Public by default | Types/members are `public` where only one assembly should know them. | warn |
| `dotnet.SD-B-3` | Friend assembly escape hatch | `InternalsVisibleTo` exposes broad internals instead of a narrower seam. | warn |
| `dotnet.SD-B-4` | Hosted service owns policy | `BackgroundService` or worker adapter owns domain policy rather than orchestrating it. | warn |
| `dotnet.SD-S-1` | EF entity leakage | EF entities are used as API DTOs, cross-boundary contracts, or unrelated module state. | warn |
| `dotnet.SD-S-2` | One class, three roles | A type simultaneously acts as persistence entity, domain aggregate, and transport DTO without an explicit boundary decision. | warn |
| `dotnet.SD-S-3` | Invariant in service layer | Aggregate/state invariant is enforced only by an external service method. | warn |
| `dotnet.SD-W-1` | Repository over EF without force | Repository/unit-of-work layer wraps EF Core with pass-through CRUD only. | info |
| `dotnet.SD-W-2` | Mediator/CQRS ceremony | MediatR/CQRS splits a simple in-process action into handlers, requests, and pipeline steps without current complexity. | warn |
| `dotnet.SD-W-3` | Specification for trivial query | Specification objects encode single-use simple predicates. | info |
| `dotnet.SD-E-1` | Accidental hybrid architecture | Vertical slices and layers coexist without a rule for which owns policy, workflow, or persistence. | warn |

## Review Notes

- Use project/namespace evidence before naming architectural intent.
- Cite Microsoft Learn only for what .NET constructs mean. Cite the core reference for why a dependency, boundary, or abstraction is healthy or unhealthy.
- Do not flag a library merely by name. Flag the mismatch between the library's design cost and the known problem.
