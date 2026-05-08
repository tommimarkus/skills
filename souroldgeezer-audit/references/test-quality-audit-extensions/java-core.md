# Java Core Extension

Loaded when Java test signals are present. This file owns Java detection,
rubric routing, Mockito/TestNG/JUnit test-double semantics, rubric-neutral
smells, carve-outs, SUT surface enumeration, determinism verification, and the
PIT mutation-tool declaration. Load the matching rubric addon after `SKILL.md`
selects the rubric.

Rubric-exclusive content lives in:

- [`java-unit.md`](java-unit.md) - JUnit/TestNG unit smells and positive signals.
- [`java-integration.md`](java-integration.md) - Java integration, container,
  HTTP, database, migration, and auth matrix smells.
- [`java-e2e.md`](java-e2e.md) - Playwright Java and Selenium E2E smells.

## Sources

Use these sources for runner and tool facts:

- JUnit User Guide: https://docs.junit.org/6.0.3/overview.html
- Maven Surefire JUnit Platform docs:
  https://maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html
- Gradle Java testing docs:
  https://docs.gradle.org/current/userguide/java_testing.html
- TestNG docs: https://testng.org/
- Mockito javadoc:
  https://site.mockito.org/javadoc/current/org/mockito/Mockito.html
- Mockito static mock javadoc:
  https://www.javadoc.io/static/org.mockito/mockito-core/5.12.0/org/mockito/MockedStatic.html
- Testcontainers for Java JUnit 5 docs:
  https://java.testcontainers.org/test_framework_integration/junit_5/
- PIT Maven quickstart: https://pitest.org/quickstart/maven/

Cite core quality rubrics for test-quality judgments.

## Detection Signals

Load this extension when the audit target contains any of:

- Java build/project files: `pom.xml`, `mvnw`, `.mvn/`, `build.gradle`,
  `build.gradle.kts`, `settings.gradle*`, `gradlew`, or `src/test/java/**`.
- Test files or imports: `.java` files with `org.junit`, `org.testng`,
  `org.mockito`, `org.assertj`, `org.hamcrest`, `org.awaitility`,
  `org.testcontainers`, `com.microsoft.playwright`, or `org.openqa.selenium`.
- Build dependencies or plugins: JUnit Jupiter/Vintage/Platform, TestNG,
  Mockito, AssertJ, Hamcrest, Awaitility, Testcontainers, WireMock, MockWebServer,
  REST Assured, Selenium, Playwright, Maven Surefire/Failsafe, Gradle `Test`
  tasks, or PIT.
- Runner commands: `mvn test`, `mvn verify`, `mvn failsafe:integration-test`,
  `./gradlew test`, `./gradlew check`, `./gradlew integrationTest`, or
  `testng`.

Detection glob shortcuts: `**/pom.xml`, `**/build.gradle*`,
`**/src/test/java/**/*.java`, `**/*Test.java`, `**/*Tests.java`,
`**/*IT.java`, `**/*ITCase.java`, `**/*E2E*.java`.

## Test Type Detection Signals

Gradle documents JVM tests around the `Test` task and source sets; Maven
Surefire documents `src/test/java` as the default test source directory for
JUnit Platform. Use those facts for runner detection only. Classify each test
by boundary evidence.

### E2E rubric signals

- Playwright Java: `com.microsoft.playwright.*`,
  `com.microsoft.playwright.junit.UsePlaywright`, `Page`, `BrowserContext`,
  `assertThat(page)`, navigation, clicks, fills, or browser fixtures.
- Selenium: `org.openqa.selenium.*`, `WebDriver`, `WebElement`, `By.cssSelector`,
  `By.xpath`, `WebDriverWait`, or browser driver setup.
- Project-level names/tags: `e2e`, `end-to-end`, `browser`, `ui`, `journey`,
  `a11y`, `perf`, or `security`.
- User-session behavior: real browser/app navigation, login/logout flows,
  rendered page state, mobile/web gestures, or assertions on browser-visible
  outcomes.

Classify E2E sub-lanes:

- `@Tag("a11y")`, accessibility helper imports, or axe-style assertions -> `A`.
- `@Tag("perf")`, timing metrics, Web Vitals, or browser performance budgets
  -> `P`.
- `@Tag("security")`, auth/session/cookie/CSP/CORS/tampered-token assertions
  -> `S`.
- Otherwise -> `F`.

### Integration rubric signals

- Project-level names: `*IT`, `*ITCase`, `integrationTest` source set, Maven
  Failsafe configuration, or Gradle custom integration-test source sets/tasks.
