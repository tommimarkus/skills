# Extension: Next.js — E2E-rubric addon

Addon to [nextjs-core.md](nextjs-core.md) loaded **only when step 0b selects the E2E rubric**. Carries Next.js-specific Playwright smells and positive signals around App Router hydration, RSC-payload scraping, and Server Action side-effect verification.

**Prerequisite:** [`nodejs-core.md`](nodejs-core.md), [`nextjs-core.md`](nextjs-core.md), and [`nodejs-e2e.md`](nodejs-e2e.md) must already be loaded. This file adds Next.js-specific refinements on top. `nextjs.E-*` smells are additional to `nodejs.E-*` smells, not replacements. The Playwright locator / web-first-assertion / per-test context patterns (`nodejs.E-POS-F1..F3`) all apply under Next.js unchanged.

**Note on procedures not applicable to E2E:** `nodejs-core.md` declares the Stryker JS mutation tool, SUT surface enumeration, and determinism verification. Per [SKILL.md § Mutation testing (conditional)](../../skills/test-quality-audit/SKILL.md) and [SKILL.md § Determinism verification](../../skills/test-quality-audit/SKILL.md), those procedures **do not apply to E2E audit targets** — the SUT for an E2E test is the whole deployed stack driven through a browser. Skip those steps when the selected rubric is E2E.

---

## Sub-lane classification hints

Core [SKILL.md § 0b step 5](../../skills/test-quality-audit/SKILL.md) and [`nodejs-e2e.md § Sub-lane classification hints`](nodejs-e2e.md#sub-lane-classification-hints) already cover the canonical signals. Next.js refinements:

- **App Router–only assertions on hydration timing** — a test that `page.goto('/dashboard')` then immediately `await expect(page.getByRole('button', { name: 'Add item' })).toBeEnabled()` is sub-lane F (functional journey); the hydration wait is the functional gate.
- **RSC-payload network interception** — a test that uses `page.route('**/_rsc=*', ...)` to assert on the serialized Server Component payload is sub-lane F but characterization (see `nextjs.E-HC-F2`). The RSC payload shape is a Next.js compile-time artifact, not a published contract.
- **Server Action post-submission UI assertion** — a test that clicks a form whose action triggers a Server Action and asserts the resulting UI reflects the post-revalidation state is sub-lane F; the revalidation lag is the integration point under test.

---

## Framework-specific high-confidence E2E smells (`nextjs.E-HC-*`)

### `nextjs.E-HC-F1` — E2E assumes App-Router hydration is complete without an observable wait

**Applies to:** `e2e` — sub-lane F. Refines core `E-HC-F3`.

**Detection:** a test whose first interaction after `page.goto('<app-router-path>')` is a synchronous click / type / fill (`page.click(...)` / `page.fill(...)` / `locator.click()` without a preceding `await expect(locator).toBeEnabled()` / `toBeVisible()` / `toBeAttached()`).

**Smell:** Next.js App Router streams Server Component HTML, then hydrates Client Components progressively. A test that clicks immediately after navigation races the hydration — the click either hits the button before its React event handlers are attached (the click does nothing) or hits during a hydration boundary mismatch (the click is dispatched to stale markup). The test fails intermittently under CI CPU pressure and passes reliably on the author's machine.

**Rewrite (intent):**
```ts
// Before (smell):
await page.goto('/dashboard');
await page.getByRole('button', { name: 'Add item' }).click();

// After (intent):
await page.goto('/dashboard');
await expect(page.getByRole('button', { name: 'Add item' })).toBeEnabled();
await page.getByRole('button', { name: 'Add item' }).click();
```

The `toBeEnabled()` assertion is a hydration gate — Playwright retries until the element is attached AND the attribute state says it's interactive.

---

### `nextjs.E-HC-F2` — Test scrapes the `_rsc` response payload via network interception

**Applies to:** `e2e` — sub-lane F. Refines core `E-HC-F7` (snapshot) and `E-HC-F10` (re-proves a lower-lane contract).

**Detection:** a test that uses `page.route('**/*_rsc=1*', ...)` / `page.on('response', res => res.url().includes('_rsc='))` to capture or assert on the Server Component flight payload (the `_rsc=1` query-string or the `text/x-component` response body).

**Smell:** the RSC payload is a Next.js internal compile-time artifact. Its shape changes between Next.js minor versions (RSC protocol v1 → v2 transitions, Server Component boundary compression changes). A test that asserts on payload structure pins the Next.js version; a test that asserts on payload content pins the compile-time output — both are characterization, and the test fails on Next.js upgrades with no business-visible change. Additionally, any assertion that *could* be made on `_rsc` could be made more reliably at the Server Component integration layer (sub-lane A) without the browser — so this test is also in the wrong lane per `E-HC-F10`.

**Rewrite (intent):** move the assertion down-lane. If the test is verifying "the dashboard page shows the logged-in user's data", assert on the *rendered* UI (`screen.getByText(...)` / `page.getByText(...)`) — that's the user-observable outcome. If the test is verifying the Server Component's data-fetch shape, write an integration sub-lane A test against the Server Component with a real DB fixture.

---

## Framework-specific low-confidence E2E smells (`nextjs.E-LC-*`)

*(No entries yet. Add Next.js-specific Playwright patterns here as real audits surface them — e.g. tests that assume a specific Next.js dev-overlay element is absent.)*

---

## Framework-specific E2E positive signals (`nextjs.E-POS-*`)

### `nextjs.E-POS-F1` — Server Action E2E asserts on post-revalidation UI

**Applies to:** `e2e` — sub-lane F. Complements `nextjs.I-HC-A2` at the E2E layer.

**Detection:** a test that submits a form whose HTML `action` attribute targets a Server Action (a `<form action={createOrder}>` in the source), then asserts on the UI updating to reflect the server-side state change — typically via `await expect(page.getByText(/order created/i)).toBeVisible()` or `await expect(page.locator('[data-testid="order-list"] li')).toHaveCount(n)` where `n` includes the newly-created row.

**Why positive:** Server Actions' full contract is DB write + `revalidatePath` / `revalidateTag` + the consumer UI re-rendering with fresh data. Asserting on the post-revalidation UI is the only place where *all three* are verified together — sub-lane A tests the DB write and the revalidation side effect (via `nextjs.I-HC-A2`'s fix); only the E2E exercises the full round-trip. Matches `E-POS-1` (user-story-named) and `POS-3` (asserts on published side effect).

