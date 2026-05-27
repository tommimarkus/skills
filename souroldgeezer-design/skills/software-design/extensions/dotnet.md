# .NET Software Design Extension

Load for `.sln`, `.slnx`, `.csproj`, `Directory.Build.*`, `global.json`,
`InternalsVisibleTo`, `IServiceCollection`, `DbContext`, `BackgroundService`,
worker services, package refs, or C# modules.

Covers .NET project/module/API design. Delegate HTTP to `api-design`, security
to `devsecops-audit`, and tests to `test-quality-audit`.

Sources: .NET project SDK
https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview, DI
https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/basics,
and EF modeling https://learn.microsoft.com/en-us/ef/core/modeling/.

Inspect project references, namespaces, public/internal/friend types, DI
composition, EF entities, hosted services, options, shared projects, generated
code, and validation (`dotnet build`, `dotnet test`, analyzers, or smoke).

Defaults: project refs are the dependency graph; public APIs/friend assemblies
are contracts; composition roots own DI; controllers/workers stay thin; EF
entities, DTOs, and domain models split when invariants or ownership differ;
Repository/MediatR/CQRS ceremony needs current force.

For Build mode, include `devsecops-audit` Quick review for reflection, dynamic
loading, serialization, process execution, generated code, or hosting-boundary
changes when available. Otherwise use the cheapest build/test/analyzer/smoke.

Smell codes: `dotnet.SD-C-*` for project cycles, policy-to-adapter refs,
service location, and shared-core gravity; `dotnet.SD-B-*` for namespace,
public/friend, controller, worker, or hosted-service boundary drift;
`dotnet.SD-S-*` for EF/DTO/domain or invariant leakage; `dotnet.SD-W-*` for
pass-through repository/MediatR/CQRS ceremony; `dotnet.SD-E-*` for mixed layer
rules; `dotnet.SD-Q-*` for reflection/generated boundary ownership gaps.
