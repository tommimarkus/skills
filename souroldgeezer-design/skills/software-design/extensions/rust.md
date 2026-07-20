# Rust Software Design Extension

Load for `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`, `.cargo/config.toml`,
Rust source, `build.rs`, proc-macro crates, Cargo features, `no_std`, or Rust
repo tooling.

Covers crate/workspace/API design. Delegate unsafe/FFI, supply chain, secrets,
permissions, and command execution to `devsecops-audit`; delegate tests to
`test-quality-audit`.

Sources: Cargo workspaces
https://doc.rust-lang.org/cargo/reference/workspaces.html, Cargo features
https://doc.rust-lang.org/cargo/reference/features.html, visibility/privacy
https://doc.rust-lang.org/reference/visibility-and-privacy.html, and Rust API
Guidelines https://rust-lang.github.io/api-guidelines/.

Inspect workspace members/default-members, features, profiles, library/binary
crates, `pub`/`pub(crate)`/re-exports, traits/generics/errors, build scripts,
generated code, proc macros, async/runtime ownership, globals, locks, channels,
and validation (`cargo check`, `cargo clippy`, `cargo fmt`, feature matrix,
docs/examples, or smoke).

Defaults: crate boundaries reflect policy, adapter, release, or reuse; binary
entrypoints stay thin; `pub`/`pub use` are contracts; features are additive and
feature unification means mutually exclusive semantics need separate packages,
runtime config, or matrix evidence; traits need current variation or external
isolation; unsafe/FFI/generated code gets a small safe wrapper.

For Build mode, include `devsecops-audit` Quick review for unsafe, FFI, build
scripts, command execution, generated code, or dependency-sensitive changes
when available. Otherwise use `cargo check --workspace --all-targets --locked`,
`cargo clippy --workspace --all-targets --locked`, `cargo fmt --check`, feature
matrix checks, or smoke.

Smell codes: `rust.SD-B-*` for crate/binary/pub/build/proc/FFI boundary drift;
`rust.SD-C-*` for policy-to-adapter deps, non-additive features, one-impl
traits, or runtime/global coupling; `rust.SD-S-*` for error, stringly-state, or
ownership contract drift; `rust.SD-E-*` for brittle public traits/enums;
`rust.SD-Q-*` for unsafe/FFI/generated boundary width.

Key codes: `rust.SD-B-3` `pub`/re-export exposes internals; `rust.SD-C-2`
feature flags are non-additive or change public semantics; `rust.SD-C-3` trait
wraps one implementation for tests/ceremony; `rust.SD-S-1` error type collapses
domain/transport/infrastructure failures; `rust.SD-Q-1` unsafe/FFI/generated
boundary is too wide to review independently.

Only these key codes are citable; the `Smell codes:` families above describe
scope only. Emit core `SD-*` for anything not covered by a key code.
