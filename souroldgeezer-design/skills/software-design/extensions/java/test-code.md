# Java Test-Code Lane

Load when writing or restructuring Java test classes, fixtures, or helpers, or
on a `tdd-policy` handoff. Use the project's existing framework and build
tool; add no dependency.

Sources: https://docs.junit.org/current/writing-tests/parallel-execution.html;
https://docs.junit.org/6.1.1/api/org.junit.jupiter.api/org/junit/jupiter/api/util/DefaultLocale.html;
https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/caching.html;
https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/.

## Shared test support

- Search the test source set for existing builders, base classes, and JUnit
  extensions before defining one.
- Reusable behavior goes in a JUnit extension (`@ExtendWith`,
  `@RegisterExtension`) or builder; prefer composition over deep base classes.
- Support shared across modules goes in a `testFixtures` source set (Gradle
  `java-test-fixtures`) or Maven test-jar, not `src/main`; use `@TempDir` for
  files.

## Setup lifetime

- `@BeforeAll` only for immutable or safely resettable infrastructure; it is
  `static` unless the class uses `@TestInstance(Lifecycle.PER_CLASS)`. Mutable
  state is rebuilt in `@BeforeEach`.
- Under `PER_CLASS`, instance fields persist across tests: shared mutable
  state (core `SD-C-4`).
- Expensive containers follow the singleton pattern: a static container in a
  shared base class, started once and reused. The framework never stops it
  explicitly, so cleanup relies on the container reaper; keep its data
  resettable per test.
- Spring test contexts are cached by configuration; a distinct set of
  `@MockitoBean`/`@MockBean` overrides, profiles, or properties builds a new
  context. Keep a few shared base configurations and add overrides sparingly.

## Time, randomness, and ambient environment

- Inject `java.time.Clock` (`Clock.fixed`, `Clock.offset`) into the unit
  instead of calling `Instant.now()` there; seed `Random` explicitly (core
  `SD-B-5`).
- JUnit 6.1 ships `@DefaultLocale` and `@DefaultTimeZone` (package
  `org.junit.jupiter.api.util`), which set and restore the JVM default per
  class or method; older JUnit has them in JUnit Pioneer.
- `-Duser.language`, `-Duser.timezone`, and `-Dfile.encoding` set in build
  tool test JVM args are environment-level; assert `Locale.getDefault()` and
  `TimeZone.getDefault()` so an ignored setting fails loudly.
- Replace `Thread.sleep` with a bounded wait on an observable condition (a
  latch, or an Awaitility-style wait if already used).

## Isolation and parallel runs

- JUnit parallelism is off by default; it needs
  `junit.jupiter.execution.parallel.enabled=true` plus a default mode
  (`mode.default`, `mode.classes.default`) or per-element `@Execution`.
- Tests touching a shared resource declare it with `@ResourceLock`
  (`READ`/`READ_WRITE`); `@Isolated` runs a class with nothing alongside it.
  Tests that change JVM defaults (locale, properties) need the lock.
- Build-tool forking (Surefire `forkCount`, Gradle `maxParallelForks`) is a
  separate axis from JUnit threads; shared ports or databases need per-fork
  unique resources.

## Lanes and durations

- Mark lanes with `@Tag("integration")` (or a meta-annotation) and select them
  through the build tool's tag include/exclude (Surefire `groups`/
  `excludedGroups`, Gradle `useJUnitPlatform { includeTags ... }`); separate
  integration source sets or Failsafe are the alternative.
- Read per-test durations from the report XML `time` attribute (Surefire or
  Gradle test results) or a Gradle build scan.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
