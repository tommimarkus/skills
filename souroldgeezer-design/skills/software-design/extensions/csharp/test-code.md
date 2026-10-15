# C# and .NET Test-Code Lane

Load when writing or restructuring this stack's test files, fixtures, and
helpers, or on a `tdd-policy` handoff for the detected stack.

Sources: xUnit shared context https://xunit.net/docs/shared-context, xUnit
parallelism https://xunit.net/docs/running-tests-in-parallel, xUnit runner
settings https://xunit.net/docs/config-xunit-runner-json, NUnit culture
attributes https://docs.nunit.org/articles/nunit/writing-tests/attributes/setculture.html,
FakeTimeProvider https://learn.microsoft.com/dotnet/core/extensions/timeprovider-testing,
test filtering https://learn.microsoft.com/dotnet/core/testing/selective-unit-tests.

## Shared test support

- Search the existing test-support project or shared folder (builders, fakes,
  fixtures, base classes) before defining a helper.
- A helper used by more than one test project moves into a test-support project
  that test projects reference; keep it out of production assemblies.

## Setup lifetime

- Per-test setup is the constructor and `Dispose`; async setup or cleanup uses
  `IAsyncLifetime` (xUnit) or the runner's async setup attributes.
- One instance per test class: `IClassFixture<T>`. Across several classes:
  `ICollectionFixture<T>` on a `[CollectionDefinition]` class that test classes
  join with `[Collection("name")]`. xUnit v3 also has an assembly-level
  fixture, shared by every class and so required to be thread-safe. NUnit and
  MSTest offer one-time fixture, class, and assembly setup attributes.
- Widest scope only for immutable or resettable infrastructure (a container, a
  read-only seed): a class or collection fixture is shared by all its tests, so
  a mutable one couples them (core `SD-C-4`).

## Time, randomness, and ambient environment

- Production code takes `TimeProvider`; tests pass `FakeTimeProvider`
  (Microsoft.Extensions.TimeProvider.Testing) and `Advance` it, never sleeping.
  Wait on a signal or observable condition with a bounded timeout.
- Inject `TimeZoneInfo` and a seeded or injected random source rather than
  `TimeZoneInfo.Local` or `Random.Shared` (core `SD-B-5`).
- Culture: set `CultureInfo.CurrentCulture` and `CurrentUICulture` inside the
  test and restore them (dispose a scope), or use NUnit `[SetCulture]` /
  `[SetUICulture]`. xUnit v3 also has a runner `culture` setting
  (`"invariant"` or a BCP 47 name) for a whole assembly.
- Assert the setting took effect (read the culture back, or format a known
  value): where ICU data is missing or globalization-invariant mode is on, a
  named culture does not behave as requested.

## Isolation and parallel runs

- xUnit runs test classes (one collection each by default) in parallel and the
  tests inside a collection in series; sharing a collection serializes classes
  that touch common state. `[CollectionDefinition(DisableParallelization =
  true)]` opts a collection out; the runner's parallel mode and thread limit
  are assembly or runner settings.
- NUnit uses `[Parallelizable]` / `[NonParallelizable]`; MSTest uses its
  parallelize attribute and `DoNotParallelize`.
- Parallel-safe means no static or process-global mutable state, no shared
  ports, files, or database rows; unique per-test names or temp directories
  (core `SD-C-4`). Environment-variable and current-directory changes need
  serialization.

## Lanes and durations

- Mark lanes with `[Trait("Category", "...")]` (xUnit), `[Category]` (NUnit),
  or `[TestCategory]` (MSTest); select with `dotnet test --filter`, or split
  lanes into separate test projects.
- Read per-test durations from the runner's detailed console logger or its TRX
  report (under Microsoft.Testing.Platform, the TRX extension) rather than
  guessing which tests are slow.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
