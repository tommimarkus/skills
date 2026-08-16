# Extension: .NET — deep-mode procedures

Deep-mode-only procedures for the .NET test-quality-audit extension:
SUT surface enumeration, determinism verification, and the Stryker.NET mutation
tool declaration. Loaded only in Deep mode, for any rubric; Quick audits
never load it. Detection, dispatch, and smells stay in [`core.md`](core.md).

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../../../SKILL.md) — step 2.5 of the deep-mode workflow. This section declares the .NET-specific grep patterns the audit agent uses to enumerate testable symbols in a SUT and cross-reference them against a test project. Applies under both the unit and integration rubrics; not run under the E2E rubric.

### SUT identification

For a given test project (`tests/Foo.Tests/Foo.Tests.csproj`):

1. Parse the `<ItemGroup>` sections of the csproj and collect every `<ProjectReference Include="..." />` entry.
2. For each referenced project, resolve the absolute path relative to the test csproj.
3. Recurse: for each referenced project, parse its csproj and follow its own `<ProjectReference>` entries.
4. Stop at projects whose SDK is **not** a production-code SDK (i.e. a test SDK like `Microsoft.NET.Sdk` + `xunit`/`bunit` references). The closure is the SUT.

In this repo, for example:

- `tests/Lfm.Api.Tests` → SUT closure: `api/Lfm.Api.csproj` + `shared/Lfm.Shared.csproj`.
- `tests/Lfm.App.Core.Tests` → SUT closure: `app/Lfm.App.Core/Lfm.App.Core.csproj` + `shared/Lfm.Shared.csproj`.
- `tests/Lfm.App.Tests` → SUT closure: `app/Lfm.App.csproj` (Blazor WASM) + `app/Lfm.App.Core/Lfm.App.Core.csproj` + `shared/Lfm.Shared.csproj`.

### Grep patterns per gap class

All patterns are case-sensitive ripgrep expressions applied to `.cs` files in the SUT. Each match returns a symbol identifier plus `file:line`.

**`Gap-API` — public methods and types.** Multi-line aware. Detection patterns:

- Public classes / records / structs / interfaces: `^\s*public\s+(sealed\s+|abstract\s+|static\s+|partial\s+)*(class|record|record\s+struct|struct|interface)\s+(?P<name>[A-Z][A-Za-z0-9_]*)`.
- Public instance or static methods: `^\s*public\s+(static\s+|virtual\s+|override\s+|sealed\s+|async\s+|new\s+)*([A-Za-z0-9_<>?,\[\]\s]+)\s+(?P<name>[A-Z][A-Za-z0-9_]*)\s*\(` — then exclude matches where the captured name is a keyword, a constructor (same as the class name), or a C# operator. Ignore files under `obj/`, `bin/`, and generator-output paths.

**`Gap-Route` — HTTP and Functions routes.** Detection patterns:

- Azure Functions isolated: `\[Function\("(?P<name>[^"]+)"\)\]` — capture the function name and any adjacent `[HttpTrigger(...)]` route template.
- HTTP trigger route: `\[HttpTrigger\([^)]*,\s*Route\s*=\s*"(?P<route>[^"]+)"\)\]`.
- HTTP method + route in `HttpTrigger` args: `\[HttpTrigger\(AuthorizationLevel\.[A-Za-z]+,\s*"(?P<methods>[^"]+)"(?:,\s*Route\s*=\s*"(?P<route>[^"]+)")?`.
- ASP.NET Core minimal API: `app\.Map(Get|Post|Put|Delete|Patch)\s*\(\s*"(?P<route>[^"]+)"`.
- ASP.NET Core MVC attribute routing: `\[Route\("(?P<route>[^"]+)"\)\]` and `\[Http(Get|Post|Put|Delete|Patch)(\("(?P<route>[^"]+)"\))?\]`.

**`Gap-Migration` — database migration classes.** Detection patterns:

- Any class in `api/Migrations/` that inherits from or implements a migration base type: `:\s*(?:IAsync)?Migration\b` or `:\s*MigrationBase\b`.
- Any file whose name matches `\d{4}_[a-z0-9_]+\.cs` under `api/Migrations/` — treat the class name declared at top-of-file as the migration identifier even if the base type is missing (documented repo convention).

**`Gap-Throw` — exception throw sites.** Detection patterns:

- `throw\s+new\s+(?P<type>[A-Z][A-Za-z0-9_]*Exception)\s*\(` — capture exception type.
- Record the containing method via the nearest preceding `public|internal|private|protected` method declaration; the audit agent walks up from the match to the enclosing method name.
- Exclude re-throws (`throw;` and `throw ex;`) — those are not new sites.

**`Gap-Validate` — validation attributes on input types.** Detection patterns:

- `\[(Required|StringLength|MaxLength|MinLength|Range|RegularExpression|EmailAddress|Url|CreditCard|Phone)(\([^)]*\))?\]` on a property declaration.
- Capture the containing record / class (input type) and the property name — e.g. `CreateOrderRequest.CustomerId`.

### Cross-reference matching

For each enumerated symbol, the audit agent searches the test project tree (`tests/**/*.cs` except `obj/`, `bin/`, `TestResults/`, `StrykerOutput/`) for at least one of the matches below.

When a test-artifact extension is also loaded, include its test files in the cross-reference if they exercise this .NET SUT's public boundary. For Robot Framework, also search `**/*.robot` and `**/*.resource` files, excluding generated outputs and vendored dependencies. A Robot test can satisfy a .NET gap when it calls the route, command, or public adapter and asserts the required contract. Count that as external contract coverage; do not require a C# test unless the gap is specifically source-level and not observable from Robot.

