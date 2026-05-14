# Rust Integration Addon

Loaded after `core.md` when `SKILL.md` selects the integration rubric.

## Detection Signals

- Top-level `tests/*.rs` or workspace-member tests importing the public crate.
- `assert_cmd`, `Command::cargo_bin`, `reqwest`, Axum/Rocket/Warp/Actix
  harnesses, TCP listeners, `testcontainers`, `sqlx::test`, Diesel/SeaORM
  connections, Redis/Kafka clients, migrations, or filesystem persistence.
- Contract tests against local/deployed services without browser automation.

## Framework-Specific High-Confidence Smells

### `rust.I-HC-A1` -- shared external state without per-test ownership

Applies to: integration

Detection: fixed database rows, buckets, ports, directories, queues, or
container resources are shared across tests without transaction rollback,
unique keys, cleanup, or isolated resources.

Rewrite: use per-test resources, unique IDs, transactions, temporary
directories, ephemeral ports, or container lifecycle ownership.

### `rust.I-HC-A2` -- global process mutation leaks across tests

Applies to: integration

Detection: a test changes `std::env`, current directory, process-wide logger,
static/global state, or runtime config without restoration.

Rewrite: scope changes with guards/fixtures that restore state, or move the
state behind injected configuration.

### `rust.I-HC-B1` -- live response snapshot as contract

Applies to: integration

Detection: full JSON/stdout snapshots or response literals are accepted without
schema, fixture, CLI contract, API contract, or domain source.

Rewrite: assert documented fields, status/exit code, error envelope, and
semantically relevant values with contract provenance.

### `rust.I-HC-B2` -- transport stub claimed as provider coverage

Applies to: integration

Detection: `mockito`, `wiremock`, or a hand-written HTTP/TCP stub returns the
whole provider response while the test claims out-of-process provider contract
coverage.

Rewrite: move the test to the consumer unit/integration seam or add real
provider/contract verification.

## Framework-Specific Low-Confidence Smells

### `rust.I-LC-1` -- fixed port or path without collision handling

Applies to: integration

Detection: tests bind a fixed localhost port or write a fixed path under the
repo/workdir.

Rewrite: bind port `0`, use temp directories, or serialize with a documented
reason and cleanup.

### `rust.I-LC-2` -- CLI assertion ignores failure channels

Applies to: integration

Detection: `assert_cmd` checks success but not stdout/stderr, file effects, or
exit-code distinction that the CLI contract exposes.

Rewrite: assert the visible output/effect and distinguish expected failure
codes where relevant.

## Framework-Specific Positive Signals

### `rust.I-POS-1` -- per-test infrastructure ownership

Applies to: integration

Detection: each test owns its transaction, unique resource name, tempdir,
ephemeral port, or container lifecycle.

### `rust.I-POS-2` -- CLI contract assertion

Applies to: integration

Detection: `assert_cmd` or process tests assert exit status, stdout/stderr,
and side effects from a documented CLI contract.

### `rust.I-POS-3` -- provider contract provenance

Applies to: integration

Detection: API assertions cite schema, OpenAPI, Pact, protocol docs, or a
repo-owned fixture that predates the live run.

## Carve-Outs

- Do not flag `mockito`/`wiremock` when the stated seam is the local client's
  outbound request mapping and assertions verify request shape plus local
  behavior.
- Do not flag top-level `tests/*.rs` as E2E solely because Cargo calls them
  integration tests; route by actual boundary.
