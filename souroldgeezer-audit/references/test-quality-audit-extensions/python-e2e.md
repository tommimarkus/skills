# Python E2E Addon

Loaded after `python-core.md` when `SKILL.md` step 0b selects the E2E rubric.

## Detection Signals

- Playwright Python imports from `playwright.sync_api` or
  `playwright.async_api`.
- Selenium imports from `selenium.webdriver`.
- pytest fixtures named `page`, `browser`, `context`, `driver`, or
  `live_server` combined with browser navigation.
- Tags or names for `e2e`, `browser`, `ui`, `journey`, `a11y`, `perf`, or
  `security` on tests that drive a real browser.

## E2E Sub-Lane Signals

- `A` accessibility: axe, pa11y, accessibility tags, keyboard/focus assertions,
  WCAG references.
- `P` performance: Web Vitals, browser performance APIs, Lighthouse, resource
  or transfer-size budgets.
- `S` security: browser-enforced CSP/CORS/frame/cookie/session checks,
  tampered cookies, cross-user navigation.
- `F` functional: default for browser journeys without the above signals.

## Framework-Specific High-Confidence Smells

### `python.E-HC-F1` — locator bypasses user-facing semantics

Applies to: e2e

Detection: Playwright `locator("css...")`, Selenium CSS/XPath selectors, or
test ids are used where role/label/text locators are available.

Rewrite: use Playwright role/text/label locators or Selenium helpers that bind
to accessible names or visible labels.

### `python.E-HC-F2` — browser session fixture shared across tests

Applies to: e2e

Detection: module/session-scoped `page`, `context`, `driver`, cookies, storage
state, or logged-in browser session mutates across tests.

Rewrite: create a fresh context/session per test or prove the fixture is
immutable.

### `python.E-HC-F3` — waiting by sleeps

Applies to: e2e

Detection: `time.sleep`, fixed `wait_for_timeout`, Selenium implicit sleeps,
or retry loops that wait for elapsed time rather than observable state.

Rewrite: use web-first assertions, explicit waits on visibility/URL/response,
or condition predicates.

### `python.E-HC-S1` — header-only browser security test

Applies to: e2e

Detection: browser test asserts CSP/CORS/cookie/frame headers without checking
browser enforcement.

Rewrite: move header value checks to integration or add a browser-enforcement
assertion.

## Framework-Specific Low-Confidence Smells

### `python.E-LC-1` — page object hides journey outcome

Applies to: e2e

Detection: page object method chains click/type/navigate steps while the test
only asserts that the helper returned.

Rewrite: keep low-level mechanics in page objects but assert user-observable
outcomes in the test.

## Framework-Specific Positive Signals

### `python.E-POS-1` — web-first assertion

Applies to: e2e

Detection: Playwright `expect(locator).to_*`, Selenium explicit waits with
state predicates, or equivalent condition-based browser assertions.

### `python.E-POS-2` — per-test browser context

Applies to: e2e

Detection: each test owns its browser context/session and state setup.

### `python.E-POS-3` — failure diagnostics only

Applies to: e2e

Detection: screenshot, trace, console, network, or DOM capture occurs only on
failure and is not used as assertion substrate.

## Carve-Outs

- Do not flag `data-testid` when the element has no stable accessible name and
  the test also asserts a user-observable outcome.
- Do not flag failure-only screenshot or trace capture as snapshot testing.
- Do not route HTTP-only tests using `requests` or `httpx` to E2E; they belong
  in integration sub-lane B unless a browser is driven.
