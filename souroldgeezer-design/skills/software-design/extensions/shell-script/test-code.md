# Shell Script Test-Code Lane

Load when writing or restructuring shell test files, fixtures, and helpers
(Bats first; shunit2 and plain test scripts follow the same ideas), or when
`tdd-policy` hands off test-code structure for a shell project.

Sources: https://bats-core.readthedocs.io/en/stable/writing-tests.html,
https://bats-core.readthedocs.io/en/stable/usage.html,
https://www.gnu.org/software/bash/manual/bash.html

## Shared test support

- Bats: shared helpers live in a `test_helper/` directory beside the tests and
  are pulled in with `load` (path relative to the test file). Helper libraries
  installed on `BATS_LIB_PATH` are loaded with `bats_load_library`.
- Search `test_helper/` and sibling `.bats` files for an existing helper before
  defining one; a function needed by a second file moves into `test_helper/`.
- Plain scripts: one sourced `lib` file of test helpers, sourced by path
  relative to the script, not the caller's cwd.

## Setup lifetime

- `setup_file` / `teardown_file` run once per file; `setup` / `teardown` run
  around each test. Put only immutable or safely resettable work (building a
  fixture tree, starting a read-only stub) in the file-level pair and export
  what tests need from it.
- Temp dirs: `BATS_TEST_TMPDIR` (per test), `BATS_FILE_TMPDIR` (per file),
  `BATS_SUITE_TMPDIR` (whole run). Write mutable state to the per-test one.
- Trap: globals and `cd` set in one test do not carry over, because each test
  runs in its own process; do not rely on that for state you meant to share
  (core `SD-C-4`). `teardown` also runs after a failed `setup`, so guard state
  that may be only partly created.

## Time, randomness, and ambient environment

- Replace `sleep` with a bounded polling loop on the observable condition
  (file exists, port answers, log line) that fails after a deadline. Control
  `date` by injecting a timestamp variable or a stub earlier on `PATH`.
- Set `LC_ALL=C` (or the specific `LC_*`) in the harness, and `TZ` per test.
  A locale that is not installed falls back silently, so probe that it took
  effect, for example with `locale` output or a known-format command (core
  `SD-B-5`).
- Reset the environment in one shared helper, not per test: `HOME` (and XDG
  dirs) under the temp dir, `LANG`, `TZ`, and `PATH` with a per-test stub
  `bin/` first. Stub only external effects, never the core utilities the runner
  itself uses; run `hash -r` after changing `PATH` in a long-lived shell.

## Isolation and parallel runs

- `bats --jobs N` needs GNU parallel (or a compatible tool such as rush) and
  runs files and tests concurrently; every test needs unique temp paths, ports,
  and names (use `BATS_TEST_TMPDIR`).
- A background service started in `setup_file` redirects its output and closes
  file descriptor 3 (`3>&-`), or Bats waits on it at the end of the file; keep
  its pid in `BATS_FILE_TMPDIR` and stop it in `teardown_file`.
- Set `BATS_NO_PARALLELIZE_WITHIN_FILE=true` (in `setup_file` or at file top)
  for a file whose tests share state; `--no-parallelize-within-files` does the
  same for the whole run.

## Lanes and durations

- Tag a test with a `# bats test_tags=slow,integration` comment above `@test`
  (`# bats file_tags=` for the whole file) and select with
  `--filter-tags slow,!flaky`; or split by directory. Tags are case-sensitive.
- Durations: `bats --timing` (`-T`) prints per-test time.
- Tags, `setup_file`, and the `BATS_*_TMPDIR` variables need a recent
  bats-core; check `bats --version`, as older distribution packages lack them.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
