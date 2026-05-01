# Extension: Robot Framework - unit-rubric addon

Addon to [robotframework-core.md](robotframework-core.md) loaded **only when step 0b selects the unit rubric** for Robot Framework keyword-layer tests.

**Prerequisite:** `robotframework-core.md` must already be loaded. Dispatch signals live there because rubric selection happens before addon loading.

---

## Framework-specific high-confidence smells (unit-only)

### `robotframework.HC-U1` - Resource keyword test reuses the production keyword as its oracle

**Applies to:** `unit`

**Detection:** the SUT is a user keyword or custom library keyword, and the test asserts by calling another high-level keyword from the same resource layer that uses the SUT internally, instead of asserting a returned value, variable, emitted event, or fake dependency state.

**Smell:** the test verifies the keyword layer with the keyword layer. A refactor that preserves behavior but rearranges resource keywords can fail the test, while a shared bug in both keywords still passes.

**Example (smell):**
```robotframework
*** Test Cases ***
Discount Is Applied
    Apply Discount    ${cart}
    Cart Should Have Discount    ${cart}
```

If `Cart Should Have Discount` calls `Apply Discount` again or reads only the same internal scratch variable, the oracle is not independent.

**Rewrite (intent):** use a fake library or direct returned value from the keyword under test, then assert the expected domain state without reusing the same production keyword path.

---

### `robotframework.HC-U2` - Keyword unit test depends on a live external library

**Applies to:** `unit`

**Detection:** a test classified as unit imports Browser, SeleniumLibrary, AppiumLibrary, RequestsLibrary, DatabaseLibrary, SSHLibrary, or Process and calls those libraries while claiming to test a resource keyword in isolation.

**Smell:** the test is not a unit test. It has external timing, infrastructure, and selector contracts, so the unit rubric will understate cost and flake risk.

**Rewrite (intent):** route the test to integration or E2E, or inject a fake library / variable-bound adapter so the keyword's branching and output contract can be tested without the external boundary.

---

## Framework-specific low-confidence smells (unit-only)

### `robotframework.LC-U1` - Private helper keyword tested as a public contract

**Applies to:** `unit`

**Detection:** test cases directly call keywords named `_Internal*`, `Internal *`, `Helper *`, `Build * Locator`, `Click Raw *`, or similar implementation helpers, with no repo guidance declaring those keywords public.

**Why low-confidence:** some teams intentionally test reusable helper resources. Without that convention, direct helper tests pin the implementation decomposition of higher-level keywords.

**Rewrite (intent):** test the public resource keyword that owns the behavior, or document the helper as a reusable public keyword and give it a stable contract.

---

## Framework-specific positive signals (unit-only)

### `robotframework.POS-U1` - Fake library injected through import arguments or variables

**Applies to:** `unit`

**Detection:** the suite imports a fake/in-memory library or resource through `Library    ${LIBRARY}` / import arguments / test variables, and the test asserts the keyword output or fake library state after executing the SUT keyword.

**Why positive:** Robot keyword code often wraps external libraries. A fake adapter lets the suite prove keyword behavior without browser, API, database, or process flake.

---

### `robotframework.POS-U2` - Keyword contract tested at the keyword boundary

**Applies to:** `unit`

**Detection:** each unit test calls one public keyword under test, passes fixed arguments, and asserts one documented output: return value, variable mutation, log/event emitted through a fake, or error raised via `Run Keyword And Expect Error`.

**Why positive:** the test is derived from the keyword's contract rather than from its internal calls, so resource refactors remain cheap.
