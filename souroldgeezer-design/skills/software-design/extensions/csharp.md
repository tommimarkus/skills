# C# and .NET Software Design Extension

Load for `.sln`, `.slnx`, `.csproj`, `.fsproj`, `.vbproj`, `Directory.Build.*`,
`Directory.Packages.props`, `global.json`, `InternalsVisibleTo`,
`IServiceCollection`, `DbContext`, `BackgroundService`, worker services,
package refs, or C# modules.

Covers C# on .NET — project/assembly/DI/EF/hosted-service structure **and** C#
language semantics. Delegate HTTP to `api-design`, security to `devsecops-audit`,
and tests to `test-quality-audit`.

F# and VB.NET sources load this extension for .NET build/module facts only
(`.sln`, `.fsproj`/`.vbproj`, `Directory.Build.*`, `global.json`, project refs,
assemblies, DI wiring); their language semantics are unsupported, so
language-level review uses core `SD-*` only, not the C# defaults below.

Sources: .NET project SDK
https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview, DI
https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/basics,
and EF modeling https://learn.microsoft.com/en-us/ef/core/modeling/.

Inspect project references, namespaces, public/internal/friend types, DI
composition, EF entities, hosted services, options, shared projects, generated
code, and validation (`dotnet build`, `dotnet test`, analyzers, an
API-compatibility diff for published packages, or smoke).

Defaults: project refs are the dependency graph; public APIs/friend assemblies
are contracts; composition roots own DI; controllers/workers stay thin; EF
entities, DTOs, and domain models split when invariants or ownership differ;
Repository/MediatR/CQRS ceremony needs current force; records/`readonly struct`/
value objects carry semantics; nullable-reference annotations are part of the
contract; `IDisposable`/`IAsyncDisposable` and
`async`/`Task`/`ValueTask`/`CancellationToken` name lifetime and concurrency
ownership; DI lifetimes are contracts — a singleton capturing a scoped
service breaks ownership; published-package compatibility is binary, not
source.

For Build mode, include `devsecops-audit` Quick review for reflection, dynamic
loading, serialization, process execution, generated code, or hosting-boundary
changes when available. Otherwise use the cheapest build/test/analyzer/smoke.

Smell codes: `csharp.SD-C-*` for project cycles, policy-to-adapter refs,
service location, and shared-core gravity; `csharp.SD-B-*` for namespace,
public/friend, controller, worker, or hosted-service boundary drift;
`csharp.SD-S-*` for EF/DTO/domain or invariant leakage; `csharp.SD-W-*` for
pass-through repository/MediatR/CQRS ceremony; `csharp.SD-E-*` for mixed layer
rules; `csharp.SD-Q-*` for reflection/generated boundary ownership gaps.

Key codes: `csharp.SD-C-1` project cycle or policy-to-adapter reference;
`csharp.SD-B-2` public/friend surface exposes internals; `csharp.SD-S-1`
EF/DTO/domain collapse hides ownership; `csharp.SD-W-1` repository/unit-of-work
wraps EF with pass-through CRUD; `csharp.SD-Q-1` reflection/generated boundary
lacks owner and validation.

Only these key codes are citable; the `Smell codes:` families above describe
scope only. Emit core `SD-*` for anything not covered by a key code.
