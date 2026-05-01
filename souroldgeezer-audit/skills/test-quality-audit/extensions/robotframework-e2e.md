# Extension: Robot Framework - E2E-rubric addon

Addon to [robotframework-core.md](robotframework-core.md) loaded **only when step 0b selects the E2E rubric** for Robot Framework browser, web, or mobile suites.

**Prerequisite:** `robotframework-core.md` must already be loaded. The test-type detection signals that route a test to E2E live in `robotframework-core.md` because dispatch happens before rubric selection.

**Note on procedures not applicable to E2E:** `robotframework-core.md` declares a Robot-level mutation skip and non-E2E determinism verification. Per [SKILL.md § Mutation testing (conditional)](../SKILL.md#mutation-testing-conditional) and [SKILL.md § Determinism verification](../SKILL.md#determinism-verification), those procedures do not run against E2E targets.

---

## Sub-lane classification hints

Core [SKILL.md § 0b step 5](../SKILL.md#0b-select-the-rubric) already lists canonical sub-lane routing signals. Robot-specific refinements:

- **Tags are primary.** `[Tags]    a11y`, `[Tags]    perf`, `[Tags]    security`, and `Test Tags` equivalents are strong sub-lane signals when the test body matches the tag.
- **Accessibility.** Axe-style libraries, accessibility audit keywords, focus-order checks, keyboard-only navigation, aria-label assertions, or screen-reader name assertions -> sub-lane A.
- **Performance.** Browser timing / Web Vitals / Lighthouse-style keywords, page-load budgets, or explicit elapsed-time assertions -> sub-lane P.
- **Security.** Login/session/cookie/token tampering, CSP / CORS / frame assertions, cross-user data isolation, or role/scope assertions -> sub-lane S.
- **Functional.** Browser / mobile journeys without A/P/S-specific signals -> sub-lane F.

---

## Framework-specific high-confidence E2E smells (`robotframework.E-HC-*`)

### `robotframework.E-HC-F1` - Raw locator path is the only user contract

**Applies to:** `e2e` - sub-lane F.

**Detection:** Browser / SeleniumLibrary / AppiumLibrary tests use only raw CSS, XPath, generated IDs, dynamic class names, or positional locators for key interactions and assertions, with no text, role, label, title, accessibility id, or visible business-state assertion in the same test.

**Smell:** the test is coupled to the current DOM/app structure instead of the user-observable behavior. A markup or layout refactor breaks the test without changing the product.

**Example (smell):**
```robotframework
Click Element    xpath=//div[3]/button[2]
Element Should Be Visible    css=.toast-success
```

**Rewrite (intent):** prefer role/text/label/accessibility-id locators where the library supports them, then assert the visible state or domain outcome that users rely on.

---

### `robotframework.E-HC-F2` - Click-through journey ends before a stable waypoint

**Applies to:** `e2e` - sub-lane F.

**Detection:** final test step is a click/tap/navigation/input keyword or fixed wait, with no following condition-based assertion such as visible text, URL, element state, page title, app state, API side effect, or domain confirmation.

**Smell:** the test may finish while the app is still transitioning. It proves the automation command returned, not that the journey completed.

**Rewrite (intent):** finish each journey at a stable user waypoint and assert that waypoint with a condition-based keyword.

---

### `robotframework.E-HC-S1` - Auth/security E2E test reuses authenticated state across negative cases

**Applies to:** `e2e` - sub-lane S.

**Detection:** security-tagged suite uses a shared browser/session from suite setup, then tests anonymous, expired, tampered, or cross-user cases without creating a fresh context/session or clearing cookies/storage between cases.

**Smell:** residual auth state can make negative security tests pass for the wrong reason or fail only by order.

**Rewrite (intent):** create a fresh browser context/session per security case, seed only the required auth state, and assert both the blocked action and the resulting user-visible state.

---

## Framework-specific low-confidence E2E smells (`robotframework.E-LC-*`)

### `robotframework.E-LC-F1` - `Sleep` used as synchronization

**Applies to:** `e2e` - sub-lane F.

**Detection:** `Sleep    <duration>` in a Browser / SeleniumLibrary / AppiumLibrary test body, especially between action and assertion keywords.

**Why low-confidence:** fixed waits are flaky and slow, but a small number can be legitimate for non-observable effects such as analytics debounce. Flag with context instead of treating every sleep as a blocker.

**Rewrite (intent):** use condition-based waits: Browser `Wait For Elements State`, SeleniumLibrary `Wait Until Element Is Visible` / `Wait Until Page Contains Element`, Appium visibility/state waits, or a project-specific keyword that waits for a published UI state.

---

### `robotframework.E-LC-F2` - Page-object keyword hides the wait/assert contract

**Applies to:** `e2e` - sub-lane F.

**Detection:** high-level page keyword such as `Submit Login Form` or `Open Account Settings` wraps clicks/navigation but neither the keyword body nor the test body contains a condition-based wait/assertion.

**Why low-confidence:** page-object keywords are good when they hide mechanics, but the audit still needs evidence that the keyword waits for a stable state.

**Rewrite (intent):** make page keywords return at a stable waypoint or pair every action keyword with a visible-state assertion in the calling test.

---

## Framework-specific E2E positive signals (`robotframework.E-POS-*`)

### `robotframework.E-POS-F1` - User-facing locator strategy

**Applies to:** `e2e` - sub-lane F and A.

**Detection:** Browser / Playwright-style role, text, label, title, placeholder, or alt-text locators; SeleniumLibrary locators built from visible text / labels where stable; Appium accessibility IDs for mobile controls.

**Why positive:** user-facing locators double as accessibility and usability checks. They survive DOM/app refactors better than generated IDs, dynamic classes, or positional XPath.

---

### `robotframework.E-POS-F2` - Condition-based wait or assertion after each asynchronous action

**Applies to:** `e2e` - sub-lane F.

**Detection:** action steps are followed by Browser `Wait For Elements State` / state assertions, SeleniumLibrary `Wait Until ...` / `Element Should ...` / `Page Should ...`, or equivalent Appium wait/assertion keywords tied to a user-visible condition.

**Why positive:** condition-based waits make the suite synchronize on product state instead of runner timing. This directly counters `robotframework.E-LC-F1`.

---

### `robotframework.E-POS-S1` - Fresh session per security case

**Applies to:** `e2e` - sub-lane S.

**Detection:** security tests create a new browser context/session or explicitly clear cookies/storage before each auth scenario, then assert the visible blocked/allowed outcome.

**Why positive:** auth and cross-user E2E tests are only trustworthy when state cannot leak from a previous case.

---

### `robotframework.E-POS-A1` - Accessibility scan or keyboard path anchored to a stable page state

**Applies to:** `e2e` - sub-lane A.

**Detection:** test waits for a stable page waypoint, runs an accessibility scan or keyboard-only navigation path, and asserts no violations or a concrete focus/label outcome.

**Why positive:** accessibility checks at the Robot E2E layer catch rendered issues that keyword-layer or unit tests cannot see.