- Real adjacent dependencies: Testcontainers `@Testcontainers` / `@Container`,
  JDBC/DataSource connections, database migrations, message broker clients,
  file-system persistence under a real temp directory, or HTTP servers/clients.
- In-process or slice harnesses: app context bootstrapping, test HTTP clients,
  servlet/filter/controller harnesses, or local server ports.
- Out-of-process contracts: HTTP calls to localhost, deployed test
  environments, partner sandboxes, or contract endpoints.
- Service stubs as boundary fixtures: WireMock, MockWebServer, or similar
  protocol stubs used to assert outbound client behavior.

### Unit rubric signals

- JUnit or TestNG test methods directly construct a class/function with values,
  fakes, stubs, or Mockito doubles.
- No real browser, service process, HTTP boundary, database, queue, filesystem
  behavior, or launched application context is exercised.
- Parameterized/property-like cases exercise in-process behavior only.

### Mixed-file handling

Classify each test method independently. A single class may contain a direct
unit test, a Testcontainers integration test, and a Playwright E2E test. A test
belongs to exactly one rubric; report the selected rubric and E2E sub-lane per
test.

## Test Double Classification

Required reading for auditors: `../../docs/quality-reference/unit-testing.md`
section 7.1. Classify doubles by their role before applying interaction
pinning smells.

- **Mockito stub:** `mock(...)`, `@Mock`, or `spy(...)` with stubbing such as
  `when(...).thenReturn(...)` and no `verify(...)` or interaction assertion
  against that double.
- **Mockito mock:** any `verify(...)`, `InOrder.verify(...)`,
  `verifyNoMoreInteractions(...)`, `times(...)`, `never()`, `atLeast(...)`, or
  argument-captor assertion against the double.
- **Static mock:** `mockStatic(...)` or `MockedStatic<T>`. Mockito documents
  static mocks as scoped resources that should be released; unscoped static
  mocks are state-leak evidence.
- **TestNG data provider:** table driver, not a double. Judge the case rows and
  expected values the same way as JUnit parameterized tests.
- **Fakes:** in-memory repositories, fake clocks, capture sinks, temp
  directories, embedded protocol stubs, or handwritten interface
  implementations are fakes when assertions target observable results.

## Rubric-Neutral Smells

### `java.HC-1` - Mockito call-count verification pins implementation loops

Applies to: unit, integration

Detection: `verify(..., times(N))`, `atLeast(N)`, `atMost(N)`, or
`InOrder.verify(...)` is the primary assertion, and `N` tracks the current loop,
batch, retry, or collection size rather than a published protocol.

Rewrite: assert the return value, persisted state, emitted message, or protocol
result. Keep call-count verification only when the count is the contract.

### `java.HC-2` - blanket `verifyNoMoreInteractions` overspecifies owned collaborators

Applies to: unit, integration

Detection: `verifyNoMoreInteractions(...)` or `only()` is used on an owned
collaborator in most tests or as a generic cleanup assertion.

Rewrite: verify only the observable interaction that forms a public contract,
or replace the mock with a fake and assert the published state.

### `java.HC-3` - static mock is unscoped or replaces owned policy

Applies to: unit, integration

Detection: `Mockito.mockStatic(...)` is not held in try-with-resources,
`close()` is not guaranteed, or the static mock replaces an in-repo utility
that owns policy rather than an external time/process boundary.

Rewrite: inject the boundary, use a fake clock or adapter, and scope static
mocks tightly when they are unavoidable.

### `java.HC-4` - asynchronous behavior is not observed before assertion

Applies to: unit, integration

Detection: test starts a `CompletableFuture`, `ExecutorService`, virtual thread,
callback, or scheduled task and asserts before awaiting completion, joining the
future, consuming the callback, or observing a deterministic completion signal.

Rewrite: await the future/result, assert the emitted state, or expose a
completion hook in the SUT boundary.

### `java.LC-1` - parameterized/data-provider rows miss contract boundaries

Applies to: unit, integration

Detection: JUnit `@ParameterizedTest`, `@CsvSource`, `@ValueSource`,
`@MethodSource`, or TestNG `@DataProvider` covers only happy/interior cases
while visible contracts expose min/max, null/missing, enum/state, validation,
auth, duplicate, or error partitions.

Rewrite: add named rows for the actual equivalence classes and assert the
case-specific expected result.

### `java.LC-2` - broad presence/truthiness assertion on complex behavior

Applies to: unit, integration

Detection: assertion is only `assertNotNull`, `assertTrue`, `isNotNull`,
`isTrue`, `not(empty())`, or type checking for a value-bearing result.

Rewrite: assert the spec-derived values, invariant, state transition, or
published side effect.

### `java.LC-3` - disabled or ignored test hides required coverage

