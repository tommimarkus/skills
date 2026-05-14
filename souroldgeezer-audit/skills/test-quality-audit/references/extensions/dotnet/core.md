# Extension: .NET — core

Shared core for the .NET test-quality-audit extension. This file is loaded **whenever a .NET project is detected in the audit target**, before step 0b (rubric selection). It owns everything that is not rubric-exclusive: detection signals, test-type dispatch, test-double classification, rubric-neutral smells, carve-outs, SUT surface enumeration, determinism verification, and the Stryker mutation tool declaration.

Rubric-exclusive content lives in the rubric addons:

- [`unit.md`](unit.md) — `Applies to: unit` smells (mocking-owned-class, bUnit `MarkupMatches`, etc.)
- [`integration.md`](integration.md) — `dotnet.I-*` smells, auth matrix enumeration, migration upgrade-path enumeration.
- [`e2e.md`](e2e.md) — E2E sub-lane refinements (stub; no `dotnet.E-*` smells declared yet).

Covers xUnit, NUnit, MSTest, bUnit (Blazor component testing), Playwright .NET (browser-driven E2E), Selenium.WebDriver, and the commonly-used mocking and assertion libraries (Moq, NSubstitute, FakeItEasy, FluentAssertions).

## Detection signals

Load this extension when the audit target contains any of:

- `*.csproj` or `*.sln` files.
- A `.cs` file with `using Xunit;` / `using NUnit.Framework;` / `using Microsoft.VisualStudio.TestTools.UnitTesting;` / `using Bunit;` / `using Microsoft.Playwright;` / `using OpenQA.Selenium;`.
- A `.csproj` with `<PackageReference Include="xunit"` / `"nunit"` / `"MSTest.TestAdapter"` / `"bunit"` / `"Moq"` / `"NSubstitute"` / `"FakeItEasy"` / `"FluentAssertions"` / `"Microsoft.Playwright"` / `"Selenium.WebDriver"` / `"Testcontainers"`.
- A `global.json` or `dotnet-tools.json` in the target tree.

Detection glob shortcuts: `**/*.csproj`, `**/*Tests.cs`, `**/*Tests/*.cs`, `**/Tests/**/*.cs`.

---

## Test type detection signals

Consumed by [SKILL.md § 0b (Rubric selection)](../../../SKILL.md). Declares which patterns route a .NET test to the integration or E2E rubric instead of the unit rubric. A test with no matching integration or E2E signal defaults to the unit rubric — explicit and backwards compatible.

### Integration rubric signals

Route the test (or the containing file / project) to the integration rubric when any of these are present:

- **Project-level.** Project name matches `*Integration*.Tests*`, OR the project's `<ProjectReference>` transitive closure contains a project using the ASP.NET Core web SDK (`Microsoft.NET.Sdk.Web`).
- **Using directive.** `using Microsoft.AspNetCore.Mvc.Testing;` — imports `WebApplicationFactory<T>`. `using Aspire.Hosting.Testing;` — imports `DistributedApplicationTestingBuilder` and `IDistributedApplicationTestingBuilder` (.NET Aspire 9.1+; `IDistributedApplicationTestingBuilder` inherits from `IDistributedApplicationBuilder` as of that release).
- **Construction.** The test constructs or injects any of: `WebApplicationFactory<T>`, `HostBuilder`, `IHostBuilder`, `TestServer`, `DistributedApplicationTestingBuilder.CreateAsync<TEntryPoint>(...)` / `DistributedApplicationTestingBuilder.CreateAsync(typeof(Program), ...)` (.NET Aspire), or obtains an `HttpClient` via `factory.CreateClient()`.
- **Real infrastructure helpers.** `using Testcontainers.*;`, `using WireMock.Server;`, Respawn for per-test cleanup, or a similar helper that spins up a real adjacent dependency.
- **Emulator endpoints.** A `CosmosClient` / `BlobServiceClient` / `QueueClient` / equivalent constructed against a local emulator endpoint (`https://localhost:8081` for the Cosmos emulator, `http://127.0.0.1:10000` for Azurite, etc.) rather than mocked.

### Unit rubric signals (default)

Route to the unit rubric (the default) when:

