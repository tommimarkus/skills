# Java Integration Addon

Loaded after `java-core.md` when `SKILL.md` selects the integration rubric.

## Detection Signals

- Maven Failsafe, `*IT.java`, `*ITCase.java`, Gradle `integrationTest` source
  set/task, or suite tags/groups named `integration`, `contract`, `api`,
  `database`, `messaging`, or `migration`.
- Testcontainers `@Testcontainers` / `@Container`, JDBC/DataSource connections,
  migrations, HTTP clients against localhost/deployed services, local server
  startup, WireMock/MockWebServer, REST Assured, servlet/resource harnesses, or
  framework app-context bootstrapping.

## Framework-Specific Integration Smells

### `java.I-HC-A1` - integration test mocks the owned in-process boundary

Applies to: integration

Detection: a test routed to integration still uses Mockito to replace an
in-repo service/repository/adapter that the integration boundary claims to
exercise.

Rewrite: use the real owned boundary and fake only external processes,
protocols, or infrastructure.

### `java.I-HC-A2` - Testcontainers state leaks between tests

Applies to: integration

Detection: shared/static `@Container`, singleton container, database, topic, or
bucket is mutated by tests without per-test cleanup, unique resource names, or
transactional reset.

Rewrite: reset state per test, use isolated schemas/resources, or move the
shared container to read-only fixture setup.

### `java.I-HC-A3` - parallel execution with unsafe shared container fixture

Applies to: integration

Detection: JUnit/Gradle/TestNG parallel execution is enabled while tests share
mutable Testcontainers resources, ports, databases, files, or static clients.

Rewrite: disable parallelism for the shared fixture, isolate resources per
test, or prove thread-safe setup with explicit cleanup.

### `java.I-HC-B1` - HTTP contract assertion only checks success status

Applies to: integration

Detection: REST Assured, Java HTTP client, servlet harness, or framework test
client asserts only `200`, `201`, `204`, or a truthy response for a value-bearing
endpoint.

Rewrite: assert response shape, headers, error partitions, idempotency, auth
matrix, and domain state relevant to the contract.

### `java.I-HC-B2` - external environment contract lacks ownership evidence

Applies to: integration

Detection: test calls staging, sandbox, partner, or shared deployed URL but does
not name the owned fixture, schema version, auth role, cleanup, or contract
source.

Rewrite: bind the test to an owned test environment or record the external
contract, version, and cleanup limits in the audit evidence.

### `java.I-LC-1` - migration path is not exercised

Applies to: integration

Detection: tests start from the latest schema/changelog only, while the changed
SUT includes migrations or schema compatibility behavior.

Rewrite: add upgrade-path tests from a previous schema/data state to the new
state and assert preserved data plus new constraints.

### `java.I-LC-2` - transaction rollback hides committed behavior

Applies to: integration

Detection: a framework transaction rolls back every test while the contract is
about committed rows, events, locks, triggers, or idempotency.

Rewrite: assert committed behavior in a per-test isolated resource, or state
that rollback-only coverage is weaker.

### `java.I-POS-1` - per-test adjacent dependency fixture

Applies to: integration

Detection: container/database/broker/filesystem fixture is owned per test or
reset deterministically before assertions.

### `java.I-POS-2` - auth and role matrix covers negative partitions

Applies to: integration

Detection: suite covers anonymous, wrong role/scope, valid role/scope, and
invalid/expired credential outcomes for the same boundary.

### `java.I-POS-3` - migration upgrade path is asserted

Applies to: integration

Detection: test seeds an old schema/data version, runs the migration path, and
asserts both preserved old behavior and new constraints.

## Auth Matrix Enumeration

Deep mode should enumerate Java integration surfaces with auth or session
semantics:

- anonymous / missing credential;
- authenticated but missing role/scope;
- valid role/scope;
- expired, malformed, or revoked credential when the contract exposes it;
- tenant or ownership mismatch when data boundaries are tenant-scoped.

Happy-path-only tests are `referenced-weak` for `Gap-AuthZ`.

## Migration Enumeration

Deep mode should inspect migration tools, changelog files, generated DDL, and
test setup. Static references to latest schema objects do not prove upgrade
coverage. Treat upgrade/downgrade or compatibility gaps as probable until a
test exercises old data through the migration path.

## Carve-Outs

- Do not require Java integration tests for a route already strongly covered by
  a test-artifact extension such as Robot Framework, provided the test asserts
  stable status, body, auth, and domain outcomes.
- Do not flag Testcontainers static containers when their contents are read-only
  or reset before every test method.
- Do not flag WireMock/MockWebServer by itself. It is a useful boundary fake
  when the asserted behavior is the Java client's outbound protocol contract.
