# Extension: .NET — unit + integration smells

`Applies to: unit, integration` framework smells — defects needing in-process
access to the SUT (Moq verification, logger mocks, reflection construction,
`TimeProvider` injection, `[Theory]` input partitions). Loaded on the unit and
integration paths only, never on E2E. Three-rubric smells stay in
[`core.md`](core.md).

## Framework-specific high-confidence smells (`dotnet.HC-*`)

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

## Framework-specific positive signals (`dotnet.POS-*`)

### `dotnet.POS-1` — `[Theory]` with `TheoryData<...>` or `MemberData` and *varied* expected values

**Applies to:** `unit, integration`

**Why positive:** the parameterization covers equivalence classes with meaningful variation, not just repetition.

---

### `dotnet.POS-2` — `FluentAssertions` `.BeEquivalentTo(expected)` against a spec-derived expected object

**Applies to:** `unit, integration`

**Why positive:** asserts the full shape of the return value, not just a single field. When the expected object is built from a fixture or spec, the test is specification.

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