- The test instantiates the SUT directly (`new OrderService(mockRepo.Object, ...)`) with `Mock<T>` / `Substitute.For<T>` / `A.Fake<T>()` dependencies, and
- The file does not import or construct any of the integration-rubric markers above.

### E2E rubric signals

Route the test (or the containing file / project) to the E2E rubric when any of these are present:

- **Project-level.** Project name matches `*E2E*` or `*EndToEnd*`, OR the `.csproj` contains a `<PackageReference>` to `Microsoft.Playwright`, `Microsoft.Playwright.NUnit`, `Microsoft.Playwright.MSTest`, `Microsoft.Playwright.Xunit`, `Microsoft.Playwright.TestAdapter`, `Azure.Developer.Playwright.NUnit` (Azure Playwright Workspaces, cloud browser runner), `Azure.Developer.MicrosoftPlaywrightTesting.NUnit` (Microsoft Playwright Testing Preview), or `Selenium.WebDriver`.
- **Using directive.** `using Microsoft.Playwright;`, `using Microsoft.Playwright.NUnit;`, `using Microsoft.Playwright.MSTest;`, `using Microsoft.Playwright.Xunit;`, `using Azure.Developer.Playwright.NUnit;`, `using Azure.Developer.MicrosoftPlaywrightTesting.NUnit;`, `using OpenQA.Selenium;`, or `using OpenQA.Selenium.Chrome;`.
- **Construction.** The test injects or constructs an `IPlaywright`, `IBrowser`, `IBrowserContext`, `IPage`, `IWebDriver`, or similar browser-session type.
- **Base class or helper.** The test class inherits from `PageTest`, `ContextTest`, `BrowserTest`, `PlaywrightTest` (Playwright NUnit/MSTest/Xunit base classes from `Microsoft.Playwright.NUnit` / `.MSTest` / `.Xunit`), `PlaywrightServiceBrowserNUnit` / `ServicePageTest` (Azure Playwright Workspaces cloud-browser bases), or equivalent project-specific bases that expose a browser session.

Once a file is routed to E2E, classify each test into a sub-lane (`F` functional / `A` accessibility / `P` performance / `S` security) using the sub-lane signals in [SKILL.md § 0b step 5](../../../SKILL.md):

- `[Trait("Category", "Accessibility")]` or axe / `AxeBuilder` / `AccessibilityHelper`-style imports → sub-lane **A**.
- `[Trait("Category", "Perf")]` or Web Vitals / `PerformanceObserver` / `PerfHelper`-style imports → sub-lane **P**.
- `[Trait("Category", "Security")]` or assertions on CSP / cookie jar / cross-origin iframe / tampered-cookie behaviour → sub-lane **S**.
- Otherwise → sub-lane **F**.

### Mixed-file handling

When a single test class contains multiple patterns — some tests use only mocked dependencies, some construct `WebApplicationFactory<T>`, some drive a browser via `IPage` — classify each test method individually. A test is unit, integration, *or* E2E under exactly one rubric; never more than one. The audit records the chosen rubric (and, for E2E, the sub-lane) per test so the reader can audit the dispatch itself.

---

## Test double classification

Required reading for auditors: [../../docs/quality-reference/unit-testing.md § 7.1](../../docs/quality-reference/unit-testing.md) — the Fowler taxonomy (Dummy / Stub / Spy / Mock / Fake) that core smells like `HC-5` and `HC-6` are scoped to.

Moq, NSubstitute, FakeItEasy, and Microsoft.Extensions.Logging.Testing all produce test doubles through one construction syntax but serve different roles in the taxonomy. Classify each double before applying interaction-pinning smells:

### Moq

- **Stub:** `new Mock<T>()` (or `Mock.Of<T>(...)`) plus only `.Setup(...)` / `.SetupGet(...)` / `.Returns(...)` / `.ReturnsAsync(...)`, with `mock.Object` passed to the SUT. **No `.Verify(...)` call anywhere in the test body.**
- **Mock (behavior verification):** any `.Verify(...)` / `.VerifyAll()` / `.VerifyNoOtherCalls()` / `.VerifySet(...)` on the double. This is the lens under which `HC-5`, `HC-6`, `dotnet.HC-1` apply.
- **Strict mock:** `new Mock<T>(MockBehavior.Strict)` — every call must be pre-setup; unspecified calls throw. Always a mock for taxonomy purposes.

