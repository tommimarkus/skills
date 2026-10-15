# TypeScript Test-Code Lane

Load when writing or restructuring TypeScript/JavaScript test files, fixtures,
or helpers, or on a `tdd-policy` handoff. Use the project's existing runner;
add no runner, plugin, or dependency.

Sources: https://vitest.dev/config/pool; https://vitest.dev/config/isolate;
https://vitest.dev/guide/mocking/timers; https://jestjs.io/docs/cli;
https://nodejs.org/api/test.html; https://nodejs.org/api/cli.html.

## Shared test support

- Search the test tree and setup files for factories, builders, and harnesses
  before defining one. A helper needed by a second file moves to a support
  directory beside the tests (`test/support/`), named so it never matches the
  test glob (Jest takes every file under `__tests__/` as a test), not into
  production source.
- Per-file registration uses the setup hook (Vitest `setupFiles`, Jest
  `setupFilesAfterEnv`); `node:test` imports a support module. Global setup
  runs in the parent process, so its state reaches tests only through Vitest
  `provide`/`inject`, environment variables, or files.

## Setup lifetime

- File-level `beforeAll`/`before` only for immutable infrastructure (a built
  app, a read-only fixture, a started server); mutable state is rebuilt in
  `beforeEach`. A `beforeAll` product that tests mutate is shared state (core
  `SD-C-4`).
- Vitest `test.extend` fixtures keep setup and teardown (after `use`) together
  and run only for tests that request them; prefer them to hook-held state.
- Module-level state (caches, singletons, mocked modules) outlives a test;
  reset mocks, env stubs, and stubbed globals in runner config
  (`restoreMocks`, `unstubEnvs`, `unstubGlobals`), not scattered calls.

## Time, randomness, and ambient environment

- Prefer an injected clock or random seed (core `SD-B-5`); otherwise use the
  runner's fake timers (`vi.useFakeTimers`, `jest.useFakeTimers`, `node:test`
  `mock.timers`) with a fixed clock (`setSystemTime`, `mock.timers` `now`),
  faking only the APIs the test needs so I/O callbacks still run, and restore
  real timers in `afterEach`.
- Pass an explicit locale and `timeZone` to `Intl.*` and `toLocaleString`;
  assert `Intl.DateTimeFormat().resolvedOptions()` when a test depends on an
  environment-set value, since missing ICU data falls back silently.
- `TZ` is read from the process: set it in the script or CI step that launches
  the runner, or assign `process.env.TZ` before any `Date` use. Vitest's
  `threads` pool does not apply a changed `TZ` (use `forks`), so assert the
  resulting offset instead of trusting the setting.
- Resolve fixture paths from `import.meta.dirname` or `__dirname`, never cwd.

## Isolation and parallel runs

- Vitest: test files run in parallel workers (`pool`: `forks` default,
  `threads`, VM pools); `fileParallelism: false` serializes files.
  `sequence.concurrent` runs a file's tests concurrently, so they share no
  mutable state and use the test context's `expect`. `isolate: false` shares
  module state between files; use it only when no file relies on side effects.
- Jest: `--maxWorkers` bounds the pool, `--runInBand` serializes. `node:test`
  isolates each file in a process; `--test-concurrency` bounds it, and
  `--test-isolation=none` shares global state across files.
- Derive per-worker databases, directories, and ports from the worker id
  (`VITEST_POOL_ID`, `JEST_WORKER_ID`) or port 0 rather than forcing serial runs.

## Lanes and durations

- Separate lanes by file suffix or directory (`*.int.test.ts`), selected
  through runner projects (Vitest `projects`, Jest `projects` with
  `--selectProjects`), a path pattern (`--testPathPatterns`), or `node:test`
  `--test-name-pattern`.
- Read per-test durations from the verbose or JSON reporter (Vitest
  `--reporter=verbose`, Jest `--verbose`, `node:test` `duration_ms`); Vitest's
  summary splits out setup and collect time, exposing heavy setup files.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
