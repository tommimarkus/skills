# Python Core Extension

Loaded when Python test signals are present. This file owns Python detection,
rubric routing, Python test-double semantics, shared smells, surface
enumeration, determinism verification, and mutation-tool declaration. Load the
matching rubric addon after `SKILL.md` step 0b.

## Detection Signals

- Python project manifests: `pyproject.toml`, `setup.cfg`, `setup.py`,
  `requirements*.txt`, `tox.ini`, `noxfile.py`, `Pipfile`, `poetry.lock`, or
  `uv.lock`.
- Test runner files: `pytest.ini`, `.coveragerc`, `conftest.py`, `tests/**/*.py`,
  `test_*.py`, `*_test.py`.
- Imports or dependencies: `pytest`, `unittest`, `unittest.mock`, `hypothesis`,
  `pytest_asyncio`, `pytest_django`, `pytest_playwright`, `playwright`,
  `selenium`, `requests`, `httpx`, `fastapi`, `starlette`, `flask`, `django`,
  `sqlalchemy`, `alembic`.

## Test Type Detection Signals

### E2E rubric signals

- Imports from `playwright.sync_api`, `playwright.async_api`, `selenium`,
  `pytest_playwright`, or browser fixture names such as `page`, `browser`,
  `context`, `driver`, `live_server` with browser navigation.
- Tests tagged or named `e2e`, `browser`, `ui`, `journey`, `a11y`, `perf`, or
  `security` and driving a real browser.

### Integration rubric signals

- Web test clients or ASGI/WSGI clients: `TestClient`, `AsyncClient`,
  `Client()`, `app.test_client()`, `django.test.Client`, `pytest-django`
  database fixtures, `live_server` without browser use.
- Real adjacent dependencies: SQLAlchemy engine/session against test database,
  Alembic migrations, Redis/Rabbit/Kafka clients, Testcontainers, filesystem
  integration via `tmp_path` where persistence semantics are under test.
- Network/API contract tests through `requests` or `httpx` against a deployed
  or locally launched service without browser automation.

### Unit rubric signals

- Direct function/class construction with no real I/O.
- `unittest.mock.Mock` / `patch` / `monkeypatch` used to replace process
  boundaries while assertions target return values or published side effects.
- Pure pytest/unittest tests with fixtures that provide values, fakes, or
  in-memory collaborators.

## Test Double Classification

- `Mock`, `MagicMock`, `AsyncMock`, `patch`, and `monkeypatch` are not smells by
  themselves. They become interaction-coupled when the test asserts
  `.assert_called*`, `.mock_calls`, or call counts on owned collaborators.
- `tmp_path`, `tmp_path_factory`, in-memory repositories, fake clocks, and
  capture fakes are fakes or controlled resources, not mocks.
- `monkeypatch.setenv` and `patch.dict(os.environ, ...)` are acceptable when the
  environment variable is a documented process boundary. They are smells when
  used to steer hidden module-global state.

## Rubric-Neutral Smells

### `python.HC-1` — import-time SUT execution

Applies to: unit, integration

Detection: test imports a module after monkeypatching globals or environment
only because the module performs workflow logic at import time.

Rewrite: move workflow logic behind an explicit function or application
factory; test the callable, not import side effects.

### `python.HC-2` — mock call history as the only assertion

Applies to: unit, integration

Detection: assertion is only `assert_called*`, `mock_calls`, `call_args`, or
`call_count` against an owned collaborator.

Rewrite: assert a return value, persisted state, emitted message, structured
audit event, or other published side effect.

### `python.HC-3` — monkeypatching internals instead of the public seam

Applies to: unit, integration

Detection: monkeypatch replaces a private function, private module variable,
or implementation helper in the same package as the SUT.

Rewrite: inject the process boundary or test through the public API.

### `python.LC-1` — fixture hides the behavior under test

Applies to: unit, integration

Detection: a fixture creates the SUT, act step, and expected value so the test
body only asserts a generic result.

Rewrite: keep fixture setup reusable, but keep the behavior-specific act and
expected value in the test.

### `python.LC-2` — broad autouse fixture

Applies to: unit, integration

Detection: `@pytest.fixture(autouse=True)` mutates environment, filesystem,
network, database, or global state for an entire module/session.

Rewrite: narrow fixture scope and request it explicitly from tests that need it.

### `python.LC-3` — parametrized cases miss contract-derived boundaries

Applies to: unit, integration