### NSubstitute

- **Stub:** `Substitute.For<T>()` plus only `.Returns(...)` / `.ReturnsForAnyArgs(...)` / `.ReturnsNull()`, no `Received` call.
- **Mock:** any `.Received(...)` / `.ReceivedWithAnyArgs(...)` / `.DidNotReceive(...)` / `.DidNotReceiveWithAnyArgs(...)` call.

### FakeItEasy

- **Stub:** `A.Fake<T>()` plus only `A.CallTo(() => ...).Returns(...)` / `.ReturnsNextFromSequence(...)`.
- **Mock:** any `A.CallTo(() => ...).MustHaveHappened(...)` / `.MustNotHaveHappened()` / `.MustHaveHappenedOnceExactly()`.

### Fakes (working implementations)

Types named `Fake*`, `InMemory*`, `TestLogger<T>`, `FakeLogger` / `FakeLogger<T>` (namespace `Microsoft.Extensions.Logging.Testing`, shipped in the `Microsoft.Extensions.Diagnostics.Testing` NuGet package), `CapturingLogger`, `FakeTimeProvider` (namespace `Microsoft.Extensions.Time.Testing`, shipped in the `Microsoft.Extensions.TimeProvider.Testing` NuGet package), or any custom class that implements the real interface with a recording / in-memory / shortcut body are Fowler **fakes**, not mocks. Positive signals: `dotnet.POS-5` (capture logger), `dotnet.POS-6` (FakeTimeProvider). Do not apply `HC-5` / `HC-6` / `dotnet.HC-1` to fakes.

**Note on package vs namespace.** The package name and namespace differ for both Microsoft.Extensions testing helpers above. Treat the `using` directive (`using Microsoft.Extensions.Time.Testing;`, `using Microsoft.Extensions.Logging.Testing;`) as the authoritative detection signal; the package name appears only in the csproj's `<PackageReference>`.

### Interpretation rules

- **Mixed use in one test.** If a test body constructs a `Mock<T>` that is treated as a stub (no `.Verify`) *and* another `Mock<U>` that is verified (mock), classify each double independently. Smells like `HC-5` apply only to the mocked collaborator.
- **One mock per finding.** If a test has three mock collaborators and only one is over-verified, the finding names the offending collaborator rather than marking the entire test as `HC-6`.
- **Same-module owned types.** `dotnet.HC-4` (mocking an owned concrete class) applies regardless of stub-vs-mock classification — the construction of a double against an owned concrete class is the smell, not the verification mode. `dotnet.HC-4` lives in [`unit.md`](unit.md) because under the integration rubric, mocking an owned collaborator is already a scope leak (`I-HC-A1`).
- **Heavy `It.IsAny<T>()` in `Setup`.** `dotnet.LC-1` applies when the double is used as a stub — that's the case where `Setup` is the entire contract. A mock with `It.IsAny<T>()` in `Setup` plus a strict `.Verify` is a different smell (`dotnet.HC-1` or core `HC-6`) covered elsewhere. `dotnet.LC-1` lives in [`unit.md`](unit.md).

---

## Framework-specific high-confidence smells (`dotnet.HC-*`)

These smells apply under both the unit and integration rubrics (`Applies to: unit, integration`). Unit-only framework smells live in [`unit.md`](unit.md); integration-only framework smells live in [`integration.md`](integration.md).

### `dotnet.HC-1` — Moq `.Verify(...)` with a specific `Times.Exactly(N)` matching loop count

**Applies to:** `unit, integration`

**Detection:** `\.Verify\(.*Times\.Exactly\(\s*\d+\s*\)\)` where N is a small integer that also appears as a literal collection size in the Arrange section.

**Smell:** the test pins the number of calls to the collaborator to match the current implementation's loop structure. Refactoring the SUT to batch calls will break the test without changing observable behavior.

**Example (smell):**
```csharp
var items = new[] { "a", "b", "c" };
await sut.ProcessAsync(items);
repoMock.Verify(r => r.SaveAsync(It.IsAny<Item>()), Times.Exactly(3));
```