---

### `nextjs.E-POS-F2` — Per-test Next.js webServer config via Playwright's `webServer` option

**Applies to:** `e2e` — sub-lane F.

**Detection:** `playwright.config.{ts,js,mjs}` with a `webServer` block pointing at `next build && next start -p <dynamic-port>` OR a `webServer.command` of `pnpm start` / `npm start` whose underlying `package.json` `start` script runs `next start`. The config uses `webServer.reuseExistingServer: !process.env.CI` (or equivalent) so that CI always builds fresh but local dev reuses.

**Why positive:** testing against `next start` (production build) rather than `next dev` catches production-only issues that dev-mode hides — static optimization, chunking, RSC-payload shape, the absence of dev-mode hot-reload hooks. This is the [Next.js-recommended Playwright pattern](https://nextjs.org/docs/app/guides/testing/playwright). Counterpart and enabler for `nextjs.POS-2` (core).

---

### `nextjs.E-POS-F3` — Test uses `page.getByRole(...)` against Next.js's Link and Form elements

**Applies to:** `e2e` — sub-lane F and A.

**Detection:** a test that navigates via `page.getByRole('link', { name: '<accessible text>' }).click()` for Next.js `<Link>` elements, or submits forms via `page.getByRole('button', { name: /submit/i })` for `<form action={serverAction}>`.

**Why positive:** Next.js's `<Link>` renders a real `<a>` element (not a JS click handler), so accessible-role queries work correctly. `<form action={serverAction}>` submits like a plain HTML form — so `getByRole('button', { type: 'submit' })` finds the submitter and the test exercises the full browser-form submission path, including the Next.js-generated action URL. Explicitly complements `nodejs.E-POS-F1` for the Next.js-specific elements.
