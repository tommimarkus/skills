# Rust E2E Addon

Loaded after `core.md` when `SKILL.md` selects the E2E rubric.

## Detection Signals

- Browser automation through `thirtyfour`, `fantoccini`, `chromiumoxide`,
  `headless_chrome`, WebDriver sessions, or browser-driven `wasm-bindgen-test`.
- Tests or runner profiles named `e2e`, `browser`, `ui`, `journey`, `a11y`,
  `perf`, or `security` that drive a real browser.

## E2E Sub-Lane Signals

- `A` accessibility: axe/ARIA/focus/keyboard checks or accessibility tags.
- `P` performance: browser timing APIs, resource budgets, or Web Vitals-style
  assertions.
- `S` security: browser-enforced CSP/CORS/frame/cookie/session behavior,
  tampered cookies, or cross-user navigation.
- `F` functional: default for browser journeys without the above signals.

## Framework-Specific High-Confidence Smells

### `rust.E-HC-F1` -- locator bypasses user-facing semantics

Applies to: e2e

Detection: CSS/XPath selectors or DOM IDs are used where role, label, text, or
visible-name locators are available.

Rewrite: prefer user-facing locators and assert the visible outcome.

### `rust.E-HC-F2` -- shared browser session mutates across tests

Applies to: e2e

Detection: browser, driver, cookies, local storage, or logged-in state is shared
across tests and mutated by the journey.

Rewrite: create a fresh browser context/session per test or prove the shared
fixture is immutable.

### `rust.E-HC-F3` -- waiting by elapsed time

Applies to: e2e

Detection: sleeps, fixed timeout waits, or retry loops wait for duration rather
than observable browser state.

Rewrite: wait for URL, visible text, network response, enabled control, or a
domain-specific condition.

### `rust.E-HC-S1` -- header-only browser security test

Applies to: e2e

Detection: browser test checks CSP/CORS/cookie/frame headers without observing
browser enforcement.

Rewrite: move header checks to integration or add enforcement behavior in the
browser.

## Framework-Specific Low-Confidence Smells

### `rust.E-LC-1` -- helper hides journey outcome

Applies to: e2e

Detection: page/helper methods perform navigation and assertions while the test
body only checks helper completion.

Rewrite: keep mechanics in helpers and assert user-observable outcomes in the
test.

## Framework-Specific Positive Signals

### `rust.E-POS-1` -- condition-based browser assertion

Applies to: e2e

Detection: waits/assertions bind to visible state, URL, response, accessibility
tree, or domain event rather than time.

### `rust.E-POS-2` -- per-test browser context

Applies to: e2e

Detection: each test owns browser session, cookies/storage, and teardown.

### `rust.E-POS-3` -- failure-only diagnostics

Applies to: e2e

Detection: screenshots, logs, traces, or DOM captures are produced on failure
and are not used as the assertion substrate.

## Carve-Outs

- Do not route CLI black-box tests to E2E unless they drive a real user-facing
  external journey; most CLI process tests belong in integration.
- Do not flag test IDs when the element has no stable accessible name and the
  test still asserts a user-visible outcome.
