# Python Integration Addon

Loaded after `python-core.md` when `SKILL.md` step 0b selects the integration
rubric.

## Detection Signals

- Web/application clients: FastAPI or Starlette `TestClient`, `httpx.AsyncClient`
  against ASGI apps, Flask `app.test_client()`, Django `Client` /
  `APIClient`, or live service calls through `requests` / `httpx`.
- Real adjacent dependencies: SQLAlchemy sessions, Django database fixtures,
  Alembic/Django migrations, Redis, queues, filesystem persistence, or
  Testcontainers.
- Contract tests against deployed/local HTTP services without browser use.

## Framework-Specific High-Confidence Smells

### `python.I-HC-A1` — database fixture shared without transaction or unique keys

Applies to: integration

Detection: tests use module/session-scoped database state, global factories, or
seed rows without per-test transaction rollback or unique identifiers.

Rewrite: use per-test factories, transactions, truncation, or unique tenant/key
scoping.

### `python.I-HC-A2` — web app dependency override leaks across tests

Applies to: integration

Detection: FastAPI `dependency_overrides`, Flask app config, Django settings,
or monkeypatched app dependencies are mutated and not restored per test.

Rewrite: scope overrides with fixtures that clean up in `finally` blocks.

### `python.I-HC-B1` — contract expected response pasted from live run

Applies to: integration

Detection: full JSON response literal or snapshot has no OpenAPI, schema,
consumer pact, fixture, or documented domain source.

Rewrite: assert documented fields and status/error envelope with schema or
consumer provenance.

### `python.I-HC-B2` — transport stub replaces the service boundary under test

Applies to: integration

Detection: `responses`, `respx`, `requests_mock`, or monkeypatched transport
returns the entire downstream response in a test claiming out-of-process
contract coverage.

Rewrite: move to unit lane or replace with consumer/provider contract coverage.

## Framework-Specific Low-Confidence Smells

### `python.I-LC-1` — client fixture hides app startup behavior

Applies to: integration

Detection: `client` fixture constructs app, dependencies, database, and seed
data with no visible scope in the test.

Rewrite: keep app/client setup in fixtures but make test-specific data and seam
intent visible in each test.

### `python.I-LC-2` — filesystem integration without cleanup proof

Applies to: integration

Detection: test writes outside `tmp_path` / temporary directory fixtures or
uses fixed filenames under the repo/workdir.

Rewrite: use per-test temporary directories and assert cleanup when cleanup is
part of the contract.

## Framework-Specific Positive Signals

### `python.I-POS-1` — per-test database ownership

Applies to: integration

Detection: transaction rollback, unique keys, isolated schema/database, or
factory-created rows owned by the test.

### `python.I-POS-2` — app dependency override cleanup

Applies to: integration

Detection: fixture scopes app overrides and restores them after each test.

### `python.I-POS-3` — contract assertion cites schema

Applies to: integration

Detection: status codes, problem details, response schema, OpenAPI fragment, or
consumer expectations are cited in the test or fixture.

## Auth Matrix Enumeration

For Python web APIs, auth matrix enumeration applies when route handlers or
middleware declare auth dependencies:

- FastAPI / Starlette: `Depends(...)` auth dependencies, security schemes, or
  middleware guarding routes.
- Django: `login_required`, permission classes, DRF authentication/permission
  classes.
- Flask: auth decorators or middleware guarding routes.

Minimum cells: `anonymous`, `token-expired`, `token-tampered`,
`insufficient-scope`, `sufficient-scope`, and `cross-user`. Add
scheme-specific cells when the app exposes them: `not-before`,
`wrong-issuer`, `wrong-audience`, `wrong-token-type`, `revoked-token`,
`logout-invalidated`, `idle-timeout`, `session-rotation`,
`session-fixation`, `csrf-missing`, and `csrf-invalid`.

A Python test covers a cell only when it arranges that auth/session state and
asserts the documented status, response envelope, redirect, cookie mutation, or
visible blocked state. A client call that only sends a valid token and asserts
success is `referenced-weak` for every negative auth cell. Report uncovered
cells as `Gap-AuthZ`.

## Migration Upgrade-Path Enumeration

When Alembic or Django migrations are in scope, each migration needs a test
that names the revision/class/file, seeds representative prior-schema data, and
asserts post-migration state. Empty-database migration smoke tests do not
count as upgrade-path coverage.

## Carve-Outs

- Do not flag FastAPI/Django/Flask test clients as E2E unless a browser is
  actually driven.
- Do not flag dependency overrides as mocks when the test's stated seam is app
  routing/model binding/auth pipeline and the override stands outside that
  seam.
