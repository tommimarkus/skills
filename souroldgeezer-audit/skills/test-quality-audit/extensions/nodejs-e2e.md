# Extension: Node.js / TypeScript — E2E-rubric addon

Addon to [nodejs-core.md](nodejs-core.md) loaded **only when step 0b selects the E2E rubric**. Playwright-primary: most smells and positive signals target the Playwright JS / TS API. Cypress and WebdriverIO are covered as one-line carve-outs and direct analogs; full Cypress / WebdriverIO coverage is deferred to future `cypress-*.md` / `wdio-*.md` extensions.

**Prerequisite:** `nodejs-core.md` must already be loaded. The test-type detection signals that route a test to the E2E rubric (`@playwright/test`, `cypress`, `webdriverio`, `puppeteer` imports; `playwright.config.*` / `cypress.config.*` / `wdio.conf.*` files) live in `nodejs-core.md` because dispatch happens before rubric selection.

**Note on procedures not applicable to E2E:** `nodejs-core.md` declares the Stryker JS mutation tool, SUT surface enumeration, and determinism verification. Per [SKILL.md § Mutation testing (conditional)](../SKILL.md#mutation-testing-conditional) and [SKILL.md § Determinism verification](../SKILL.md#determinism-verification), those procedures **do not apply to E2E audit targets** — the SUT for an E2E test is the whole deployed stack driven through a browser, and neither mutation testing nor determinism rerun is meaningful against that target. The audit agent must skip those steps when the selected rubric is E2E.

---

## Sub-lane classification hints

Core [SKILL.md § 0b step 5](../SKILL.md#0b-select-the-rubric) already lists the canonical sub-lane routing signals (axe imports → A, Web Vitals / `PerformanceObserver` → P, CSP / cookie-jar assertions → S, default F).

Node-ecosystem refinements:

- **Playwright tags** — the `@playwright/test` tag system is the idiomatic per-test sub-lane marker (see https://playwright.dev/docs/test-annotations#tag-tests). Use the `details` argument:
  - Per-test: `test('title', { tag: '@a11y' }, async ({ page }) => { ... })` or `test('title', { tag: ['@a11y', '@smoke'] }, ...)`.
  - Per-describe: `test.describe('group', { tag: '@a11y' }, () => { ... })`.
  - In-title: a `@a11y` token anywhere in the test title also counts (`test('test keyboard nav @a11y', ...)`).
  - `@a11y` → sub-lane A; `@perf` → P; `@security` → S. (`test.describe.configure(...)` controls `mode` / `retries` / `timeout` but not tags; do not confuse it with the tag system.)
- **`@axe-core/playwright` / `cypress-axe` / `axe-core` import** — sub-lane A regardless of tag presence.
- **`web-vitals` npm package / `lighthouse` import / `PerformanceObserver` inside a `page.evaluate` call** — sub-lane P.
- **`page.context().addCookies(...)` with tampered-value tests / CSP header assertions with browser-enforcement checks** — sub-lane S.
- **Visual regression libraries (`@playwright/test`'s built-in `expect(page).toHaveScreenshot()`, `jest-image-snapshot`, `pixelmatch`)** — sub-lane F with a pinned-output smell (`E-HC-F8`).

---

## Framework-specific high-confidence E2E smells (`nodejs.E-HC-*`)

*(No framework-specific HC entries yet. Playwright / Cypress / WebdriverIO patterns that widely trigger `E-HC-F*` already have sharp core detection; add Node-specific refinements here as real audits surface them — e.g. a Cypress-specific variant of `E-HC-F2` that targets `cy.get('.some-class')` without a `cy.findByRole(...)` fallback.)*

---

## Framework-specific low-confidence E2E smells (`nodejs.E-LC-*`)

### `nodejs.E-LC-F1` — `page.waitForTimeout(...)` / `cy.wait(<ms>)` / `browser.pause(...)` fixed-duration wait

**Applies to:** `e2e` — sub-lane F (functional). Refines core `E-HC-F3`.

**Detection:**

- Playwright: `await page\.waitForTimeout\(\s*\d+\s*\)` anywhere in a test body.
- Cypress: `cy\.wait\(\s*\d+\s*\)` (a numeric argument — not `cy.wait('@alias')` which waits on a network intercept).
- WebdriverIO: `await browser\.pause\(\s*\d+\s*\)`.
- Puppeteer: `await page\.waitForTimeout\(\s*\d+\s*\)` — removed in Puppeteer v22 (the method no longer exists on `Page`); tests still using it fail at runtime. Flag together with the recommended replacement (`await new Promise(r => setTimeout(r, ms))` for the rare legitimate case, or a web-observable wait otherwise).

**Why low-confidence:** fixed-duration waits are flaky by construction — they fail on slow CI runners and waste time on fast ones. Playwright's own [timeout docs](https://playwright.dev/docs/test-timeouts) explicitly discourage them ("Discouraged: Never wait for timeout in production. Tests that wait for time are inherently flaky. Use Locator actions and web assertions that wait automatically."). Cypress [`cy.wait` docs](https://docs.cypress.io/api/commands/wait) and [best-practices § Unnecessary Waiting](https://docs.cypress.io/app/core-concepts/best-practices#Unnecessary-Waiting) flag `cy.wait(Number)` as an anti-pattern. Sometimes legitimate when waiting for a non-observable side effect (e.g. a debounced analytics beacon), but rare. Flag with a note; the author can dismiss if the delay is genuinely tied to wall-clock time.

**Rewrite (intent):**
- Playwright: `await expect(locator).toBeVisible()` / `.toHaveText(...)` / `.toHaveURL(...)` web-first assertions retry with a timeout until the condition holds.
- Cypress: `cy.wait('@aliasedIntercept')` (network-triggered) or `cy.findByRole(...)` / `cy.contains(...)` which retry implicitly.
- WebdriverIO: `await $(...).waitForDisplayed({ timeout })` / `browser.waitUntil(() => ..., { timeout })`.

---

## Framework-specific E2E positive signals (`nodejs.E-POS-*`)

### `nodejs.E-POS-F1` — Accessible-name locators (`getByRole`, `getByLabel`, `getByText`, `getByPlaceholder`, `getByAltText`, `getByTitle`)

**Applies to:** `e2e` — sub-lane F (functional) and A (accessibility).

**Detection:**

- Playwright: `page\.getBy(Role|Label|Text|Placeholder|AltText|Title)\(` or `locator\.getBy(Role|Label|Text|Placeholder|AltText|Title)\(`.
- Cypress (with `@testing-library/cypress`): `cy\.findBy(Role|LabelText|Text|PlaceholderText|AltText|Title)\(`.
- WebdriverIO (with its accessibility-locator extensions): `$('aria/<accessible-name>')` or `browser.$('//*[@role="button" and contains(text(), "<name>")]')`.

**Why positive:** locators based on ARIA role, label text, or accessible name double as accessibility checks — if the locator can't find the element, the control is likely unlabelled for assistive tech. Tests stay resilient to CSS / DOM restructuring. Reward under sub-lane F always; under sub-lane A the same pattern is load-bearing because it validates the accessible-name contract.

Playwright's documented locator priority puts these first for exactly this reason. See https://playwright.dev/docs/locators.

---

### `nodejs.E-POS-F2` — Web-first assertions: `expect(locator).to*` with retry semantics

**Applies to:** `e2e` — sub-lane F.

**Detection:**

- Playwright: `await\s+expect\([^)]+\)\.to(BeVisible|BeHidden|BeEnabled|BeDisabled|BeChecked|BeFocused|HaveText|HaveValue|HaveCount|HaveAttribute|HaveClass|HaveURL|HaveTitle|ContainText|BeAttached|BeInViewport)\(` — typically from `import { expect } from '@playwright/test'`.
- Cypress: `cy\.get\(['"]<sel>['"]\)\.should\(['"](be.visible|contain|have.text|have.class|have.attr|have.length|have.value|have.url|not.exist)['"]` — Cypress's `should` chain has the same retry semantics.
- WebdriverIO: `await expect\([^)]+\)\.to(BeDisplayed|HaveText|HaveValue|HaveAttribute|HaveElementClass)` from `@wdio/expect` matchers.

**Why positive:** Playwright's web-first assertions and Cypress's `should` chain retry until the condition is met or the per-assertion timeout expires. Pairing them with accessible-name locators eliminates both locator flake and timing flake — tests describe the target UI state rather than pinning execution order. Counterpart to `nodejs.E-LC-F1`.

---

### `nodejs.E-POS-F3` — Per-test browser context

**Applies to:** `e2e` — sub-lane F, S.

**Detection:**

- Playwright: `test\.use\(\{\s*(storageState|contextOptions)\s*:` at the file or describe-block level (new context per test in the block, seeded from `storageState`), OR `const context = await browser\.newContext\(` in `beforeEach` / a test body with `context.close()` in `afterEach`. `@playwright/test` already creates a fresh `BrowserContext` per test by default — isolation is the default, not the opt-in.
- Cypress: tests that call `cy.clearAllCookies()` + `cy.clearAllLocalStorage()` + `cy.clearAllSessionStorage()` in `beforeEach` OR use `cy.session(id, setup, { validate })` with per-test cache keys. Test-isolation mode (`testIsolation: 'on'`, the default since Cypress v12) already clears cookies / localStorage / sessionStorage between tests in the same spec; the `cy.clearAll*` trio is the explicit opt-in equivalent when isolation is disabled.
- WebdriverIO: `browser.reloadSession()` in `beforeEach` OR a dedicated session factory per test.

**Why positive:** a per-test context isolates cookies, storage, and auth state between tests. Suites that share a single context across tests bleed state and mask order-dependency bugs; a per-test context removes that whole class of flake. Especially valuable under sub-lane S (security) where cross-test cookie leaks invalidate auth assertions.

Playwright's `test.use({ storageState: 'playwright/.auth/user.json' })` pattern is the documented way to share auth across tests while keeping per-test cookies fresh — each test's context is re-seeded from the stored state, not literally reused. See https://playwright.dev/docs/auth#reuse-signed-in-state.

---

### `nodejs.E-POS-A1` — `@axe-core/playwright` with per-page scan + violations assertion

**Applies to:** `e2e` — sub-lane A (accessibility).

**Detection:** `import AxeBuilder from '@axe-core/playwright'` plus `const results = await new AxeBuilder({ page })\.<chain>\.analyze\(\)` followed by an assertion on `results\.violations` — typically `expect(results.violations).toEqual([])`. For Cypress: `import 'cypress-axe'` plus `cy.injectAxe()` + `cy.checkA11y(...)`.

**Why positive:** axe-core coverage at E2E time catches issues that unit tests cannot — colour contrast, focus management, live-region announcements, heading hierarchy — because only the real browser renders them. Waiting for a stable waypoint (`await expect(mainHeading).toBeVisible()`) before scanning avoids false positives from mid-render states.

---

### `nodejs.E-POS-P1` — Condition-based performance assertion via `PerformanceObserver` / Web Vitals

**Applies to:** `e2e` — sub-lane P (performance).

**Detection:** `page\.evaluate\(` returning a structured object from a `PerformanceObserver` observing `largest-contentful-paint` / `first-input` / `layout-shift`, OR import of the `web-vitals` npm package (`import { onLCP, onINP, onCLS } from 'web-vitals'`) with an assertion on LCP / INP / CLS numeric thresholds. Cypress equivalent: `cy.window().then((win) => ...)` reading `win.performance.getEntriesByType('largest-contentful-paint')`.

**Why positive:** measures the Core Web Vitals the user actually experiences rather than raw `page.goto` wall-clock time. Resilient to CI jitter when the thresholds are chosen per environment (cold load vs warm, CI vs dev).