**Rewrite (intent):**
```csharp
var items = new[] { "a", "b", "c" };
await sut.ProcessAsync(items);
var saved = await repo.GetAllAsync();
saved.Select(s => s.Name).Should().BeEquivalentTo(items);
```

---

### `dotnet.HC-2` — Verifying `ILogger.Log(...)` string content as a contract

**Applies to:** `unit, integration`

**Detection:** `\.Verify\(.*ILogger|LoggerMessage|Log\(It\.Is<.*LogLevel` combined with matching on a string literal.

**Smell:** the test asserts that a log line was emitted with a particular string. Unless the log is a *published contract* (audit event, metric, structured telemetry with a schema), the log message is a development aid, not a behavior. Pinning it blocks every refactor that touches the message.

**Carve-out:** if the log call targets a structured audit-event helper (e.g. a `LoggerMessage`-generated method whose name indicates it is an audit event, or a log with a documented event-id contract), the assertion is on a published side effect — that is `POS-3`, not a smell.

**Rewrite:** use a capture helper (a `TestLogger<T>`-style fake) to assert on structured properties by key, not on rendered strings.

---

### `dotnet.HC-3` — `Assert.NotNull(x); Assert.Equal(y, x.Prop)` as the entire assertion

**Applies to:** `unit, integration`

**Detection:** an `Assert.NotNull(...)` or `.Should().NotBeNull()` followed by a single property-level assertion, with no further checks on an object whose contract is the whole shape.

**Smell:** the method's observable behavior is the full returned object; the test only pins one field. Most of the contract is unverified.

**Rewrite:** assert the whole object with `.Should().BeEquivalentTo(expected)` against a spec-derived expected value, or split into multiple tests each covering one property.

---

### `dotnet.HC-5` — FluentAssertions chain with only `.Should().NotBeNull()` on a complex return

**Applies to:** `unit, integration`

**Detection:** `.Should().NotBeNull()` on a return value, with no further assertions on the object's contents, when the method returns a complex type.

**Smell:** asserts only that the method didn't return `null`, ignoring the actual contract.

**Rewrite:** assert on the returned object's properties, or on the full shape via `.BeEquivalentTo`.

---

### `dotnet.HC-7` — `DateTime.Now` / `DateTime.Today` / `DateTimeOffset.Now` in a test body

**Applies to:** `unit, integration`

**Detection:** any test method body containing `DateTime\.(Now|Today|UtcNow)` or `DateTimeOffset\.(Now|UtcNow)` as a direct call (not through a `TimeProvider` abstraction). More specific than core `HC-11` — `dotnet.HC-7` covers the .NET idiom.

**Smell:** the test reads the real clock. Tests that use the real clock pass when the author runs them and fail at midnight or on daylight-saving transitions. Core `HC-11` covers the general case; this smell refines detection for .NET.

**Carve-out:** if the test calls `DateTime.UtcNow` solely to generate a unique identifier (e.g. `$"test-{DateTime.UtcNow.Ticks}"`) and does not use the value in an assertion, do not flag. The canonical unique-id generation pattern is benign.

**Rewrite:** inject `TimeProvider` (.NET 8+) and use `FakeTimeProvider` with a pinned instant — see `dotnet.POS-6`.

---

### `dotnet.HC-6` — Single-line `[Fact]` with structural-only assertion on a nullable method

**Applies to:** `unit, integration`

**Detection:** a `[Fact]`-decorated method whose body is `var result = sut.Method(); Assert.NotNull(result);` (or `.Should().NotBeNull()`), nothing more.

**Smell:** the test is a presence check, not a behavior check. It passes for any implementation that returns non-null, including wrong ones.

**Rewrite:** either remove (if the only behavior is "doesn't crash") or add assertions on the returned value.

---

## Framework-specific low-confidence smells (`dotnet.LC-*`)

These smells apply under both the unit and integration rubrics. Unit-only low-confidence smells live in [`unit.md`](unit.md).

### `dotnet.LC-2` — `[Theory]` with `[InlineData]` where all cases produce the same expected value

**Applies to:** `unit, integration` — refines core `LC-8` / `I-LC-4`.

