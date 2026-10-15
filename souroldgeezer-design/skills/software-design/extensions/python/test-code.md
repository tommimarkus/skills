# Python Test-Code Lane

Load when writing or restructuring Python test files, fixtures, and helpers, or
when `tdd-policy` hands off test-code structure for a Python project.

Sources: https://docs.pytest.org/en/stable/how-to/fixtures.html, https://docs.pytest.org/en/stable/how-to/tmp_path.html,
https://docs.pytest.org/en/stable/how-to/usage.html,
https://docs.python.org/3/library/unittest.html, https://docs.python.org/3/library/time.html,
https://docs.python.org/3/library/locale.html, https://pytest-xdist.readthedocs.io/en/stable/

## Shared test support

- pytest: fixtures and hooks live in `conftest.py`, visible to that directory
  and below and never imported; importable helpers, fakes, and builders live in
  a support package (`pytest.register_assert_rewrite` keeps its asserts
  readable). unittest: a helper module or base-class mixin imported by tests.
- Search `conftest.py` files, the support package, and `tests/` for an existing
  fixture or builder before defining one; a helper used by a second module
  moves to the nearest common `conftest.py` or the support package.

## Setup lifetime

- pytest fixture scopes: `function` (default), `class`, `module`, `package`,
  `session`. Widen only for immutable or safely resettable resources; teardown
  after `yield` runs in reverse setup order. A wide fixture caches its value, so
  one that read the environment never sees a later per-test `monkeypatch`.
- `tmp_path_factory` is session-scoped; use it for a shared directory, and
  `tmp_path` (per test) for anything a test writes.
- unittest: `setUpClass` / `setUpModule` run once; register teardown with
  `addClassCleanup` / `addModuleCleanup` so it runs even if setup fails, and
  use `enterClassContext` / `enterModuleContext` (3.11+) for context managers.
- Trap: a mutable object in a wide-scope fixture leaks state between tests
  (core `SD-C-4`); hand each test a copy or reset it per test.

## Time, randomness, and ambient environment

- Time: inject a clock or a callable, patch it with `unittest.mock`, or use a
  freezing library the project already has (a frozen monotonic clock hangs a
  deadline loop unless it ticks). Wait on `threading.Event.wait(timeout)` or
  poll a condition with a deadline, not `time.sleep`. Seed a local
  `random.Random(seed)` rather than the global one.
- Change environment, cwd, and attributes through `monkeypatch` or
  `mock.patch.dict(os.environ)` so the change undoes itself.
- Timezone: prefer aware datetimes; otherwise set `TZ`, call `time.tzset()`
  (Unix only; guard with `hasattr`), and restore both.
- Locale: `locale.setlocale` changes process-global state, is not thread-safe,
  and raises `locale.Error` when the locale is not installed, so check or skip
  explicitly and restore it. Assert the locale took effect (core `SD-B-5`).
- Encoding: pass `encoding=` on every `open()`; run with `-X warn_default_encoding`
  or `PYTHONWARNDEFAULTENCODING` to surface implicit use as `EncodingWarning`.

## Isolation and parallel runs

- pytest-xdist (only if the project uses it) runs workers as separate
  processes, each with its own session fixtures, so once-per-run work takes a
  file lock under the shared base temp directory. Collection must match across
  workers: parametrize from ordered lists, not sets.
- Make shared resources worker-unique (the `worker_id` fixture or `tmp_path`),
  never a fixed port, file, or database name.
- Process-global state (env, cwd, locale, `sys.modules`, logging handlers,
  warning filters, cached singletons) is restored by the fixture that changed it.

## Lanes and durations

- pytest: register markers in config (`--strict-markers` enforces it) and
  select with `-m "expr"`, or split by directory (`tests/unit`,
  `tests/integration`). unittest: gate with `skipUnless` on an environment
  flag, or separate discovery directories.
- Durations: `pytest --durations=N` (`--durations-min=S` cuts noise) reports
  setup and teardown apart from the call, so fixture cost shows;
  `python -m unittest --durations N` (3.12+).

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
