# Extension: .NET — core

Shared core for the .NET test-quality-audit extension. This file is loaded **whenever a .NET project is detected in the audit target**, before step 0b (rubric selection). It owns only what all three rubrics need: detection signals, test-type dispatch, test-double classification, genuinely rubric-neutral smells (`Applies to: unit, integration, e2e`), and carve-outs. Deep-mode procedures (SUT surface enumeration, determinism verification, and the Stryker.NET mutation tool declaration) live in [`deep.md`](deep.md).

Rubric-scoped content lives in the addons:

- [`unit-integration.md`](unit-integration.md) — `Applies to: unit, integration` smells that need in-process access to the SUT (Moq verification, logger mocks, reflection construction, `TimeProvider` injection, `[Theory]` input partitions). Loaded on the unit and integration paths only.
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

Required reading for auditors: [unit-testing.md § 7.1](../../../../../docs/quality-reference/unit-testing.md) — the Fowler taxonomy (Dummy / Stub / Spy / Mock / Fake) that core smells like `HC-5` and `HC-6` are scoped to.

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

These apply under **all three** rubrics — each is a defect a browser-driven spec can commit too. Unit+integration smells live in [`unit-integration.md`](unit-integration.md), unit-only in [`unit.md`](unit.md), integration-only in [`integration.md`](integration.md).

### `dotnet.HC-7` — `DateTime.Now` / `DateTime.Today` / `DateTimeOffset.Now` in a test body

**Applies to:** `unit, integration, e2e`

**Detection:** any test method body containing `DateTime\.(Now|Today|UtcNow)` or `DateTimeOffset\.(Now|UtcNow)` as a direct call (not through a `TimeProvider` abstraction). More specific than core `HC-11` — `dotnet.HC-7` covers the .NET idiom.

**Smell:** the test reads the real clock. Tests that use the real clock pass when the author runs them and fail at midnight or on daylight-saving transitions. Core `HC-11` covers the general case; this smell refines detection for .NET.

**Carve-out:** if the test calls `DateTime.UtcNow` solely to generate a unique identifier (e.g. `$"test-{DateTime.UtcNow.Ticks}"`) and does not use the value in an assertion, do not flag. The canonical unique-id generation pattern is benign.

**Rewrite:** under the unit and integration rubrics, inject `TimeProvider` (.NET 8+) and use `FakeTimeProvider` with a pinned instant — see `dotnet.POS-6` in [`unit-integration.md`](unit-integration.md). Under the E2E rubric the app runs out of process, so the test cannot inject a clock: pin time at the browser with Playwright .NET's `Page.Clock.InstallAsync(...)`, or drive the deployed app's own test-time configuration hook, rather than reading the runner's clock.

---

## Framework-specific low-confidence smells (`dotnet.LC-*`)

### `dotnet.LC-8` — `CultureInfo.CurrentCulture` / `CurrentUICulture` read in a test body without explicit set

**Applies to:** `unit, integration, e2e`

**Detection:** `CultureInfo\.(CurrentCulture|CurrentUICulture)` read anywhere in the test body without a preceding `CultureInfo\.(CurrentCulture|CurrentUICulture)\s*=\s*new CultureInfo\(` assignment or a `using` block that scopes the culture.

**Why low-confidence:** the test will pass on the author's machine and fail on a CI agent whose locale differs. Parsing, formatting, and collation depend on culture; assertions on parsed dates / formatted numbers are the most common failure mode.

**Rewrite:** set the culture explicitly per test (`CultureInfo.CurrentCulture = CultureInfo.InvariantCulture`) in the Arrange block, restored in a `Dispose` or `finally`, or inject an `IFormatProvider` into the SUT and use `CultureInfo.InvariantCulture` in the test.

---

### `dotnet.LC-9` — Platform-specific path / line-ending / separator literal in a test body

**Applies to:** `unit, integration, e2e`

**Detection:** any of the following in a test body without a platform-abstracting call:

- Literal `\\` (Windows path separator) or `"/"` (Unix path separator) concatenated into a path.
- `Environment.NewLine` in an assertion expected value.
- `\r\n` or `\n` literal in a string-equals assertion.
- Hardcoded `C:\\`, `/tmp/`, `/home/`, `/var/` in a path.

**Why low-confidence:** the test passes on the author's platform and fails on the other. `Environment.NewLine` evaluates to `\r\n` on Windows and `\n` on Linux — an assertion comparing rendered output with a literal `\n` fails on the other platform.

**Rewrite:** use `Path.Combine(...)` or `Path.DirectorySeparatorChar` for paths; use `"\n"` (or a regex `\r?\n`) for line endings; parameterize over platforms if the behavior is platform-sensitive.

---

### `dotnet.LC-7` — Positive-only test with no sibling negative test

**Applies to:** `unit, integration, e2e` — refines core `LC-12`.

**Detection:** a `[Fact]` whose name ends in `_Returns_*`, `_Succeeds`, `_Persists_*`, `_Creates_*`, `_Updates_*`, `_Completes_*`, `_Is_*` on a method that has at least one `throw new *Exception` statement, a `Result.Fail` / `Error.*` return, or `[Required]` / `[Range]` / custom validator on its input type. The method must be detected via the test's SUT construction (`var sut = new Foo(...); sut.Bar(...)`). Flag when no sibling test method on the same class targets the same method with a name matching `_Throws_*`, `_Fails_*`, `_Rejects_*`, `_Returns_Error_*`, or `_Validates_*`.

**Why low-confidence:** the test file may organize negative cases into a separate file (e.g. `OrderServiceValidationTests.cs` alongside `OrderServiceTests.cs`). Before flagging, grep the whole test project for any test whose body constructs the same SUT and targets the same method with an expected-exception pattern (`Assert.Throws<...>` / `.Should().Throw<...>()`). Only flag if zero sibling negative tests exist across the project.

**Rewrite:** add a sibling test for each distinct sad path (`POS-5` positive signal in the core rubric).

---

## Framework-specific positive signals (`dotnet.POS-*`)

### `dotnet.POS-3` — xUnit `IClassFixture` / NUnit `[OneTimeSetUp]` used for expensive shared setup *without* mutable state

**Applies to:** `unit, integration, e2e` — especially valuable under the integration rubric, where expensive fixtures like `WebApplicationFactory<T>` are the norm and shared immutable setup is the correct way to amortize them.

**Why positive:** shared setup is unavoidable when the fixture is genuinely expensive (e.g., DI container, data protection provider). Without mutable state, it doesn't cause test interdependence.

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
