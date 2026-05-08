# Java E2E Addon

Loaded after `java-core.md` when `SKILL.md` selects the E2E rubric.

## Sources

Use Playwright Java docs for Playwright fixture facts:
https://playwright.dev/java/docs/junit

Use Selenium project documentation for WebDriver facts:
https://www.selenium.dev/documentation/webdriver/

## Detection Signals

- Playwright Java imports, `@UsePlaywright`, `Page`, `Browser`,
  `BrowserContext`, `Locator`, or Playwright assertions.
- Selenium imports, `WebDriver`, `WebElement`, `By`, `WebDriverWait`, browser
  driver setup, or Selenium Grid/cloud-browser configuration.
- JUnit/TestNG tags/groups or project names containing `e2e`, `end-to-end`,
  `browser`, `ui`, `journey`, `a11y`, `perf`, or `security`.

## Framework-Specific E2E Smells

### `java.E-HC-F1` - fixed sleep instead of browser-observable wait

Applies to: e2e

Detection: `Thread.sleep`, `TimeUnit.sleep`, or arbitrary timeout waits appear
before checking browser state.

Rewrite: use Playwright web assertions, locator waits, or Selenium explicit
waits tied to a user-visible state.

### `java.E-HC-F2` - selector-only assertion has no user-visible oracle

Applies to: e2e

Detection: assertion checks only CSS/XPath presence, element count, or raw DOM
implementation detail with no accessible/user-visible state or domain result.

Rewrite: assert role/name text, page state, URL transition, form result,
visible error, persisted effect, or domain outcome.

### `java.E-HC-F3` - browser/session state leaks between tests

Applies to: e2e

Detection: browser context, cookies, local storage, authenticated session, or
server-side test account is reused across tests without reset.

Rewrite: create an isolated browser context/page per test or reset both browser
and server state before each scenario.

### `java.E-HC-F4` - E2E only repeats a cheaper integration assertion

Applies to: e2e

Detection: browser test visits a route and asserts status/title/heading only
for behavior already covered by a cheaper API or unit test, with no user
journey value.

Rewrite: move the check down a layer or extend the browser test to prove the
user-observable workflow that cheaper tests cannot prove.

### `java.E-HC-S1` - session lifecycle test omits invalidation proof

Applies to: e2e

Detection: login/logout or auth browser test asserts navigation only, without
checking old session reuse, protected-route denial, cookie/session invalidation,
or role isolation.

Rewrite: assert that the previous session cannot return to protected state and
that the UI/API reports the expected signed-out or unauthorized outcome.

### `java.E-HC-P1` - performance assertion uses one local timestamp

Applies to: e2e

Detection: test measures a single wall-clock duration around browser actions
without a budget source, warmup, network/runtime control, or browser metric.

Rewrite: use project performance budgets, browser metrics, trace evidence, or a
dedicated performance lane with controlled environment disclosure.

### `java.E-LC-1` - broad browser smoke test

Applies to: e2e

Detection: test opens the app, asserts title/URL, and stops, while claiming a
feature journey.

Rewrite: assert the visible workflow outcome and any state change the user
story requires.

### `java.E-POS-1` - isolated Playwright fixture with web assertion

Applies to: e2e

Detection: Playwright Java supplies isolated `Page`/`BrowserContext` fixtures
and the test uses web assertions over user-visible state.

### `java.E-POS-2` - Selenium explicit wait plus visible outcome

Applies to: e2e

Detection: Selenium waits on a user-visible condition and then asserts visible
text, route, form result, or domain state.

### `java.E-POS-3` - browser auth/session negative path

Applies to: e2e

Detection: test covers successful auth plus denied access, logout invalidation,
role mismatch, or session expiry in a browser-visible way.

## Sub-Lane Notes

- Functional (`F`) owns browser journey proof and user-visible workflow state.
- Accessibility (`A`) owns accessibility-specific tags, axe-style checks,
  keyboard/focus behavior, and semantic role/name evidence.
- Performance (`P`) owns browser timing, budgets, and environment disclosure.
- Security (`S`) owns browser-visible auth, session, cookie, CSP, CORS, CSRF,
  or tampered-state behaviors.

## Carve-Outs

- Do not flag a raw locator when it is immediately followed by a role/name,
  visible text, URL, domain-state, or accessibility assertion that proves the
  user-facing outcome.
- Do not require Java E2E tests for every route; prefer cheaper tests unless
  the behavior needs real browser rendering, navigation, storage, or session
  semantics.