**Detection:** multiple `[InlineData(...)]` on a `[Theory]` where inspection shows every case asserts the same expected literal.

**Why low-confidence:** the parameterization isn't doing work. May indicate the author intended to cover equivalence classes but the assertion is too coarse.

---

### `dotnet.LC-4` — SUT constructed via reflection or `Activator.CreateInstance`

**Applies to:** `unit, integration`

**Detection:** `Activator\.CreateInstance|typeof\(.*\)\.GetConstructor` in Arrange.

**Why low-confidence:** usually means the SUT has inaccessible constructors or the test is reaching into internals.

---

### `dotnet.LC-6` — `[Theory]` missing contract-derived boundary rows

**Applies to:** `unit, integration` — refines core `LC-11`.

**Detection:** a `[Theory]` method with a numeric parameter (`int`, `long`, `double`, `decimal`, `float`), string parameter, collection parameter (`T[]`, `IEnumerable<T>`, `List<T>`), enum/state parameter, or input DTO whose validation attributes expose a range or partition. Collect every `[InlineData(...)]` / `[MemberData(...)]` / `[ClassData(...)]` row feeding that parameter. First inspect the visible contract:

- Data annotations: `[Range]`, `[StringLength]`, `[MinLength]`, `[MaxLength]`, `[Required]`, `[RegularExpression]`.
- FluentValidation rules: `.MinimumLength(...)`, `.MaximumLength(...)`, `.InclusiveBetween(...)`, `.GreaterThan(...)`, `.LessThanOrEqualTo(...)`, `.Must(...)`.
- Route constraints and model-binding constraints.
- Enum / state-transition branches and guard clauses.
- Persistence constraints that are asserted through request/response or DB state.

Flag when no row covers the contract-derived boundary coverage items, or when rows cover only generic sentinels while richer edges are visible. Examples:

- A login length contract `6..15` needs `5/6` and `15/16` for 2-value BVA; `0` alone is `sentinel-only`.
- A `[Range(1, 10)]` quantity needs `0/1` and `10/11`; a single happy row `5` is interior-only.
- A nullable `[Required]` field needs the missing/null case plus the valid case; a payload with the field present in every row is positive-only.

When no richer contract is visible, fall back to generic sentinel signals:

- Numeric: `0`, `1`, `-1`, `int.MaxValue`, `int.MinValue` (scale to the numeric type).
- String: `""` (empty), single-character literal, `null`.
- Collection: `new T[] {}`, `new T[] { x }`, `null`.

**Why low-confidence:** the test may be intentionally scoped to a narrow equivalence class. Always report `Boundary evidence` as `contract-derived`, `partial`, `sentinel-only`, or `unknown` so the author can dismiss a narrow-by-design case with evidence.

**Rewrite:** add boundary rows or separate `[Fact]` tests for each contract edge the function is specified to handle.

---

### `dotnet.LC-8` — `CultureInfo.CurrentCulture` / `CurrentUICulture` read in a test body without explicit set

**Applies to:** `unit, integration`

**Detection:** `CultureInfo\.(CurrentCulture|CurrentUICulture)` read anywhere in the test body without a preceding `CultureInfo\.(CurrentCulture|CurrentUICulture)\s*=\s*new CultureInfo\(` assignment or a `using` block that scopes the culture.

**Why low-confidence:** the test will pass on the author's machine and fail on a CI agent whose locale differs. Parsing, formatting, and collation depend on culture; assertions on parsed dates / formatted numbers are the most common failure mode.

**Rewrite:** set the culture explicitly per test (`CultureInfo.CurrentCulture = CultureInfo.InvariantCulture`) in the Arrange block, restored in a `Dispose` or `finally`, or inject an `IFormatProvider` into the SUT and use `CultureInfo.InvariantCulture` in the test.

---

### `dotnet.LC-9` — Platform-specific path / line-ending / separator literal in a test body

**Applies to:** `unit, integration`

**Detection:** any of the following in a test body without a platform-abstracting call:

- Literal `\\` (Windows path separator) or `"/"` (Unix path separator) concatenated into a path.
- `Environment.NewLine` in an assertion expected value.
- `\r\n` or `\n` literal in a string-equals assertion.
- Hardcoded `C:\\`, `/tmp/`, `/home/`, `/var/` in a path.

