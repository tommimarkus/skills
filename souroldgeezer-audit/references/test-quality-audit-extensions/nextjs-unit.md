# Extension: Next.js — unit-rubric addon

Addon to [nextjs-core.md](nextjs-core.md) loaded **only when step 0b selects the unit rubric** (or `component`, which is unit-equivalent). Carries framework-specific smells that apply exclusively under the unit rubric — almost all are client-component tests, since Server Components cannot be meaningfully unit-tested (they route to integration sub-lane A per `nextjs-core.md`'s file-shape table).

**Prerequisite:** Both [`nodejs-core.md`](nodejs-core.md) and [`nextjs-core.md`](nextjs-core.md) must already be loaded. This file refines unit-rubric behaviour on top of both. [`nodejs-unit.md`](nodejs-unit.md) also loads concurrently; `nextjs.*-U*` smells are additional to `nodejs.*-U*` smells, not replacements.

---

## Framework-specific high-confidence smells (unit-only)

### `nextjs.HC-U1` — Test asserts on the rendered `'use client'` directive string

**Applies to:** `unit` — test pins a compilation artifact that never reaches the DOM.

**Detection:** any of the following in a client-component test body:

- `expect\(.*?\)\.toContain\(['"]use client['"]\)` against the rendered HTML / `container.innerHTML` / `prettyDOM(container)` output.
- A snapshot (`toMatchSnapshot()` / `toMatchInlineSnapshot()`) whose content string includes `"use client"`.
- A `getByText\(['"]use client['"]\)` assertion (authors sometimes confuse the directive with user-visible text).

**Smell:** `'use client'` is a compile-time directive that Next.js's SWC pipeline reads and strips before rendering. It is never present in the DOM at runtime. An assertion that the rendered output contains the string is either (a) a misconception about how the directive works, or (b) a characterization snapshot that happens to include the directive as a source-level artifact. Either way, the assertion is not testing user-observable behaviour.

**Rewrite (intent):** if the test is verifying the component is a Client Component, that's a concern for the build / type system, not for a runtime test — delete the assertion. If the test is pinning the rendered output as characterization, replace with role-based / label-based queries per `nodejs.POS-7`.

---

## Framework-specific low-confidence smells (unit-only)

### `nextjs.LC-U1` — Client-component test `jest.mock`s a sibling Client Component it renders

**Applies to:** `unit` — refines `nodejs.LC-U1` for the Next.js-specific case where the sibling is inside the same client subtree.

**Detection:** `(jest|vi)\.mock\(['"](?P<path>[./][^'"]+)['"]` in a test targeting a file that has `'use client'` at top-of-file, where `<path>` resolves to a file that *also* has `'use client'` at top-of-file (both are Client Components in the same subtree).

**Why low-confidence:** sometimes legitimate (a sibling Client Component wraps a heavyweight library — Mapbox, a rich-text editor — whose initialization in a unit test is genuinely infeasible). More often the author defaulted to module mocking because the sibling is "someone else's code" when in reality both components are owned by the same module and the mock is pinning an internal boundary. A `jest.mock` of an owned Client Component sibling is particularly fragile because the mock's shape must track the sibling's props evolution, and TypeScript does not catch drift across a `jest.mock(...)` factory boundary.

**Carve-out:** suppressed when the mocked sibling's top-of-file JSDoc contains `@seam` or the project's `CLAUDE.md` declares a "Client Component seam" convention — same pattern as `nodejs.LC-U1`'s test-via-seams carve-out.

**Rewrite (intent):** let the sibling render normally. If the sibling's initialization is genuinely expensive (ships a heavy third-party library), extract the expensive piece behind a small wrapper that can be stubbed at a boundary rather than mocking the whole sibling.

---

## Framework-specific positive signals (unit-only)

### `nextjs.POS-U1` — Client component tested with `next-router-mock` + `userEvent.setup()` + accessible-name queries

**Applies to:** `unit`

**Detection:** a client-component test file with all three of:

- `import 'next-router-mock'` OR `jest.mock('next/navigation', () => require('next-router-mock/MemoryRouterProvider'))` OR equivalent memory-router wiring.
- `import userEvent from '@testing-library/user-event'` with `userEvent.setup()` per test (v14+ idiom from `nodejs.POS-U1`).
- At least one `screen.getByRole(...)` / `screen.getByLabelText(...)` assertion (accessible-name query — `nodejs.POS-7`).

**Why positive:** combines three blessed patterns — Next-compatible navigation mocking without hand-rolling `useRouter`; real user-like interaction via `userEvent` v14+; accessible-name locators that double as a11y smoke. This is the shape Next.js's own [testing docs](https://nextjs.org/docs/app/guides/testing) point to for component tests.
