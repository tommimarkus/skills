# Rust Unit Addon

Loaded after `core.md` when `SKILL.md` selects the unit or component
rubric.

## Detection Signals

- `#[cfg(test)] mod tests` beside the SUT.
- Direct function/type construction, trait fakes, in-memory state, temporary
  paths, property tests, or `rstest` cases without real process boundaries.
- No real browser, service process, database, queue, or CLI process boundary.

## Framework-Specific High-Confidence Smells

### `rust.HC-4` -- private helper is the asserted contract

Applies to: unit

Detection: the test calls a private helper or module-internal function and
does not assert through the public function/type that owns the behavior.

Rewrite: test the public contract, or promote the helper into an explicit
module boundary with its own visible responsibility.

### `rust.HC-5` -- value-bearing result checked only for presence

Applies to: unit

Detection: assertions are only `is_ok`, `is_some`, `is_err`, `is_none`, or
`matches!(..., Ok(_))` while the returned value or error variant carries the
contract.

Rewrite: assert the concrete value, invariant, error variant, or published side
effect.

### `rust.HC-6` -- clone/default fixture erases the scenario

Applies to: unit

Detection: the test builds the SUT with `Default::default()`, blanket clones,
or a fixture builder whose defaults hide the behavior-specific input.

Rewrite: make the behavior-relevant fields explicit in the test and leave only
irrelevant boilerplate in helpers.

## Framework-Specific Low-Confidence Smells

### `rust.LC-3` -- macro case names do not state the requirement

Applies to: unit

Detection: `rstest`, table arrays, or property-case names use generic labels
such as `case1` while the expected values differ by requirement boundary.

Rewrite: name each row or strategy by the boundary/equivalence class it proves.

### `rust.LC-4` -- feature-gated behavior only tested on default features

Applies to: unit

Detection: source has `#[cfg(feature = "...")]` or `cfg_attr` branches but the
test evidence only shows default-feature `cargo test`. Cargo features should be
additive, default features can be disabled with `--no-default-features`, and
feature unification means one dependency can enable features for another path
through the graph.

Rewrite: add explicit feature-matrix tests for the supported combinations, such
as default, `--no-default-features`, `--all-features`, or documented
`--features package/feature` cases, or document why a branch is not in scope.

## Framework-Specific Positive Signals

### `rust.POS-3` -- explicit edge-case table

Applies to: unit

Detection: test rows name below/at/above, empty/single/many, invalid/valid, or
state-transition boundaries with distinct expected results.

### `rust.POS-4` -- typed error assertion

Applies to: unit

Detection: tests match exact error enum variants, source locations, or
domain-specific error fields instead of checking broad failure.

## Carve-Outs

- Do not flag `Default::default()` for irrelevant collaborator fields when the
  behavior-specific input and expected result are explicit.
- Do not flag tests of private functions when the module itself is the crate's
  intended boundary and the user requested module-level review.
