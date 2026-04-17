# Extension: .NET — E2E-rubric addon

Addon to [dotnet-core.md](dotnet-core.md) loaded **only when step 0b selects the E2E rubric**. Currently a stub — no framework-specific `dotnet.E-*` smells are declared yet. Add them here as patterns emerge from real audits.

**Prerequisite:** `dotnet-core.md` must already be loaded. The test-type detection signals that route a test to the E2E rubric (Playwright / Selenium imports, browser session types, `PageTest` / `ContextTest` base classes) live in `dotnet-core.md` because dispatch happens before rubric selection.

**Note on procedures not applicable to E2E:** `dotnet-core.md` declares the Stryker mutation tool, SUT surface enumeration, and determinism verification. Per [SKILL.md § Mutation testing (conditional)](../SKILL.md#mutation-testing-conditional) and [SKILL.md § Determinism verification](../SKILL.md#determinism-verification), those procedures **do not apply to E2E audit targets** — the SUT for an E2E test is the whole deployed stack driven through a browser, and neither mutation testing nor determinism rerun is meaningful against that target. The audit agent must skip those steps when the selected rubric is E2E, regardless of whether `dotnet-core.md` declared the tools.

---

## Sub-lane classification hints

Core [SKILL.md § 0b step 5](../SKILL.md#0b-select-the-rubric) already lists the canonical sub-lane routing signals (`[Trait("Category", "Accessibility")]`, axe / `AxeBuilder`, Web Vitals / `PerformanceObserver`, CSP / cookie assertions).

.NET-specific refinements:

- **Cloud-browser hosts route identically.** Tests using Azure Playwright Workspaces (`Azure.Developer.Playwright.NUnit`) or Microsoft Playwright Testing Preview (`Azure.Developer.MicrosoftPlaywrightTesting.NUnit`) run the same `IPage` API against a cloud-hosted browser instead of a local one. Classify them into sub-lanes using exactly the same signals as local Playwright (`[Trait("Category", "Accessibility")]` etc.); the cloud runner is a transport detail, not a sub-lane.
- **bUnit is not E2E.** `using Bunit;` renders a component in-process without a browser — route to the unit rubric, not E2E, per `dotnet-core.md` §Test type detection signals. Microsoft's own guidance (Test Razor components in ASP.NET Core Blazor) treats bUnit as unit testing and Playwright as E2E; do not conflate.

---

## Framework-specific high-confidence E2E smells (`dotnet.E-HC-*`)

*(No entries yet. Add `dotnet.E-HC-F*`, `dotnet.E-HC-A*`, `dotnet.E-HC-P*`, `dotnet.E-HC-S*` here as Playwright / Selenium-specific failure patterns emerge. Each entry follows the standard extension-smell shape: `Applies to:` line, detection hint, smell description, example, and rewrite.)*

---

## Framework-specific low-confidence E2E smells (`dotnet.E-LC-*`)

### `dotnet.E-LC-F1` — `Page.WaitForTimeoutAsync(...)` / `Thread.Sleep(...)` instead of a condition-based wait

**Applies to:** `e2e` — sub-lane F (functional).

**Detection:** `\.WaitForTimeoutAsync\(` or `Thread\.Sleep\(` anywhere in a test body whose class routes to E2E (Playwright / Selenium base class, `IPage` injection, `[SetUpFixture]` with `PlaywrightServiceBrowserNUnit`, etc.).

**Why low-confidence:** fixed-duration waits are flaky by construction — they fail on slow CI runners and waste time on fast ones. Sometimes legitimate when waiting for a non-observable side effect (e.g. a debounced analytics beacon), but that's rare. Flag with a note; the author can dismiss if the delay is genuinely tied to wall-clock time.

**Rewrite:** use Playwright's auto-waiting assertions: `await Expect(locator).ToBeVisibleAsync()`, `await Expect(locator).ToHaveTextAsync("...")`, `await Expect(locator).ToHaveCountAsync(3)`, or `await locator.WaitForAsync(new() { State = WaitForSelectorState.Visible })` — all retry with a timeout until the condition holds.

---

## Framework-specific E2E positive signals (`dotnet.E-POS-*`)

### `dotnet.E-POS-F1` — Accessible-name locators (`GetByRole`, `GetByLabel`, `GetByText`, `GetByAltText`, `GetByPlaceholder`, `GetByTitle`)

**Applies to:** `e2e` — sub-lane F (functional) and A (accessibility).

**Detection:** `page\.GetBy(Role|Label|Text|AltText|Placeholder|Title|TestId)\(` or `locator\.GetBy...` in a Playwright E2E test.

**Why positive:** locators based on ARIA role, label text, or alternative text are the approach Playwright documents (and Microsoft recommends via its SPA testing guidance) because they double as accessibility checks — if the locator can't find the element, the control is likely unlabelled for assistive tech. Tests stay resilient to CSS / DOM restructuring. Reward under sub-lane F always; under sub-lane A the same pattern is load-bearing because it validates the accessible name contract.

---

### `dotnet.E-POS-F2` — Condition-based waits via `Expect(locator).To*Async` web-first assertions

**Applies to:** `e2e` — sub-lane F.

**Detection:** `Expect\(.*\)\.To(BeVisible|BeHidden|BeEnabled|BeChecked|HaveText|HaveValue|HaveCount|HaveAttribute|HaveClass|HaveURL|ContainText)Async\(` (from `using static Microsoft.Playwright.Assertions;`).

**Why positive:** Playwright's `Expect(...)` web-first assertions retry until the condition is met or the per-assertion timeout expires. Pairing them with `GetByRole` / `GetByLabel` locators eliminates both locator flake and timing flake — tests describe the target UI state rather than pinning execution order. Counterpart to `dotnet.E-LC-F1`.

---

### `dotnet.E-POS-F3` — Per-test `IBrowserContext` factory with explicit state scope

**Applies to:** `e2e` — sub-lane F, S.

**Detection:** a test class that derives from `ContextTest` / `PageTest` (so Playwright creates a fresh `BrowserContext` per test) OR a test that builds a context explicitly via `await browser.NewContextAsync(new() { ... })` in `[SetUp]` / `IAsyncLifetime.InitializeAsync` and disposes it per test.

**Why positive:** a per-test context isolates cookies, storage, and auth state between tests, which is what Playwright's `PageTest` base class is designed to give you. Suites that share a single context across tests bleed state and mask order-dependency bugs; a per-test context removes that whole class of flake and is what the Playwright team recommends. Especially valuable under sub-lane S (security) where cross-test cookie leaks invalidate auth assertions.

---

### `dotnet.E-POS-A1` — `AxeBuilder` or `AccessibilityHelper` wired to `IPage` with a per-page scan

**Applies to:** `e2e` — sub-lane A (accessibility).

**Detection:** `new AxeBuilder(page)` or `await page.RunAccessibilityScanAsync()`-style helper plus an assertion on `result.Violations` / `result.Passes`, typically after a known-good waypoint (e.g. `await Expect(mainHeading).ToBeVisibleAsync()` before the scan).

**Why positive:** axe-core coverage at E2E time catches issues that unit tests cannot — colour contrast, focus management, live-region announcements, heading hierarchy — because only the real browser renders them. Waiting for a stable waypoint before scanning avoids false positives from mid-render states.

---

### `dotnet.E-POS-P1` — Condition-based performance assertion via `PerformanceObserver` / Web Vitals, not wall-clock

**Applies to:** `e2e` — sub-lane P (performance).

**Detection:** `page.EvaluateAsync<...>` returning a structured object from a `PerformanceObserver`, `performance.getEntriesByType('largest-contentful-paint'|'first-input'|'layout-shift')`, or a Web Vitals library call, with an assertion on LCP / INP / CLS numeric thresholds.

**Why positive:** measures the Core Web Vitals the user actually experiences rather than raw `page.goto` wall-clock time. Resilient to CI jitter when the thresholds are chosen per environment.
