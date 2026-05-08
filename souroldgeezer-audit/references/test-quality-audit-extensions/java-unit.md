# Java Unit Addon

Loaded after `java-core.md` when `SKILL.md` selects the unit/component rubric.

## Detection Signals

- JUnit `@Test`, `@ParameterizedTest`, `@Nested`, or TestNG `@Test` methods
  directly construct or call the SUT.
- Dependencies are values, fakes, stubs, Mockito doubles, temp resources, or
  generated cases.
- No browser automation, launched application context, real service process,
  database transaction, queue, or network boundary is exercised.

## Framework-Specific High-Confidence Smells

### `java.HC-5` - Mockito replaces the class under test or same-package owned policy

Applies to: unit

Detection: `mock(...)`, `spy(...)`, `@Spy`, or `mockStatic(...)` targets the
class named by the test, a same-package concrete collaborator, or an in-repo
utility that owns the behavior under test.

Rewrite: instantiate the SUT and inject a process-boundary fake or stub.

### `java.HC-6` - expected value mirrors the same stream/mapper pipeline

Applies to: unit

Detection: expected value is computed with the same `stream().map/filter/reduce`,
mapper, serializer, or parser pipeline visible in the SUT.

Rewrite: derive expected values from a requirement example, invariant, or
explicit table.

### `java.HC-7` - sleep-based unit test

Applies to: unit

Detection: `Thread.sleep`, `TimeUnit.sleep`, or arbitrary timeout waits appear
before assertions in an in-process unit test.

Rewrite: inject a fake clock, await a future/result, or expose a deterministic
completion signal.

### `java.HC-8` - assertion hides behind `assertDoesNotThrow`

Applies to: unit

Detection: `assertDoesNotThrow`, AssertJ `doesNotThrowAnyException`, or TestNG
try/catch success logic is the only oracle for value-bearing behavior.

Rewrite: assert the returned value, state change, emitted event, or typed error
path.

## Framework-Specific Low-Confidence Smells

### `java.LC-4` - data provider hides inputs and expected values

Applies to: unit

Detection: JUnit `@MethodSource` / TestNG `@DataProvider` returns opaque arrays
or objects, while the test name/body does not identify the requirement or
expected value per row.

Rewrite: name the cases through display names, arguments, or explicit expected
records visible near the test.

### `java.LC-5` - reflection reaches private helpers

Applies to: unit

Detection: `setAccessible(true)`, reflection method lookup, or `ReflectionTestUtils`
is used to invoke or mutate private implementation details.

Rewrite: test through the public/package contract, or extract a real boundary
when the helper owns separate policy.

## Framework-Specific Positive Signals

### `java.POS-4` - readable parameterized case names

Applies to: unit

Detection: JUnit display names, `@ParameterizedTest(name = ...)`, named
`Arguments`, or TestNG data-provider rows identify the partition being proven.

### `java.POS-5` - controlled Java resource fixture

Applies to: unit

Detection: `@TempDir`, fake clock, fake repository, capture sink, or
per-test-owned in-memory resource is reset per test and assertions target a
published result.

### `java.POS-6` - deterministic async unit assertion

Applies to: unit

Detection: `CompletableFuture`, callback, channel, or executor work is awaited
through a bounded deterministic signal before the assertion.

## Carve-Outs

- Do not flag package-private access when the test is in the same package and
  still asserts the package's public behavior.
- Do not flag one `verify(...)` call when the collaborator is an outbound port
  and the interaction is the published contract being tested.
- Do not flag `assertThrows` or TestNG `expectedExceptions` when the test also
  constrains the error type/message/state enough to distinguish the contract.
