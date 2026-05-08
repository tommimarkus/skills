# Rust Core Extension

Loaded when Rust test signals are present. This file owns Rust detection,
rubric routing, Rust test-double semantics, shared smells, SUT surface
enumeration, determinism verification, and the cargo-mutants mutation-tool
declaration. Load the matching rubric addon after `SKILL.md` selects the
rubric.

## Sources

Use these sources for platform facts:

- Cargo tests guide: https://doc.rust-lang.org/cargo/guide/tests.html
- `cargo test` command: https://doc.rust-lang.org/cargo/commands/cargo-test.html
- rustc/libtest harness: https://doc.rust-lang.org/rustc/tests/index.html
- cargo-nextest: https://nexte.st/ and https://nexte.st/docs/running/
- cargo-mutants: https://mutants.rs/, https://mutants.rs/mutants-out.html,
  and https://mutants.rs/mutants.html

Cite core quality rubrics for test-quality judgments.

## Detection Signals

- Rust project files: `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`,
  `.cargo/config.toml`, `src/**/*.rs`, `tests/**/*.rs`, `benches/**/*.rs`, or
  `examples/**/*.rs`.
- Runner/config signals: `cargo test`, `cargo nextest`, `.config/nextest.toml`,
  `nextest.toml`, CI jobs invoking Cargo test commands.
- Test attributes/macros: `#[test]`, `#[should_panic]`, `#[ignore]`,
  `#[tokio::test]`, `#[async_std::test]`, `#[actix_web::test]`, `#[rstest]`,
  `proptest!`, or `quickcheck!`.
- Test/support crates: `proptest`, `quickcheck`, `rstest`, `mockall`,
  `mockito`, `wiremock`, `serial_test`, `testcontainers`, `assert_cmd`,
  `predicates`, `insta`, `wasm-bindgen-test`, `cargo-mutants`.

## Test Type Detection Signals

Cargo runs tests from `src` files and top-level `tests/`; `cargo test` also
builds examples and runs library doctests by default. The `cargo test`
reference defines `--all-targets` as `--lib --bins --tests --benches
--examples`, while `--doc` is a separate target option. Do not assume a
rerun that uses `--all-targets` has exercised doctests.

### E2E rubric signals

- Browser automation crates or APIs: `thirtyfour`, `fantoccini`,
  `chromiumoxide`, `headless_chrome`, or browser WebDriver sessions.
- `wasm-bindgen-test` configured for a browser or tests tagged/named `e2e`,
  `browser`, `journey`, `a11y`, `perf`, or `security` that drive a browser.

### Integration rubric signals

- Files under top-level `tests/` that import the public crate and exercise a
  real process, network, filesystem, database, queue, or CLI boundary.
- Web/service harnesses: Axum/Rocket/Warp/Actix test clients, `reqwest` calls
  to a local/deployed URL, or TCP listeners bound during a test.
- Real adjacent dependencies: `sqlx::test`, Diesel/SeaORM connections,
  Redis/Kafka clients, `testcontainers`, or migrations.
- CLI black-box tests using `assert_cmd` / `Command::cargo_bin` with assertions
  on exit status, stdout/stderr, files, or process side effects.

### Unit rubric signals

- `#[cfg(test)] mod tests` beside the SUT or tests that call functions/types
  directly with in-memory values, fakes, stubs, or generated cases.
- Property tests whose generated values exercise an in-process invariant.
- No real browser, service process, network, database, or CLI process boundary.

## Test Double Classification

- Hand-written in-memory implementations of a trait are fakes, not mocks, when
  assertions target returned values or published side effects.
- `mockall`, custom recording fakes, or call counters are mocks only when the
  test verifies call counts, call order, or received arguments.
- `mockito` / `wiremock` are boundary stubs for outbound HTTP. They become a
  coverage smell only when the test claims provider-contract coverage.
- `serial_test` is a runner constraint, not a test double; inspect the global
  state it protects.

## Rubric-Neutral Smells

### `rust.HC-1` -- expected value mirrors the SUT iterator pipeline

Applies to: unit, integration

Detection: expected values are built with the same `iter().map/filter/fold`,
parser, serializer, or collection transform visible in the SUT.

Rewrite: derive expected values from the requirement example, domain invariant,
fixture, or property-based invariant.

### `rust.HC-2` -- mock expectation is the only proof

Applies to: unit, integration

Detection: the only assertion verifies `mockall` expectations, call count,
call order, or recorded arguments on an owned collaborator.

Rewrite: assert the public result, state transition, emitted event, persisted
record, or boundary output.

### `rust.HC-3` -- spawned async work is not observed

Applies to: unit, integration

Detection: a `tokio::spawn`, `async_std::task::spawn`, channel receiver, or
join handle is dropped while the test asserts before completion.

