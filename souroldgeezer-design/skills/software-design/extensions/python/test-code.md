# Python Test-Code Lane

Load when writing or restructuring Python test files, fixtures, and helpers, or
when `tdd-policy` hands off test-code structure for a Python project.

Sources: https://docs.pytest.org/en/stable/how-to/fixtures.html,
https://docs.pytest.org/en/stable/how-to/tmp_path.html,
https://docs.pytest.org/en/stable/how-to/usage.html,
https://docs.python.org/3/library/unittest.html,
https://docs.python.org/3/library/time.html,
https://docs.python.org/3/library/locale.html,
https://pytest-xdist.readthedocs.io/en/stable/

## Shared test support

- pytest: shared fixtures live in `conftest.py`, visible to tests in that
  directory and below; put a fixture at the lowest directory that needs it.
  unittest: a plain helper module or base-class mixin imported by tests.
- Search `conftest.py` files, the helper package, and `tests/` for an existing
  fixture or builder before defining one; a helper used by a second module
  moves to the nearest common `conftest.py` or helper module.

## Setup lifetime

- pytest fixture scopes: `function` (default), `class`, `module`, `package`,
  `session`. Widen only for immutable or safely resettable resources; put
  teardown after `yield` so it runs in reverse setup order.
- `tmp_path_factory` is session-scoped; use it for a shared directory, and
  `tmp_path` (per test) for anything a test writes.
- unittest: `setUpClass` / `setUpModule` run once; register teardown with
  `addClassCleanup` / `addModuleCleanup` so it runs even if setup fails, and
  use `enterClassContext` / `enterModuleContext` (3.11+) for context managers.
- Trap: a mutable object in a wide-scope fixture leaks state between tests
  (core `SD-C-4`); hand each test a copy or reset it per test.

## Time, randomness, and ambient environment

- Time: inject a clock or a callable into the code under test, or patch the
  clock with `unittest.mock`, or use a freezing library the project already
  has. Wait on `threading.Event.wait(timeout)` or poll a condition with a
  deadline, not `time.sleep`.
- Randomness: seed a local `random.Random(seed)` rather than the global one.
- Timezone: set `os.environ["TZ"]`, then call `time.tzset()` (Unix only; guard
  with `hasattr`), and restore both afterwards (`monkeypatch` or
  `mock.patch.dict`). Prefer aware datetimes so tests need not touch `TZ`.
- Locale: `locale.setlocale` changes process-global state, is not thread-safe,
  and raises `locale.Error` when the locale is not installed, so check or skip
  explicitly and restore it. Assert the locale took effect (core `SD-B-5`).
- Encoding: pass `encoding=` on every `open()`; run with `-X warn_default_encoding`
  or `PYTHONWARNDEFAULTENCODING` to surface implicit use as `EncodingWarning`.

## Isolation and parallel runs

- pytest-xdist (only if the project uses it) runs workers as separate
  processes, each with its own session fixtures; collection must be identical
  across workers, so parametrize from ordered lists, not sets.
- Make shared resources worker-unique (the `worker_id` fixture or `tmp_path`),
  never a fixed port, file, or database name.
- Process-global state (env, cwd, locale, `sys.modules`) is restored by the
  fixture that changed it.

## Lanes and durations

- pytest: register markers in config and select with `-m "expr"`; or split by
  directory (`tests/unit`, `tests/integration`). unittest: gate with
  `skipUnless` on an environment flag, or separate discovery directories.
- Durations: `pytest --durations=N` (add `--durations-min=S` to cut noise);
  `python -m unittest --durations N` (3.12+).

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