Applies to: unit, integration

Detection: `@Disabled`, TestNG `enabled = false`, excluded group, or runner
filter disables a test with no issue link, owner, or replacement coverage.

Rewrite: re-enable, document the opt-in command and owner, or replace with a
deterministic narrower test.

### `java.POS-1` - contract-derived parameterized or data-provider cases

Applies to: unit, integration

Detection: JUnit parameterized rows or TestNG data-provider rows name the
boundary/equivalence class and use case-specific expected values.

### `java.POS-2` - fake over interaction mock

Applies to: unit, integration

Detection: fake repository, fake clock, embedded protocol stub, capture sink,
or temp resource lets the test assert an observable result.

### `java.POS-3` - typed exception or error-path assertion

Applies to: unit, integration

Detection: `assertThrows`, AssertJ thrown-by assertions, or TestNG expected
exception checks assert a named error path and enough message/state detail to
distinguish the contract.

## Carve-Outs

- Do not flag `@TempDir`, per-test temporary folders, or in-memory databases as
  integration merely because files or JDBC APIs are used; classify by the SUT
  boundary being exercised.
- Do not flag Mockito verification when the verified call is the published
  protocol, such as an outbound event, audit record, or idempotent retry budget
  required by the contract.
- Do not flag package-private tests in the same package by themselves. Flag
  only when the test proves a private helper instead of public behavior.
- Do not flag Testcontainers static containers by themselves. The smell appears
  when shared mutable state is not reset or when parallel execution is enabled
  despite an unsafe shared fixture.

## SUT Surface Enumeration

Java gap detection is approximate and deep-mode only.

- **SUT identification:** inspect Maven modules, Gradle projects/source sets,
  `src/main/java`, package names, and imports from tests.
- **`Gap-API`:** public classes, exported module packages, public methods on
  application services, public records/enums, and CLI entrypoints.
- **`Gap-Route`:** controller/router/resource annotations, servlet/filter
  mappings, route tables, or framework adapters when API review is not already
  delegated.
- **`Gap-CLI`:** `main(String[] args)`, command classes, parser subcommands,
  exit-code contracts, stdout/stderr contracts, and generated launchers.
- **`Gap-Error`:** checked exceptions, runtime exception families, validation
  failures, typed error responses, and negative partitions.
- **`Gap-Validate`:** Jakarta/Bean Validation annotations, custom validators,
  parser constraints, enum/state guards, and branch predicates.
- **`Gap-Migration`:** migration files, schema changelogs, and upgrade/downgrade
  scripts exercised by Java integration tests.

Identifier-only tests, import-only tests, status-only HTTP assertions,
compile-only references, and happy-path-only parameter rows are
`referenced-weak` for error, auth, migration, state-change, and invalid-input
gaps. Static-only gaps stay probable until mutation, coverage, or manual review
confirms them.

## Determinism Verification

Cheap rerun command for non-E2E scopes:

```bash
mvn -q test
mvn -q test
```

or for Gradle projects:

```bash
./gradlew test
./gradlew test
```

Use only when the suite is small enough to finish under 60 seconds per run or
the user opts in. Compare failing test classes/methods between runs. If the
project separates integration tests under Maven Failsafe or a Gradle custom
source set, rerun the project-specific integration command instead.

## Mutation Tool

### Tool name and link

PIT: https://pitest.org/

### Install instructions

For Maven, add `org.pitest:pitest-maven` to the build plugins or invoke the
plugin directly from the command line. For Gradle, use the project's configured
PIT Gradle plugin if present.

### Detection command

```bash
grep -R "pitest\\|org.pitest" pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts 2>/dev/null
```

### Run command

Maven:

```bash
mvn test-compile org.pitest:pitest-maven:mutationCoverage
```

Gradle when the PIT plugin is configured:

```bash
./gradlew pitest
```

### Known SUT limitations

- Cross-module tests need explicit PIT configuration; otherwise a module may be
  mutated against only its own tests and understate coverage.
- Generated code, annotation-processor output, framework proxies, and bytecode
  enhancement can produce poor mutant signal; mutate the handwritten module
  that owns policy when possible.
- E2E/browser suites are usually too expensive for mutation; mutate Java policy
  modules behind the browser/API boundary instead.
- Equivalent mutants and timeout-sensitive concurrency code require manual
  interpretation; surviving mutants are investigation evidence, not automatic
  findings.

### Output parser notes

Read `target/pit-reports/**/mutations.xml` for Maven runs when XML is enabled
by the project; otherwise report the HTML report directory and summarize
survived/no-coverage mutants by class and line. For Gradle plugin runs, prefer
the configured XML output path when present.
