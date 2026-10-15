# Java Test-Code Lane

Load for Java test classes, fixtures, or helpers, or a `tdd-policy` handoff;
use the project's framework and build tool and add no dependency.

Sources: https://docs.junit.org/current/writing-tests/parallel-execution.html;
https://docs.junit.org/6.1.1/api/org.junit.jupiter.api/org/junit/jupiter/api/util/DefaultLocale.html;
https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/caching.html;
https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/.

## Shared test support

- Search the test source set for builders, base classes, and JUnit extensions
  before defining one. Reusable behavior goes in a JUnit extension (`@ExtendWith`,
  `@RegisterExtension`) or builder, not deep base classes. Extension state
  lives in `ExtensionContext.Store`; a closeable resource in the root store is
  a run-wide singleton.
- Cross-module support goes in a `testFixtures` source set (Gradle
  `java-test-fixtures`) or a test-support module used at test scope, not
  `src/main`; a Maven test-jar drops transitive dependencies.

## Setup lifetime

- `@BeforeAll` only for immutable or safely resettable infrastructure; it is
  `static` unless the class uses `@TestInstance(Lifecycle.PER_CLASS)`. Mutable
  state is rebuilt in `@BeforeEach`.
- Under `PER_CLASS` instance fields, and `static` mutable fields always,
  persist across tests: shared mutable state (core `SD-C-4`).
- Expensive containers are static singletons in a shared base class, started
  once and never stopped by the framework, so the container reaper cleans up;
  keep their data resettable per test. A non-static `@Container` field
  restarts per test.
- Test-managed transactions roll back only the test thread's connection;
  calls through a real server port or async work commit, so pick one reset
  strategy (rollback, truncation, or schema per fork).
- Spring caches test contexts by configuration: a distinct set of
  `@MockitoBean`/`@MockBean` overrides, profiles, or properties builds a new
  context and `@DirtiesContext` discards one, so keep a few shared bases.

## Time, randomness, and ambient environment

- Inject `java.time.Clock` (`Clock.fixed`, `Clock.offset`) instead of calling
  `Instant.now()` and seed `Random` (core `SD-B-5`); wait on an observable
  condition with a bound (a latch, or Awaitility if used), never `Thread.sleep`.
- JUnit 6.1 ships `@DefaultLocale` and `@DefaultTimeZone` (package
  `org.junit.jupiter.api.util`), which set and restore the JVM default per
  class or method; older JUnit has them in JUnit Pioneer.
- `-Duser.language`, `-Duser.timezone`, and `-Dfile.encoding` set in build
  tool test JVM args are environment-level; assert `Locale.getDefault()` and
  `TimeZone.getDefault()` so an ignored setting fails loudly.

## Isolation and parallel runs

- JUnit parallelism is off by default; it needs
  `junit.jupiter.execution.parallel.enabled=true` plus a default mode
  (`mode.default`, `mode.classes.default`) or per-element `@Execution`.
- Tests touching a shared resource declare it with `@ResourceLock`
  (`READ`/`READ_WRITE`); `@Isolated` runs a class with nothing alongside it.
  Tests that change JVM defaults (locale, properties) need the lock.
- Build-tool forking (Surefire `forkCount`, Gradle `maxParallelForks`) is a
  separate axis from JUnit threads and multiplies static singletons; shared
  ports or databases need per-fork unique resources. A lane with random method
  and class orderers surfaces order dependence.

## Lanes and durations

- Mark lanes with `@Tag("integration")` (or a meta-annotation) selected by the
  build tool's tag include/exclude (Surefire `groups`, Gradle `includeTags`);
  separate integration source sets or Failsafe are the alternative.
- Read per-test durations from the report XML `time` attribute (Surefire or
  Gradle test results) or a Gradle build scan.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
