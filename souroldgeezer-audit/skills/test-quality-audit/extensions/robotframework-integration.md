# Extension: Robot Framework - integration-rubric addon

Addon to [robotframework-core.md](robotframework-core.md) loaded **only when step 0b selects the integration rubric** for Robot Framework API, database, CLI, service, or out-of-process contract tests.

**Prerequisite:** `robotframework-core.md` must already be loaded. Dispatch signals live there because rubric selection happens before addon loading.

---

## Framework-specific high-confidence integration smells (`robotframework.I-HC-*`)

### `robotframework.I-HC-A1` - RequestsLibrary test asserts only a generic HTTP success

**Applies to:** `integration`

**Detection:** RequestsLibrary `GET` / `POST` / `PUT` / `PATCH` / `DELETE` or `Create Session` flow followed only by `Status Should Be    200`, `Request Should Be Successful`, or `expected_status=200`, with no assertion on response body, headers, schema, idempotency, auth outcome, or downstream state.

**Smell:** the test proves the route did not fail, not that the contract is correct. It misses wrong payloads, wrong resource ownership, partial writes, stale data, and weak auth behavior.

**Example (smell):**
```robotframework
${response}=    GET    ${BASE_URL}/orders/123    expected_status=200
```

**Rewrite (intent):** assert the response contract and the business state that makes the status meaningful.

---

### `robotframework.I-HC-A2` - Database integration test validates seed data instead of SUT behavior

**Applies to:** `integration`

**Detection:** test connects to DatabaseLibrary, runs a query, and asserts only that preloaded rows exist or row count is non-zero, with no preceding SUT action in the test or setup owned by the test.

**Smell:** the test characterizes the fixture database, not the product behavior. It can pass even if the SUT never writes or reads correctly.

**Rewrite (intent):** arrange explicit per-test seed data, perform the product action through its public boundary, then assert the resulting row state.

---

### `robotframework.I-HC-B1` - Contract test mutates a shared environment without idempotent cleanup

**Applies to:** `integration`

**Detection:** test calls a deployed API / CLI / SSH command that creates or updates named resources in a shared environment, but resource names are static and no teardown deletes or restores them.

**Smell:** reruns, parallel workers, and other teams can observe or corrupt the same state. The test result depends on external residue.

**Rewrite (intent):** use per-test resource identifiers, idempotent setup, and teardown that removes or resets exactly what the test created.

---

### `robotframework.I-HC-B2` - Auth contract tests cover only happy-path identity

**Applies to:** `integration`

**Detection:** an API or CLI suite has authenticated success tests but no tests or tags for anonymous, expired token/session, tampered token/session, insufficient scope/role, sufficient scope, or cross-user access where those scenarios are relevant.

**Smell:** authorization bugs usually live in the negative matrix. A suite that only proves "valid user succeeds" leaves the security contract mostly untested.

**Rewrite (intent):** add a small auth matrix at the Robot layer or delegate to lower-level integration tests that exercise the same public boundary.

---

## Framework-specific low-confidence integration smells (`robotframework.I-LC-*`)

### `robotframework.I-LC-1` - `expected_status=any` or broad status acceptance

**Applies to:** `integration`

**Detection:** RequestsLibrary calls with `expected_status=any`, a status variable whose allowed values are not asserted later, or status checks accepting a broad class (`2xx`, `4xx`) without a body/header assertion.

**Why low-confidence:** broad status acceptance can be legitimate for negative tests where the exact error differs by environment. It is a smell when the test never narrows the contract after the call.

**Rewrite (intent):** assert the exact status or assert a stable problem shape / error code after accepting a range.

---

### `robotframework.I-LC-2` - Integration suite depends on execution order

**Applies to:** `integration`

**Detection:** test names or bodies imply ordered CRUD chaining (`Create`, `Update`, `Delete`) over the same static ID, or later tests read variables/resources created only by earlier tests.

**Why low-confidence:** some systems require expensive setup and intentionally stage scenarios. The suite should still disclose the order dependency and isolate it from parallel runs.

**Rewrite (intent):** make each test arrange its own state, or collapse the ordered flow into one explicitly named journey test evaluated under the E2E or integration sub-lane B scope.

---

## Framework-specific integration positive signals (`robotframework.I-POS-*`)

### `robotframework.I-POS-1` - Contract assertion includes status, body shape, and domain invariant

**Applies to:** `integration`

**Detection:** RequestsLibrary or custom API library test asserts status plus at least one stable response field/schema/header and one domain invariant, such as ownership, idempotency, validation error code, or persisted state.

**Why positive:** the test proves the contract a consumer relies on, not just transport success.

---

### `robotframework.I-POS-2` - Per-test external resource lifecycle

**Applies to:** `integration`

**Detection:** test creates resources with per-test IDs and has teardown that deletes them, rolls back database state, removes files, closes sessions, or resets external service state.

**Why positive:** clean lifecycle makes Robot integration suites safe for reruns, selective execution, and parallel workers.

---

## Auth matrix enumeration

Consumed by [SKILL.md § Auth matrix enumeration](../SKILL.md#auth-matrix-enumeration) in deep mode when Robot integration tests exercise an authenticated API or CLI boundary.

### Protected endpoint / command detection

Robot tests cannot enumerate server-side auth declarations by themselves. Use the SUT language extension when available. If no SUT extension is loaded, infer a Robot-side auth matrix only from tests that call endpoints or commands containing auth signals: `Authorization`, `Bearer`, `Cookie`, `Login`, `Token`, `Session`, `Role`, `Scope`, `Forbidden`, `Unauthorized`, or tags `auth` / `security`.

### Matrix columns

Use the core columns: `anonymous`, `token-expired`, `token-tampered`, `insufficient-scope`, `sufficient-scope`, `cross-user`. Add `not-before`, `wrong-issuer`, `wrong-audience`, `wrong-token-type`, `revoked-token`, `logout-invalidated`, `idle-timeout`, `session-rotation`, `session-fixation`, `csrf-missing`, `csrf-invalid`, and `admin-only` only when the endpoint, suite, tags, fixtures, or loaded SUT extension make those cells applicable.

### Cross-reference matching

A Robot test covers a cell when the test name, tags, or body names the scenario and asserts the expected status / error / visible result, cookie/session mutation, redirect, or blocked state. A setup keyword that silently changes identity without the test naming the scenario is not enough. A table with only valid credentials, `200` / `OK`, or "login succeeds" rows is `referenced-weak` for every negative cell.

### Output

Emit `Gap-AuthZ` rows with **medium** confidence when inferred from Robot tests alone. Upgrade to **high** only when a SUT extension enumerates the protected endpoint and Robot tests are the declared contract layer.

---

## Migration upgrade-path enumeration

Robot Framework does not enumerate migration classes. Use the SUT language extension's migration-upgrade procedure when available. If only Robot Framework is detected, skip this step and state that the extension has no migration source pattern.