- **`Gap-API`** — `covered-strong` only when the symbol name appears as an identifier and the same test asserts a return value, published side effect, error, state, or domain outcome. Word-boundary identifier presence by itself is `referenced-weak`. A constructor/import/setup-only mention is `referenced-incidental`.
- **`Gap-Route`** — `covered-strong` only when the route template or Functions name appears and the test asserts the route's published contract: status plus body/header/auth/domain outcome, state change, validation error, or problem code. A test that only asserts `200`, `201`, URL reachability, or no exception is `referenced-weak`. In Robot tests, count RequestsLibrary / custom API-library calls only when they assert the same contract strength.
- **`Gap-Migration`** — the migration class name appears as an identifier in any test body, or the migration file name appears as a path literal.
- **`Gap-Throw`** — both the exception type (e.g. `InvalidOperationException`) *and* the containing method name appear in the same test method body, and the assertion checks the exception or public error contract. If either is missing, or the test only reaches the happy path, the throw site remains a probable gap. Robot tests may cover this only when they assert the public error contract produced by that throw site; they do not cover private throw-site details.
- **`Gap-Validate`** — the input type's property name (e.g. `CustomerId`) appears in a test body that also references the input type and intentionally violates or omits the field (e.g. `new CreateOrderRequest { CustomerId = null }`) with an assertion on validation status / problem details. Payloads that include only valid values are `referenced-weak` for invalid-field coverage. In Robot API tests, count payloads only when they include or omit the field and assert the expected validation status / problem code.

### Known indirect-coverage patterns (carve-outs)

These patterns suppress a false-positive `Gap-API` entry:

- A service method `Foo.BarAsync(...)` is covered indirectly when a Functions endpoint `Foo.BarFunction` that wraps it has a test, and the service type is registered in DI under the Functions project. Search DI registrations (`services.AddScoped<Foo>()` / `services.AddSingleton<Foo>()`) in the Functions project to establish wrapping; if a test exercises the wrapping endpoint and asserts the published contract, record as "indirectly covered via `FooFunction`" and suppress the `Gap-API` entry. If the endpoint test is status-only, keep the service as `referenced-weak`.
- A Robot Framework API, CLI, or browser test can cover a route, function, validation rule, or public adapter when it exercises the .NET public boundary and asserts the relevant contract. Record as "externally covered via Robot `<suite>/<test>`" and suppress only the matching public-boundary gap. Do not suppress unit-seam, private throw-site, or mutation-target findings from Robot evidence alone. Robot happy-path-only rows are weak evidence for negative validation/auth/boundary gaps.
- A `MigrationRunner.RunAsync` test in `tests/Lfm.Api.Tests/` that exercises the runner with seed data covers every migration transitively if the test explicitly asserts post-state for each migration class. Search for the pattern and suppress `Gap-Migration` entries for the covered classes.

### Confidence annotations

- `Gap-API`: **medium** — indirect coverage via controllers / Functions / facade methods is common in this repo.
- `Gap-Route`, `Gap-Migration`, `Gap-Validate`: **high** — these are registered by string or class identity with few indirect-coverage paths.
- `Gap-Throw`: **medium** — generic error-path tests often exercise the method without naming the exception type.

### Recommended `--mutate` follow-up

When the gap report lists a probable `Gap-API` finding on a SUT shape that Stryker.NET supports, the audit agent may suggest a targeted mutation run to confirm: `dotnet stryker --mutate "<path>.cs" --reporter cleartext` (fast — seconds).

---

## Determinism verification

Consumed by [SKILL.md § Determinism verification](../../../SKILL.md) — step 4.5 of the deep-mode workflow. Applies under unit and integration rubrics; not run under the E2E rubric (browser-dominated suites are too expensive to rerun cheaply).

### Cheap-rerun command

Run the non-E2E test project twice, each with structured output for diffing:

```bash
dotnet test tests/<Project>.Tests/<Project>.Tests.csproj \
  --no-build -c Release \
  --logger "trx;LogFileName=run1.trx" \
  --results-directory ./.test-determinism/run1
dotnet test tests/<Project>.Tests/<Project>.Tests.csproj \
  --no-build -c Release \
  --logger "trx;LogFileName=run2.trx" \
  --results-directory ./.test-determinism/run2
```

Compare via `dotnet-trx` or a manual diff of the `<UnitTestResult outcome="Passed|Failed|Skipped">` attributes.

### Gating

- **Project size:** skip and recommend targeted rerun of top-N slowest tests when the test project has ≥ 500 test methods. Determine via `grep -c '\[Fact\|\[Theory' tests/<Project>.Tests/**/*.cs`.
- **Total elapsed time from run 1:** if run 1 takes more than 60 seconds, warn the user before running run 2. Abort if an interactive audit and the user declines.
- **E2E projects:** never run. E2E suites are expensive and browser-dominated; determinism verification there requires different tooling.

### Recommended scope for this repo

- `tests/Lfm.Api.Tests` — small, reruns cheaply.
- `tests/Lfm.App.Core.Tests` — small, reruns cheaply.
- `tests/Lfm.App.Tests` (bUnit) — small, reruns cheaply.
- `tests/Lfm.E2E` — do **not** rerun. The E2E docker stack bringup makes a second full run prohibitive; the audit agent should recommend `--filter FullyQualifiedName~FlakeCandidate` reruns of specific tests identified by static smells instead.

---

## Mutation testing

Stryker.NET is the .NET mutation tool. Load
[../../procedures/mutation-dotnet.md](../../procedures/mutation-dotnet.md) only
in Deep mode when mutation evidence is requested or the Deep audit reaches the
mutation section. Quick audits must not load or apply mutation setup guidance.