Detection: `pytest.mark.parametrize`, `subTest`, or table-driven fixture data
covers numeric, string, collection, parser, enum/state, CLI, or validated
inputs while visible contracts expose boundaries that are absent from the rows.
Inspect Pydantic constraints, dataclass validators, `argparse` choices/ranges,
attrs validators, parser grammar cutoffs, branch predicates, and route/request
schemas before falling back to generic sentinels. Generic values such as `0`,
`None`, `""`, and `[]` are `sentinel-only` unless they are actual boundaries
for the visible contract.

Rewrite: add below / at / above or before / at / after rows for the named
contract, plus the corresponding invalid partition where one exists.

### `python.POS-1` — explicit parametrized boundary set

Applies to: unit, integration

Detection: `pytest.mark.parametrize` or `subTest` covers contract-derived
boundary/equivalence classes with varied expected values.

### `python.POS-2` — property-based invariant

Applies to: unit, integration

Detection: Hypothesis `@given(...)` test asserts an invariant such as
round-trip, idempotency, ordering, bounds, or commutativity.

### `python.POS-3` — controlled resource fixture

Applies to: unit, integration

Detection: `tmp_path`, test database transaction fixture, fake clock, or
factory fixture creates per-test owned state and cleans it up.

## Carve-Outs

- Do not flag `LC-7` for pytest fixtures or `setUp` methods that create
  reusable test infrastructure when each test still names the behavior and owns
  its expected value.
- Do not flag environment patching as `python.HC-3` when the environment
  variable is the documented process boundary under test.
- Do not flag `tmp_path` filesystem use as unit-lane I/O when the function's
  public contract is filesystem behavior and the file tree is per-test owned.
- Do not flag Hypothesis-generated examples as random-value smells when the
  assertion expresses an invariant over generated inputs.

## SUT Surface Enumeration

Python gap detection is approximate and deep-mode only.

- **SUT identification:** inspect imports from the test package and project
  metadata. Exclude `tests/`, `.venv/`, build artifacts, generated caches, and
  migrations unless migration enumeration is active.
- **`Gap-API`:** public functions/classes in non-test modules matching
  `^def [a-zA-Z_][a-zA-Z0-9_]*\\(`, `^async def ...`, or `^class ...`, excluding
  names starting `_`.
- **`Gap-Route`:** decorators such as `@app.route`, `@router.get`,
  `@router.post`, Django `path(...)`, `re_path(...)`.
- **`Gap-Migration`:** Alembic revision files under `versions/` or Django
  migration classes/files under `migrations/`.
- **`Gap-Throw`:** `raise <ExceptionType>` in public functions or route
  handlers.
- **`Gap-Validate`:** Pydantic field constraints, dataclass validation,
  Marshmallow schema fields, Django form/model validators, and explicit
  request-schema validators.

Cross-reference by symbol name, route string, migration revision/name, or
exception type in test names, assertions, and bodies. Classify identifier-only,
import-only, route-status-only, and valid-payload-only tests as
`referenced-weak` or `referenced-incidental`; they do not suppress gaps for
missing invalid, auth, boundary, throw, migration, or state-change behavior.
Treat all static-only results as probable until mutation or manual review
confirms them.

## Determinism Verification

Cheap rerun command for non-E2E scopes:

```bash
pytest -q --maxfail=1
pytest -q --maxfail=1
```

Use only when the suite has fewer than 500 tests and the first run finishes
under 60 seconds, or when the user opts in. Compare failing test node IDs
between runs.

## Mutation Tool

### Tool name and link

Mutmut: https://mutmut.readthedocs.io/

### Install instructions

```bash
uv add --dev mutmut
```

or for non-uv projects:

```bash
python -m pip install mutmut
```

### Detection command

```bash
python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('mutmut') else 1)"
```

### Run command

```bash
mutmut run
mutmut results
```

If the project needs explicit source paths, use the project's documented mutmut
configuration or `mutmut run --paths-to-mutate <package>`.

### Known SUT limitations

- Native extension modules and generated C bindings may not be safely mutated;
  skip those modules and mutate the Python boundary around them.
- Framework-heavy import side effects can make mutation runs fail before tests
  start; extract pure logic into import-safe modules or configure mutmut paths.
- E2E/browser targets are out of scope for mutation; mutate the application
  package, not browser tests.

### Output parser notes

Capture the overall killed/survived/timeout summary from `mutmut results`.
When JSON or JUnit output is configured by the project, prefer that machine
output; otherwise report text-summary evidence and surviving mutant locations.
