# Python Unit Addon

Loaded after `python-core.md` when `SKILL.md` step 0b selects the unit or
component rubric.

## Detection Signals

- `pytest` or `unittest` tests that call functions/classes directly.
- Fixtures provide values, fakes, temporary paths, fake clocks, or stubs.
- No browser automation, no real web server/client, no database transaction
  fixture, and no containerized adjacent dependency.

## Framework-Specific High-Confidence Smells

### `python.HC-4` — expected value computed by the same comprehension

Applies to: unit

Detection: expected value duplicates the SUT algorithm with a list/dict/set
comprehension or generator expression, then compares the SUT output to it.

Rewrite: derive expected values from a requirement example, domain invariant,
fixture, or property-based invariant.

### `python.HC-5` — patching the function under test

Applies to: unit

Detection: `patch("package.module.function_under_test")` or
`monkeypatch.setattr(module, "function_under_test", ...)` replaces the callable
that the test claims to verify.

Rewrite: patch only process boundaries or collaborators outside the behavior
under test.

### `python.HC-6` — async test not awaiting the behavior

Applies to: unit

Detection: async SUT returns coroutine/task but the test asserts on the
coroutine object, uses `asyncio.create_task` without awaiting completion, or
lets pytest pass because no awaited assertion observes the result.

Rewrite: use `pytest.mark.asyncio`, `IsolatedAsyncioTestCase`, or the project's
async test runner and assert the awaited result.

## Framework-Specific Low-Confidence Smells

### `python.LC-3` — fixture parameterization hides expected values

Applies to: unit

Detection: parametrized fixture returns both input and expected output, while
the test name/body does not explain the requirement.

Rewrite: keep cases visible in `pytest.mark.parametrize` or give fixture cases
ids that state the requirement.

### `python.LC-4` — broad `assert isinstance` only

Applies to: unit

Detection: assertions only check type, truthiness, or `is not None` for a
non-trivial result.

Rewrite: assert the observable value, invariant, or published side effect.

## Framework-Specific Positive Signals

### `python.POS-4` — readable parametrization ids

Applies to: unit

Detection: `pytest.mark.parametrize(..., ids=[...])` names the requirement or
boundary for each case.

### `python.POS-5` — fake over mock

Applies to: unit

Detection: test uses a working fake, temporary path, fake clock, in-memory
repository, or capture sink instead of interaction assertions on mocks.

## Carve-Outs

- Do not flag `unittest.TestCase.setUp` as excessive setup when it only creates
  immutable values or per-test fakes used by multiple tests.
- Do not flag `monkeypatch` of `Path.home`, `time`, environment variables, or
  HTTP clients when that boundary is the documented dependency of the SUT and
  assertions target the SUT's observable result.