**Why low-confidence:** the test passes on the author's platform and fails on the other. `Environment.NewLine` evaluates to `\r\n` on Windows and `\n` on Linux — an assertion comparing rendered output with a literal `\n` fails on the other platform.

**Rewrite:** use `Path.Combine(...)` or `Path.DirectorySeparatorChar` for paths; use `"\n"` (or a regex `\r?\n`) for line endings; parameterize over platforms if the behavior is platform-sensitive.

---

### `dotnet.LC-7` — Positive-only test with no sibling negative test

**Applies to:** `unit, integration` — refines core `LC-12`.

**Detection:** a `[Fact]` whose name ends in `_Returns_*`, `_Succeeds`, `_Persists_*`, `_Creates_*`, `_Updates_*`, `_Completes_*`, `_Is_*` on a method that has at least one `throw new *Exception` statement, a `Result.Fail` / `Error.*` return, or `[Required]` / `[Range]` / custom validator on its input type. The method must be detected via the test's SUT construction (`var sut = new Foo(...); sut.Bar(...)`). Flag when no sibling test method on the same class targets the same method with a name matching `_Throws_*`, `_Fails_*`, `_Rejects_*`, `_Returns_Error_*`, or `_Validates_*`.

**Why low-confidence:** the test file may organize negative cases into a separate file (e.g. `OrderServiceValidationTests.cs` alongside `OrderServiceTests.cs`). Before flagging, grep the whole test project for any test whose body constructs the same SUT and targets the same method with an expected-exception pattern (`Assert.Throws<...>` / `.Should().Throw<...>()`). Only flag if zero sibling negative tests exist across the project.

**Rewrite:** add a sibling test for each distinct sad path (`POS-5` positive signal in the core rubric).

---

## Framework-specific positive signals (`dotnet.POS-*`)

### `dotnet.POS-1` — `[Theory]` with `TheoryData<...>` or `MemberData` and *varied* expected values

**Applies to:** `unit, integration`

**Why positive:** the parameterization covers equivalence classes with meaningful variation, not just repetition.

---

### `dotnet.POS-2` — `FluentAssertions` `.BeEquivalentTo(expected)` against a spec-derived expected object

**Applies to:** `unit, integration`

**Why positive:** asserts the full shape of the return value, not just a single field. When the expected object is built from a fixture or spec, the test is specification.

---

### `dotnet.POS-3` — xUnit `IClassFixture` / NUnit `[OneTimeSetUp]` used for expensive shared setup *without* mutable state

**Applies to:** `unit, integration` — especially valuable under the integration rubric, where expensive fixtures like `WebApplicationFactory<T>` are the norm and shared immutable setup is the correct way to amortize them.

**Why positive:** shared setup is unavoidable when the fixture is genuinely expensive (e.g., DI container, data protection provider). Without mutable state, it doesn't cause test interdependence.

---

### `dotnet.POS-4` — Assertions on structured log properties by key, not rendered string

**Applies to:** `unit, integration`

**Why positive:** treats the log entry as a published contract (audit event, metric) with a stable schema. Pattern typically uses a capture-helper like `TestLogger<T>` rather than `Mock<ILogger<T>>`.

---

### `dotnet.POS-5` — Capture helper (test double) instead of `Mock<ILogger<T>>`

**Applies to:** `unit, integration`

**Detection:** a `TestLogger<T>`, `CapturingLogger`, `FakeLogger` / `FakeLogger<T>` (namespace `Microsoft.Extensions.Logging.Testing`, package `Microsoft.Extensions.Diagnostics.Testing`), or similar capture-style helper in Arrange. Assertions typically enumerate `FakeLogCollector.GetSnapshot()` or iterate `FakeLogRecord` entries by key rather than matching on the rendered string.

**Why positive:** a capture helper is a fake (real `ILogger<T>` behavior with recording), not a mock. Assertions on the captured entries test observable behavior, not interaction.

---

### `dotnet.POS-6` — Use of `TimeProvider` (.NET 8+) with a fixed instant