Rewrite: await the handle, assert the message/result, or expose a deterministic
completion signal.

### `rust.LC-1` -- broad `#[should_panic]`

Applies to: unit, integration

Detection: `#[should_panic]` has no expected message or the test arranges many
possible panic sites before the assertion point.

Rewrite: assert the typed `Result` / error variant, or narrow the panic test to
one contract and expected panic message.

### `rust.LC-2` -- ignored or serial tests hide required conditions

Applies to: unit, integration

Detection: `#[ignore]`, `serial_test`, or a runner profile is needed for the
test to pass but the opt-in command, global resource, or isolation reason is
not documented near the test or runner config.

Rewrite: name the required resource and command, or isolate the state so the
test can run with the normal suite.

### `rust.POS-1` -- contract-derived table or property cases

Applies to: unit, integration

Detection: table-driven cases or `proptest`/`quickcheck` invariants name the
boundary, equivalence class, or algebraic property they prove.

### `rust.POS-2` -- fake over interaction mock

Applies to: unit, integration

Detection: a trait fake, temporary directory, fake clock, in-memory repository,
or channel receiver lets the test assert an observable result.

## Carve-Outs

- Do not flag `#[cfg(test)] mod tests` or `use super::*` by itself; in-module
  tests are idiomatic. Flag only when the asserted behavior is private-helper
  coupling rather than a public contract.
- Do not flag `assert!(result.is_ok())` when the entire documented contract is
  "operation completes without error" and there is no value-bearing output.
- Do not route doctests to integration solely because they are outside
  `#[cfg(test)]`. Cargo/rustdoc doctests are documentation examples; classify
  them by the behavior and boundary they exercise, and report compile-only
  examples as weak evidence for value-bearing behavior.

## SUT Surface Enumeration

Rust gap detection is approximate and deep-mode only.

- **SUT identification:** inspect `Cargo.toml`, `cargo metadata` when
  available, `src/`, workspace members, and imports from tests.
- **`Gap-API`:** `pub fn`, `pub struct`, `pub enum`, `pub trait`, `pub type`,
  public inherent methods, and `pub(crate)` surfaces used outside a module.
- **`Gap-Route`:** Axum/Rocket/Warp/Actix route builders, router merges, and
  handler functions bound to public routes.
- **`Gap-CLI`:** binary entrypoints under `src/main.rs` or `src/bin/*.rs`,
  parser subcommands/options, and documented exit-code contracts.
- **`Gap-Error`:** public error enum variants, `thiserror`/`anyhow` boundary
  conversions, panic contracts, and explicit `Result` error paths.
- **`Gap-Cfg`:** public behavior behind Cargo features, target-specific `cfg`,
  or `no_std`/`std` splits.

Identifier-only tests, compile-only references, and success-path CLI invocations
are `referenced-weak` for error, cfg, auth, migration, state-change, and invalid
input gaps. Static-only gaps stay probable until mutation, coverage, or manual
review confirms them.

## Determinism Verification

Cheap rerun command for non-E2E scopes:

```bash
cargo test --workspace --all-targets --locked
cargo test --workspace --all-targets --locked
```

If doctests are in scope, add the separate Cargo doctest target:

```bash
cargo test --workspace --doc --locked
cargo test --workspace --doc --locked
```

If the repo uses nextest, prefer the configured profile:

```bash
cargo nextest run --workspace --profile ci
cargo nextest run --workspace --profile ci
```

The cargo-nextest docs state that doctests are not supported by nextest; keep
`cargo test --doc` as a separate step when documentation examples matter.

Run only when the suite is small enough to finish under 60 seconds per run or
the user opts in. Compare failing test names/binaries between runs.

## Mutation Tool

### Tool name and link

cargo-mutants: https://mutants.rs/

### Install instructions

```bash
cargo install --locked cargo-mutants
```

### Detection command

```bash
cargo mutants --version
```

### Run command

```bash
cargo mutants --output mutants.out
```

### Known SUT limitations

- `unsafe` functions are automatically excluded from mutation by
  cargo-mutants; report mutation coverage as unavailable for unsafe-only policy
  unless a separate review covers it.
- Functions marked with `#[cfg(test)]`, test functions, and
  `#[mutants::skip]` are excluded from mutation; inspect skipped/filtered
  areas before treating absence of mutants as coverage.
- Macro-generated code and generated bindings can produce poor mutation signal;
  prefer mutating the handwritten crate that owns the policy.
- Browser/E2E and external-service suites are usually too expensive for deep
  mutation; skip with a documented cost reason unless the user opts in.

### Output parser notes

Read `mutants.out/outcomes.json` for outcome counts and
`mutants.out/mutants.json` for generated mutant locations. Treat survived or
missed mutants as evidence to investigate, not automatic findings without
matching test-quality context.
