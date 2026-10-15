# TypeScript Test-Code Lane

Load when writing or restructuring TypeScript/JavaScript test files, fixtures,
or helpers, or on a `tdd-policy` handoff. Use the project's existing runner;
add no runner, plugin, or dependency.

Sources: https://vitest.dev/config/pool; https://vitest.dev/config/isolate;
https://vitest.dev/guide/mocking/timers; https://jestjs.io/docs/cli;
https://nodejs.org/api/test.html; https://nodejs.org/api/cli.html.

## Shared test support

- Search the test tree and setup entry for existing factories, builders, and
  harnesses before defining one.
- Global registration uses the setup hook (Vitest `setupFiles`, Jest
  `setupFilesAfterEnv`); `node:test` just imports a support module.
- A helper needed by a second file moves to a support module beside the tests
  (`test/support/`), not into production source.

## Setup lifetime

- File-level `beforeAll`/`before` only for immutable infrastructure (a built
  app, a read-only fixture, a started server); mutable state is rebuilt in
  `beforeEach`.
- A `beforeAll` product that tests mutate is shared state (core `SD-C-4`).
- Module-level state (caches, singletons, mocked modules) outlives a test;
  reset it per test through the runner's reset facilities.

## Time, randomness, and ambient environment

- Control time with the runner's fake timers (`vi.useFakeTimers`,
  `jest.useFakeTimers`, `node:test` `mock.timers`) and a fixed clock
  (`vi.setSystemTime`, Jest `setSystemTime`, `mock.timers` `Date` with `now`).
  Restore real timers in `afterEach`.
- Prefer injecting the clock or random seed over patching globals (core
  `SD-B-5`).
- Pass an explicit locale and `timeZone` to `Intl.*` and `toLocaleString` in
  tests; assert `Intl.DateTimeFormat().resolvedOptions()` when the test
  depends on an environment-set value, since missing ICU data falls back
  silently.
- `TZ` is read from the process: set it in the npm script or CI step that
  launches the runner, or assign `process.env.TZ` before any `Date` use. Node
  honors a runtime assignment on POSIX and Windows in recent versions. Vitest's
  `threads` pool does not apply a changed `TZ` (use `forks`), so assert the
  resulting offset instead of trusting the setting.

## Isolation and parallel runs

- Vitest: test files run in parallel workers (`pool`: `forks` default,
  `threads`, VM pools); `fileParallelism: false` serializes files;
  `sequence.concurrent` runs a file's tests concurrently, so they must not
  share mutable state.
- `isolate: false` shares module state between files; use it only when no file
  relies on side effects, or scope it to one project.
- Jest: `--maxWorkers` bounds the pool, `--runInBand` serializes.
- `node:test` isolates each file in a process; `--test-concurrency` bounds it,
  and `--test-isolation=none` shares global state across files.
- Tests sharing a port, directory, or database take per-worker unique
  resources (temp dirs, ephemeral ports) rather than forcing serial runs.

## Lanes and durations

- Separate lanes by file suffix or directory (`*.int.test.ts`), selected
  through runner projects (Vitest `projects`, Jest `projects` with
  `--selectProjects`), a path pattern (`--testPathPatterns`), or `node:test`
  `--test-name-pattern`.
- Read per-test durations from the verbose or JSON reporter (Vitest
  `--reporter=verbose`, Jest `--verbose` or JSON output, `node:test`
  `duration_ms` in the `test:pass` event or the JUnit reporter).

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