**Applies to:** `unit, integration`

**Detection:** `using Microsoft.Extensions.Time.Testing;` plus `new FakeTimeProvider(...)` (optionally seeded via `new FakeTimeProvider(new DateTimeOffset(...))` or advanced via `.Advance(TimeSpan.FromMinutes(...))`), or an injected `TimeProvider` with a pinned `DateTimeOffset`. The `Microsoft.Extensions.TimeProvider.Testing` package ships `FakeTimeProvider` under the `Microsoft.Extensions.Time.Testing` namespace.

**Why positive:** the idiomatic .NET 8+ way to make time-sensitive code deterministic. `FakeTimeProvider` extends `System.TimeProvider`, defaults to midnight 2000-01-01 UTC, and advances only when the test explicitly calls `Advance`. Not an `HC-11` smell.

---

### `dotnet.POS-7` — Property-based test harness (FsCheck / CsCheck / Hedgehog)

**Applies to:** `unit, integration` — refines core `POS-9`.

**Detection:** any of:
- `using FsCheck;` / `using FsCheck.Xunit;` plus a `[Property]` attribute on a test method.
- `using CsCheck;` plus a `Gen.*` generator expression feeding `.Sample(...)`.
- `using Hedgehog;` plus `Property.ForAll(...)`.
- A `[Theory]` whose data source is a seeded RNG yielding values across a declared equivalence class.

**Why positive:** a property-based test expresses a domain invariant over a generated input space instead of pinning a finite set of examples. Correct implementations pass for the whole domain; characterization tests written from observed output cannot be phrased this way. Reward under both unit and integration rubrics.

---

## Carve-outs

Patterns that look like core smells but are idiomatic in .NET and must not be flagged:

- **Do not flag `HC-5`** (mock-return-then-mock-called-with) when the mock is `Mock<HttpMessageHandler>` and the verified call is `.Protected().Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())` (with `using Moq.Protected;`). This is the Microsoft-documented pattern for stubbing `HttpClient` behavior in .NET (see the ASP.NET Core integration-tests docs and the OData client unit-test docs); `HttpMessageHandler.SendAsync` is the process boundary the protected-setup form reaches through. The matching `Verify` also uses `ItExpr.IsAny<...>`.

- **Do not flag `HC-11`** (hardcoded clock values) when the clock is injected via `TimeProvider` (including `FakeTimeProvider` — namespace `Microsoft.Extensions.Time.Testing`, package `Microsoft.Extensions.TimeProvider.Testing`) with a fixed `DateTimeOffset`. That is the idiomatic way to test time-sensitive logic in modern .NET.

- **Do not flag `LC-1`** (mocking same-layer code) when the mocked type is an interface owned by the tested module *and* the project has a documented "test via seams" convention (e.g. a `CLAUDE.md` or `README.md` stating that interfaces exist specifically for testability). Ask before flagging if ambiguous.

- **Do not flag `LC-7`** (excessive setup) when the setup is constructing an `IHost`, `WebApplicationFactory<T>`, `HostBuilder`, `TestServer`, an `IPlaywright` / `IBrowser` / `IBrowserContext` / `IPage`, an `IWebDriver`, a Testcontainers-based stack fixture, or a collection-level fixture that brings up a full backend for an E2E run. Under the new dispatch model (see [SKILL.md § 0b (Rubric selection)](../../../SKILL.md)), these are **routing signals into the integration or E2E rubric** — tests using them should be audited under that rubric where heavy setup is expected, not the unit rubric at all. This carve-out stays in force as a **safety net for cases where the dispatch is uncertain**: if a test somehow reaches the unit rubric with one of these setups, suppress the `LC-7` finding rather than flagging a test that was misrouted.

- **Do not flag `HC-10`** (snapshot tests pinning unspecified output) when the snapshot target is a JSON response whose schema is published via an OpenAPI document in the repo, a gRPC proto, or an equivalent contract document. Reference the contract in the carve-out decision.

- **Do not flag `dotnet.HC-2`** (logger content as contract) when the log call is via a source-generated `[LoggerMessage]` method whose name is namespaced as an audit event (e.g. `LogAuditUserDeleted`) — the event *is* the contract.

---

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
