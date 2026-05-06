# Extension: Node.js / TypeScript — unit-rubric addon

Addon to [nodejs-core.md](nodejs-core.md) loaded **only when step 0b selects the unit rubric** (or `component`, which is unit-equivalent). Carries framework-specific smells that apply exclusively under the unit rubric — typically because the smell they target is already covered by a core integration-rubric smell (`I-HC-A1` / `I-HC-B5` etc.) and would double-fire if listed as rubric-neutral.

**Prerequisite:** `nodejs-core.md` must already be loaded. Everything in this file refines or depends on content defined there.

---

## Framework-specific high-confidence smells (unit-only)

### `nodejs.HC-U1` — React Testing Library implementation-selector locator when an accessible-name query exists

**Applies to:** `unit` — under the integration / E2E rubrics, selectors are governed by `E-HC-F2` at the browser layer; this refines the unit-rubric component-test finding.

**Detection:** in a test file that imports from `@testing-library/react` (or `/vue` / `/svelte` / `/dom`), any of:

- `container.querySelector\(['"](?P<sel>[^'"]+)['"]` where `<sel>` is a raw CSS class selector (starts with `.`) or attribute selector.
- `screen\.getByTestId\(` or `getByTestId\(` when the same test body does **not** reference an `aria-label`, `role`, `aria-labelledby`, or visible text anywhere — i.e. a `getByTestId` used as the *only* locator strategy with no accessible-name fallback.
- `screen\.getByClassName\(` / `getByClassName\(` (non-standard but seen in migrated Enzyme tests).

**Smell:** Testing Library's documented query priority is **`getByRole` → `getByLabelText` → `getByPlaceholderText` → `getByText` → `getByDisplayValue` → `getByAltText` → `getByTitle` → `getByTestId` → `container.querySelector` (manual)** (see https://testing-library.com/docs/queries/about#priority). Skipping to implementation selectors pins the test to the current DOM structure rather than to user-observable behavior. A refactor that restructures the markup (changes a wrapper `<div>`, swaps `<a>` for `<button>`, reorders class names) breaks the test without changing what the user experiences.

**Carve-out:** do not flag `getByTestId` when the SUT renders opaque third-party content (iframe embeds, `<canvas>`, `<svg>` without `<title>` / `aria-label`) where no accessible name is available — the test-id is the legitimate fallback.

**Example (smell):**
```tsx
render(<CheckoutForm />);
const btn = container.querySelector('.btn-primary.submit-checkout');
fireEvent.click(btn!);
```

**Rewrite (intent):**
```tsx
render(<CheckoutForm />);
const btn = screen.getByRole('button', { name: /submit order/i });
const user = userEvent.setup();
await user.click(btn);
```

---

## Framework-specific low-confidence smells (unit-only)

### `nodejs.LC-U1` — `jest.mock('<local-relative>')` / `vi.mock('<local-relative>')` of the SUT's immediate collaborator

**Applies to:** `unit` — under the integration rubric, module-level mocking of an in-process collaborator is already a scope leak (`I-HC-A1`); this refines the unit-rubric finding by targeting the one specific case `nodejs.HC-1` does not cover: an adjacent-module collaborator that the project team has declared a seam.

**Detection:** `(jest|vi)\.mock\(['"](?P<path>\.[^'"]+)['"]` at module level where `<path>` resolves to a sibling file of the SUT (same directory) or a child of the SUT's directory, AND the audit has **no** evidence the project treats this module as a seam (no matching carve-out in repo `CLAUDE.md` / `README.md` / ADR; no corresponding interface declaration).

**Why low-confidence:** the same pattern is both a scope leak *and* a legitimate "test-via-seams" convention. Repo-level documentation distinguishes the two.

**Carve-out:** suppressed when the mocked module is an `index.ts` barrel that re-exports a domain boundary (e.g. `../services/index.ts` where `services/` is a documented DI seam), or when the project's `CLAUDE.md` / `README.md` states "interfaces in `*/seams/*` exist for testability".

**Rewrite (intent):** inject the collaborator as a constructor / function parameter and pass a `jest.fn()` at call time. The test names the dependency it's replacing at the call site rather than hijacking the module graph.

---

### `nodejs.LC-U2` — `waitFor(() => expect(...))` around a synchronous assertion

**Applies to:** `unit` — component-test specific.

**Detection:** `import { waitFor } from '@testing-library/react'` (or `/dom`) plus `await waitFor\(\s*\(\)\s*=>\s*{?\s*expect` wrapping an assertion whose underlying query is synchronous (`screen.getByText(...)` / `screen.getByRole(...)`) AND the preceding interaction was synchronous (`fireEvent.click(...)` rather than `user.click(...)` / an async SUT effect).

**Why low-confidence:** `waitFor` retries until the assertion passes or the timeout expires. Wrapping a synchronous assertion in `waitFor` masks a latent race — the test passes because the assertion eventually becomes true during retry, but the author's intent was "should already be true". A future refactor that changes the synchronization model silently trips the retry budget.

**Rewrite (intent):** drop `waitFor` if the assertion is synchronous. Use `screen.findByRole(...)` (which is `getBy + waitFor`) for a genuinely asynchronous query. Use `user.click(...)` from `@testing-library/user-event` for interactions that involve event-loop work.

---

## Framework-specific positive signals (unit-only)

### `nodejs.POS-U1` — `userEvent.setup()` once per test instead of `fireEvent` for high-level interactions

**Applies to:** `unit` — component-test specific.

**Detection:** `import userEvent from '@testing-library/user-event'` plus `const user = await userEvent.setup(...)` or `const user = userEvent.setup(...)` inside a test function, followed by `await user.click(...)` / `await user.type(...)` / `await user.hover(...)` etc.

**Why positive:** `userEvent` simulates the full browser event sequence a real user triggers (pointerdown, focus, click, keyup, etc.) rather than firing one synthetic event like `fireEvent`. `userEvent.setup()` returns a user-session object whose keyboard and pointer state persist across calls in the same test, matching how a real user's inputs accumulate. This is the v14+ documented pattern — prefer it over `fireEvent` for anything above a simple "I just need to trigger a click handler" unit.
