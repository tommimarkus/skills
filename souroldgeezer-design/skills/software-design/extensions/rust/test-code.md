# Rust Test-Code Lane

Load when writing or restructuring this stack's test files, fixtures, and
helpers, or on a `tdd-policy` handoff to apply the test-code file for the
detected stack. Use the runner the project already has.

Sources: Cargo book test targets https://doc.rust-lang.org/cargo/reference/cargo-targets.html#tests,
Rust book test organization https://doc.rust-lang.org/book/ch11-03-test-organization.html,
cargo-nextest https://nexte.st/docs/design/how-it-works/ and
https://nexte.st/docs/features/slow-tests/, tokio test attribute
https://docs.rs/tokio/latest/tokio/attr.test.html.

## Shared test support

- Search `tests/common`, `#[cfg(test)]` modules, and any test-support crate
  before defining a helper.
- Integration helpers live in `tests/common/mod.rs`, pulled in with `mod
  common;`; a `tests/common.rs` file would be built as its own test target.
- Unit-test helpers sit in a `#[cfg(test)]` module; helpers shared across
  workspace crates go in a test-support crate used as a dev-dependency.
- Every file directly under `tests/` is its own crate and binary. Many small
  files cost link time; a single `tests/<name>/main.rs` with modules is the
  variant that merges them.

## Setup lifetime

- Per-test setup is a constructor or builder returning a value whose `Drop`
  cleans up; prefer it to shared mutable state.
- `OnceLock` / `LazyLock` statics amortize setup across tests only within one
  process: `cargo test` runs a binary's tests as threads of one process, while
  cargo-nextest gives each test its own process, so the static is rebuilt per
  test there. Do not rely on either behavior for correctness.
- Widest scope only for immutable data (a parsed fixture, a read-only seed);
  anything a test mutates is built per test.

## Time, randomness, and ambient environment

- Production code takes a clock trait or closure rather than calling
  `SystemTime::now` or `chrono::Local` (core `SD-B-5`); seed or inject randomness.
- Async time: `#[tokio::test(start_paused = true)]` (needs tokio's `test-util`
  feature) with `tokio::time::advance` instead of sleeping; otherwise wait on a
  channel or condition with a bounded timeout.
- Locale and timezone: pass them explicitly to the code under test. Setting
  `TZ` or other variables in-process is `unsafe` (`std::env::set_var` since
  edition 2024) and racy, and the process-wide value may already be cached;
  assert the value took effect.
- Scratch files: `tempfile` is common, `std::env::temp_dir` with a unique
  per-test subdirectory is the dependency-free variant.

## Isolation and parallel runs

- `cargo test` threads share process state: environment, current directory,
  statics, ports (core `SD-C-4`). Use `--test-threads=1` or a shared lock only
  for tests that truly need it, and prefer injection over global mutation.
- Process-per-test runners isolate statics but not files, ports, or databases;
  give each test unique names or directories.

## Lanes and durations

- Mark slow or external tests `#[ignore = "reason"]` and run them with
  `--ignored` or `--include-ignored`; other lanes are separate `tests/` targets
  or Cargo features.
- cargo-nextest prints a duration per test and a SLOW status past a
  configurable threshold; plain `cargo test` has per-test timing only through
  the nightly-only `--report-time`.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
