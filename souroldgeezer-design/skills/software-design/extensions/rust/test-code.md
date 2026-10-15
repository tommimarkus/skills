# Rust Test-Code Lane

Load when writing or restructuring this stack's test files, fixtures, and
helpers, or on a `tdd-policy` handoff; use the runner the project already has.

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
  Helpers shared across workspace crates go in a test-support crate used as a
  dev-dependency; `#[cfg(test)]` items are invisible to integration tests.
- Every file directly under `tests/` is its own crate and binary. Many small
  files cost link time; one `tests/<name>/main.rs` with modules merges them.
- Locate fixtures from `env!("CARGO_MANIFEST_DIR")`, integration scratch space
  from `CARGO_TARGET_TMPDIR`, and built binaries from `CARGO_BIN_EXE_<name>`,
  never from the working directory.

## Setup lifetime

- Per-test setup returns a value whose `Drop` cleans up. Bind such guards to a
  variable that lives to the end of the test: a temporary dropped at the end of
  its statement cleans up at once. `Drop` does not run on abort or a runner
  kill, so external resources need a reaper.
- `OnceLock` / `LazyLock` statics amortize setup only within one process:
  `cargo test` runs a binary's tests as threads of one process, while
  cargo-nextest gives each test its own process. Initialize process-global
  state (logger, crypto provider) idempotently, for example with `try_init`.
- Each `#[tokio::test]` builds its own runtime, so runtime-bound handles
  (pools, clients, spawned tasks) never sit in a shared static.

## Time, randomness, and ambient environment

- Production code takes a clock trait or closure rather than calling
  `SystemTime::now` or `chrono::Local` (core `SD-B-5`); seed or inject
  randomness, and keep `HashMap` iteration order out of expected output.
- `#[tokio::test(start_paused = true)]` (tokio's `test-util` feature) with
  `tokio::time::advance` replaces sleeping; only tokio's time types follow the
  paused clock. Otherwise wait on a channel or condition with a bounded timeout.
- Pass locale and timezone to the code under test. `std::env::set_var` is
  `unsafe` since edition 2024 and races other test threads; shared defaults
  such as `TZ` belong in `.cargo/config.toml` `[env]`. Assert a value took
  effect.
- Scratch files: `tempfile` is common; `std::env::temp_dir` with a unique
  per-test subdirectory is the dependency-free variant.

## Isolation and parallel runs

- `cargo test` threads share process state: environment, current directory,
  statics, ports (core `SD-C-4`). Bind port 0 and read the address back; use
  `--test-threads=1` or a shared lock only for tests that truly need it.
- An in-process lock does not serialize across nextest's processes; use a
  nextest test group with `max-threads = 1` for a shared external resource.

## Lanes and durations

- Mark slow or external tests `#[ignore = "reason"]` and run them with
  `--ignored` or `--include-ignored`; other lanes are separate `tests/` targets
  or Cargo features. nextest does not run doctests, so keep `cargo test --doc`.
- cargo-nextest prints a duration per test and a SLOW status past a
  configurable threshold; plain `cargo test` has per-test timing only through
  the nightly-only `--report-time`.

Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`.
