# C# and .NET Test-Code Lane

Load when writing or restructuring this stack's test files, fixtures, and
helpers, or on a `tdd-policy` handoff for the detected stack.

Sources: https://xunit.net/docs/shared-context; https://xunit.net/docs/running-tests-in-parallel;
https://xunit.net/docs/config-xunit-runner-json; https://docs.nunit.org/articles/nunit/writing-tests/attributes/setculture.html;
https://learn.microsoft.com/dotnet/core/extensions/timeprovider-testing; https://learn.microsoft.com/dotnet/core/testing/selective-unit-tests.

## Shared test support

- Search the test-support project or shared folder (builders, fakes, fixtures,
  base classes) before defining a helper. One used by several test projects
  moves into a test-support class library they reference; it does not reference
  the test SDK package (that makes it a test project with no tests).
- Resolve test data from `AppContext.BaseDirectory` (files copied to output),
  never the working directory.

## Setup lifetime

- xUnit and MSTest create a class instance per test; NUnit shares one instance
  across a fixture's tests unless `[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]`,
  so its fields carry state between tests (core `SD-C-4`). Async setup uses
  `IAsyncLifetime` (xUnit) or the framework's async setup attributes.
- One instance per test class: `IClassFixture<T>`. Across several classes:
  `ICollectionFixture<T>` on a `[CollectionDefinition]` class that test classes
  join with `[Collection("name")]`. xUnit v3 also has an assembly-level
  fixture, shared by every class and so required to be thread-safe.
- Widest scope only for immutable or resettable infrastructure (a container, a
  read-only seed): a shared fixture couples every test that uses it. Share one
  `WebApplicationFactory` per class or collection; `WithWebHostBuilder` in each
  test builds a new host.

## Time, randomness, and ambient environment

- Production code takes `TimeProvider`; tests pass `FakeTimeProvider`
  (Microsoft.Extensions.TimeProvider.Testing) and `Advance` it, never sleeping.
  Wait on a signal or observable condition with a bounded timeout.
- Inject `TimeZoneInfo`, a seeded random source, and in-memory `IConfiguration`
  rather than reading `TimeZoneInfo.Local`, `Random.Shared`, or environment
  variables (core `SD-B-5`).
- Culture: `CultureInfo.CurrentCulture` is per thread and flows across awaits.
  Set and restore it in the test, use NUnit `[SetCulture]` / `[SetUICulture]`,
  or pin the defaults once (`DefaultThreadCurrentCulture` in a module
  initializer); xUnit v3 has a runner `culture` setting (`"invariant"` or a
  BCP 47 name). Read the culture back or format a known value: where ICU data
  is missing or globalization-invariant mode is on, a named culture does not
  behave as requested.

## Isolation and parallel runs

- xUnit runs test classes (one collection each by default) in parallel and the
  tests inside a collection in series; sharing a collection serializes classes
  that touch common state. `[CollectionDefinition(DisableParallelization =
  true)]` opts a collection out; parallel mode and thread limit are runner
  settings, and `xunit.runner.json` is ignored unless copied to the output.
- NUnit runs sequentially until an assembly `[Parallelizable]` opts in, with
  `[NonParallelizable]` to exclude; MSTest opts in with an assembly
  `[Parallelize]` and excludes with `[DoNotParallelize]`.
- Parallel-safe means no static or process-global mutable state and no shared
  ports, files, or database rows; environment-variable and current-directory
  changes need serialization.

## Lanes and durations

- Mark lanes with `[Trait("Category", "...")]` (xUnit), `[Category]` (NUnit),
  or `[TestCategory]` (MSTest); select with `dotnet test --filter`, or split
  lanes into separate test projects.
- Read per-test durations from the runner's detailed console logger or TRX
  report (under Microsoft.Testing.Platform, the TRX extension); class and
  collection fixture setup never shows in per-test times, so time it apart.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
