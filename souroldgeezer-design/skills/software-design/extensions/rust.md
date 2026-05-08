# Rust Software Design Extension

Load for Rust crates and workspaces: `Cargo.toml`, `Cargo.lock`,
`rust-toolchain*`, `.cargo/config.toml`, `src/**/*.rs`, `build.rs`, `proc-macro`
crates, Cargo features, `no_std` declarations, or Rust files invoked from
repo tooling.

This extension covers crate/module/API design, not borrow-checker tutorials,
unsafe-code security, dependency supply chain, or test quality. Delegate unsafe
audit, supply chain, permissions, secrets, and command execution to
`devsecops-audit`; delegate test quality to `test-quality-audit`.

## Sources

Use these sources for platform facts:

- Cargo workspaces: https://doc.rust-lang.org/cargo/reference/workspaces.html
- Cargo features: https://doc.rust-lang.org/cargo/reference/features.html
- Rust visibility and privacy:
  https://doc.rust-lang.org/reference/visibility-and-privacy.html
- Rust API Guidelines: https://rust-lang.github.io/api-guidelines/

Cite the core software-design reference for design judgments.

## Assimilation Signals

Inspect only what affects design shape:

- workspace/package topology: root vs virtual workspace, members,
  `default-members`, shared `Cargo.lock`, shared output directory, workspace
  dependencies, feature and profile placement;
- crate boundary: library vs binary crates, `src/lib.rs`, `src/main.rs`,
  `src/bin/*.rs`, `pub` / `pub(crate)`, modules, re-exports, sealed traits;
- API semantics: public traits, generic parameters, associated types, error
  enums, builders, newtypes, conversion traits, ownership/borrowing contracts;
- conditional surface: Cargo features, target-specific `cfg`, `no_std`/`std`,
  optional dependencies, build scripts, generated code, proc macros;
- state and async boundaries: globals, `OnceLock`/lazy statics, runtime
  ownership, channels, tasks, locks, cancellation, drop behavior;
- validation surface: `cargo check`, `cargo clippy`, `cargo fmt`, feature
  matrix checks, docs/examples, or project smoke commands.

## Design Defaults

- Crate boundaries should reflect reusable policy, adapter edges, or release
  units, not one crate per folder by habit.
- Keep binary entrypoints thin; reusable policy belongs in library modules or
  explicit adapters.
- Public `pub` APIs are compatibility contracts. Prefer `pub(crate)` or
  private modules until a downstream boundary needs the surface.
- Re-export intentionally from a narrow facade; avoid `prelude` or wildcard
  modules that hide ownership.
- Prefer concrete types until trait abstraction removes real duplication,
  isolates an external boundary, or enables current variation.
- Model state with owned values, newtypes, enums, and explicit lifetimes before
  reaching for globals or shared mutable locks.
- Keep Cargo features additive and behaviorally small. Cargo features are
  additive by design; because Cargo performs feature unification across the
  selected dependency graph, avoid mutually exclusive feature semantics in one
  package. Use separate packages, explicit runtime configuration, or a
  documented cfg matrix when behavior really must vary.
- Treat `pub` and `pub use` as design decisions. Rust defaults items to
  private, while `pub(crate)`, `pub(super)`, and `pub(in path)` can expose a
  narrower internal boundary without committing a downstream public API.
- For public structs and traits, preserve future evolution: hide fields that
  own invariants, prefer named domain types over booleans/tuples, and avoid
  trait bounds on data structures unless the bound carries semantic value.
- Keep unsafe, FFI, generated code, and proc macros behind small audited
  boundaries with safe wrappers and clear ownership.

## Validation Requirement

For Build mode on Rust targets, the `Validation step` MUST include a
`devsecops-audit` Quick review when unsafe code, FFI, build scripts, command
execution, generated code, or supply-chain-sensitive dependency changes are in
scope and that skill is available. If unavailable, state that in `Delegations`
or `Limits` and use the cheapest applicable fallback: `cargo check --workspace
--all-targets --locked`, `cargo clippy --workspace --all-targets --locked`,
`cargo fmt --check`, feature-matrix checks such as `--all-features` /
`--no-default-features` when cfg behavior changed, or a project smoke command.

## Smells

| Code | Signal | Default |
|---|---|---|
| `rust.SD-B-1` | Workspace members or crates split by folder convenience instead of policy, adapter, or release boundary. | warn |
| `rust.SD-B-2` | Binary entrypoint owns reusable domain/workflow policy. | warn |
| `rust.SD-B-3` | `pub` surface exposes implementation modules or types with no downstream contract. | warn; block when new public API |
| `rust.SD-B-4` | Re-export/prelude hides the owning module or boundary story. | info; warn when public |
| `rust.SD-B-5` | `build.rs`, generated code, proc macro, or FFI surface owns business policy. | warn; block when hard to audit |
| `rust.SD-C-1` | Crate dependency direction points from policy into adapter/infrastructure crates. | block when new |
| `rust.SD-C-2` | Feature flags are non-additive, mutually exclusive in practice, or change public semantics without a matrix contract. | warn |
| `rust.SD-C-3` | Trait abstraction exists only to satisfy tests or wraps one concrete implementation. | info; warn when public |
| `rust.SD-C-4` | Shared mutable global, lazy singleton, or process-wide runtime couples independent calls. | warn; block when cleanup depends on it |
| `rust.SD-S-1` | Error type collapses distinct domain, transport, and infrastructure failures. | warn |
| `rust.SD-S-2` | Boolean/tuple/stringly API encodes domain states that need names. | warn |
| `rust.SD-S-3` | Ownership/lifetime contract forces callers to clone, leak, or pin data without a boundary reason. | warn |
| `rust.SD-S-4` | Async task/channel boundary has no owner for cancellation, shutdown, or backpressure. | warn |
| `rust.SD-W-1` | Macro/proc-macro ceremony replaces a small explicit API without current variation. | info; warn when public |
| `rust.SD-W-2` | Workspace wrapper crate re-exports every member without adding a stable facade. | info |
| `rust.SD-E-1` | Feature, target, or `no_std` split lacks validation for supported combinations. | warn |
| `rust.SD-E-2` | Public trait or enum is impossible to evolve without breaking downstream implementers. | warn |
| `rust.SD-Q-1` | Unsafe/FFI/generated boundary is too wide to review or test independently. | block |

## Review Notes

Do not flag Rust-specific syntax, generics, traits, macros, or lifetimes by
themselves. Flag the boundary, dependency, semantic, coupling, evolution, or
tradeoff risk and name the smaller shape that would reduce it.
