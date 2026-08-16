# Extension: Rust — deep-mode procedures

Deep-mode-only procedures for the Rust test-quality-audit extension:
SUT surface enumeration, determinism verification, and the cargo-mutants mutation
tool declaration. Loaded only in Deep mode, for any rubric; Quick audits
never load it. Detection, dispatch, and smells stay in [`core.md`](core.md).

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
