# Extension: Next.js — core

Shared core for the Next.js test-quality-audit extension. This file is loaded **whenever a Next.js project is detected** (after [`nodejs-core.md`](nodejs-core.md) loads first), before step 0b (rubric selection). It owns Next.js-specific detection, the file-shape → rubric routing table, App Router / Pages Router / Route Handler / Server Action / Server Component / proxy (middleware) semantics, rubric-neutral Next.js smells, Next-platform carve-outs against `nodejs.*` smells, and Next.js-specific SUT surface enumeration patterns that extend `nodejs-core.md`'s five-class enumeration.

Rubric-exclusive content lives in the rubric addons:

- [`nextjs-unit.md`](nextjs-unit.md) — `Applies to: unit` smells for client-component tests.
- [`nextjs-integration.md`](nextjs-integration.md) — `nextjs.I-*` smells for Route Handlers, Server Actions, Server Components, and proxy / middleware tests, plus an auth-matrix extension layering Auth.js v5 `auth()` call-site enumeration and proxy `matcher` config parsing on top of [`nodejs-integration.md`](nodejs-integration.md).
- [`nextjs-e2e.md`](nextjs-e2e.md) — Playwright-specific hydration / RSC / Server Action E2E smells and positive signals.

Covers App Router (`app/` directory), Pages Router (`pages/` directory), Route Handlers, Server Components, Server Actions, proxy (Next.js 16+) / middleware (legacy), `next/navigation`, `next/headers`, `next/cache`, `next/font`, `next-router-mock`, and `next/experimental/testing/server` helpers.

---

## Composition rule (Next.js depends on Node.js / TypeScript)

**Next.js is a strict superset of Node.js / TypeScript.** When `next` is in a project's `package.json` dependencies, the detection phase **always loads [`nodejs-core.md`](nodejs-core.md) first**, then this file. The audit agent records both as loaded extensions.

Composition rules govern how `nextjs.*` smells interact with `nodejs.*` smells:

1. **`nextjs.*` carve-outs MAY suppress `nodejs.*` smells at Next-platform boundaries.** Platform boundaries are imports from `next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, `client-only`, `next/server`, and `next/image`. A mock of any of these is *not* a `nodejs.HC-1` / `HC-5` smell — the module is a platform API from Next.js's perspective even though it's a local import from Node's. See § Carve-outs below.
2. **`nextjs.*` smells MAY NOT override a `nodejs.*` smell.** When a pattern matches both (e.g. a test violates both `nodejs.HC-1` and `nextjs.HC-2`), emit a single finding citing both codes in the `Smells:` list, severity = max. Ordering in cites: `core → nodejs → nextjs` (left to right, most general to most specific). Example: `HC-5, nodejs.HC-1, nextjs.HC-2`.
3. **Carve-outs cannot expand scope.** A `nextjs.*` carve-out is always of the form "do not flag X when exactly Y"; it cannot broaden a `nodejs.*` smell's reach.
4. **Shared detection signals trigger load-once.** React Testing Library, Jest, Vitest, Playwright are all detected by `nodejs-core.md`. `nextjs-core.md` does not re-declare them; it only declares Next-specific ones (`next` dep, `next.config.*`, `app/` / `pages/`, `proxy.*` / `middleware.*`, `@next/*`, `next-router-mock`).
5. **Mutation tool, determinism verification, and test-double classification** are inherited from `nodejs-core.md` unchanged. Next.js-specific known-limitation caveats for Stryker JS (App Router SWC pipeline, React Server Components) are already documented in [`nodejs-core.md § Mutation tool § Known SUT limitations § Next.js App Router`](nodejs-core.md#5-known-sut-limitations).

---

## Detection signals

Load this extension **in addition to** `nodejs-core.md` when the audit target contains any of:

- `package.json` with `"next"` in `dependencies` (any major version). `next` in `devDependencies` alone does not trigger — that's a legacy pattern for plugins building against Next.
- `next.config.{js,ts,mjs,cjs}` at the project root (or the directory containing the `package.json` that declares `next`).
- `app/` directory with at least one of `layout.{tsx,jsx,ts,js}` / `page.{tsx,jsx,ts,js}` / `route.{ts,js}` / `template.{tsx,jsx,ts,js}` — **App Router flag.**
- `pages/` directory with at least one of `_app.{tsx,jsx,ts,js}` / `_document.{tsx,jsx,ts,js}` / `index.{tsx,jsx,ts,js}` — **Pages Router flag.** Both flags can be set simultaneously (a repo mid-migration); record both.
- `proxy.{ts,js}` at the repo root OR `src/` root OR the directory containing `app/` / `pages/` — **Proxy file flag** (Next.js v16.0.0+). Per the official docs, the `middleware` file convention was deprecated and renamed to `proxy` in v16.0.0 (see https://nextjs.org/docs/app/api-reference/file-conventions/proxy § Migration to Proxy).
- `middleware.{ts,js}` at the same locations — **Middleware file flag** (Next.js pre-v16 legacy; still present in many production repos). A Next.js codemod (`npx @next/codemod@canary middleware-to-proxy .`) migrates this to `proxy`.
- `@next/*` scoped packages: `@next/env`, `@next/mdx`, `@next/swc-*`, `@next/bundle-analyzer`, `@next/third-parties`, `@next/font` (legacy — subsumed into `next/font` in v13+). Any of these implies Next.js.

### Version flags (affect downstream behavior)

Record these on detection:

- **Major version.** Parse `"next": "<spec>"` from `package.json`. Normalize to a major number. Affects which proxy / middleware convention applies (v16+ → `proxy`; pre-v16 → `middleware`) and the App Router availability (v13+).
- **Router flags.** Set above. A repo with both `app/` and `pages/` (migration in progress) is a legitimate shape — the routing table applies per-file based on the file's location.
- **Mixed proxy / middleware state.** If both `proxy.{ts,js}` and `middleware.{ts,js}` exist in the same project, treat as a mid-migration state worth a low-confidence finding (`nextjs.LC-2` — partial codemod).

---

## Test type detection signals

Consumed by [SKILL.md § 0b (Rubric selection)](../SKILL.md#0b-select-the-rubric). Next.js **rewrites the test-type routing rules** because the file's location in the Next.js source tree dictates whether the test can be unit, integration, or E2E — a Server Component cannot be meaningfully unit-tested in isolation, a Route Handler is out-of-process contract, and a Server Action is in-process with a real DB.

### Next.js file-shape routing table

The SUT file's position in the source tree and its top-of-file directives determine the rubric. Apply in order; first match wins.

| SUT file shape | Routing rule | Rubric |
|---|---|---|
| `app/**/*.{tsx,jsx}` with top-of-file `'use client'` directive; the test renders it with `@testing-library/react` and mocks collaborators | Standard React component test | **unit** (default) |
| `app/**/*.{tsx,jsx}` without `'use client'` (implicitly a Server Component); typically `async` function, `await`s server-side data (DB, fetch, `cookies()`, `headers()`) | Server Component — cannot execute under RTL in isolation (React Testing Library does not run server components) | **integration sub-lane A** (in-process with a real adjacent dependency) |
| `app/**/route.{js,ts,jsx,tsx}` exporting one or more of `GET` / `POST` / `PUT` / `PATCH` / `DELETE` / `HEAD` / `OPTIONS` | Route Handler — tested by invoking the exported function with a `Request` and asserting on the returned `Response` | **integration sub-lane B** (out-of-process contract) |
| `app/**/actions.{ts,js}` OR any file containing an `async function` preceded by a `'use server'` directive (top-of-file or inline) | Server Action — in-process server code, typically writes to the DB and returns data to a client component | **integration sub-lane A** |
| `proxy.{ts,js}` at root or `src/` root (v16+) — exports `proxy` function or default export; returns a `NextResponse` | Proxy — tested by invoking the function with a `NextRequest` and asserting on the returned `NextResponse` (redirect target, status, headers, cookies) | **integration sub-lane B** |
| `middleware.{ts,js}` at root or `src/` root (pre-v16 legacy) — same shape, exported as `middleware` | Legacy middleware — same treatment as Proxy | **integration sub-lane B** |
| `pages/api/**/*.{js,ts}` (Pages Router API route) exporting `default` handler of `(req, res) => void` | API route — HTTP contract | **integration sub-lane B** |
| `pages/**/*.{tsx,jsx}` declaring `getServerSideProps` / `getStaticProps` / `getStaticPaths` | Server-rendered page — exercises server data fetch path | **integration sub-lane A** |
| `pages/**/*.{tsx,jsx}` with no server data fetch (purely client-rendered) | Client page | **unit** (default) |

**Sub-lane selection within integration:**

- **Sub-lane A (in-process):** the test instantiates the SUT (or its host) in the same process, wires real adjacent dependencies (DB via Testcontainers / Prisma / Drizzle / TypeORM / Knex; MSW for upstream HTTP), and asserts on observable state. Server Components, Server Actions, and `pages/*.tsx` with `getServerSideProps` fall here.
- **Sub-lane B (out-of-process contract):** the test invokes a handler that speaks HTTP (Route Handler, Pages API, proxy / middleware) by constructing a `Request` / `NextRequest` and asserting on the returned `Response` / `NextResponse`. The boundary under test is the HTTP contract; internal collaborators (`cookies()`, `headers()`, `getServerSession()`) are exercised through the real request, not mocked.

### E2E rubric signals

Next.js contributes no dedicated E2E framework — projects use `@playwright/test` / `cypress` / `webdriverio` per `nodejs-core.md` detection. Sub-lane classification uses Next.js-specific refinements in `nextjs-e2e.md`:

- Hydration-timing assertions (`await expect(page.getByRole('button')).toBeEnabled()` after `page.goto(...)`) — sub-lane F.
- `_rsc=1` network-interception assertions scraping the RSC payload — flagged as characterization under sub-lane F (see `nextjs.E-HC-F2`).
- `revalidatePath` / `revalidateTag` after a Server Action — sub-lane F with a positive pattern in `nextjs-e2e.md`.

---

## Framework-specific high-confidence smells (`nextjs.HC-*`)

These smells apply under both the unit and integration rubrics (`Applies to: unit, integration`). Unit-only smells live in [`nextjs-unit.md`](nextjs-unit.md); integration-only smells live in [`nextjs-integration.md`](nextjs-integration.md); E2E smells live in [`nextjs-e2e.md`](nextjs-e2e.md).

### `nextjs.HC-1` — `render()` from `@testing-library/react` applied to a Server Component at the unit rubric

**Applies to:** `unit, integration` — refines core `HC-1` / `I-HC-A10`; surfaces in both rubrics because the misrouting can happen in either direction.

**Detection:** a test file imports a component from `app/**/*.{tsx,jsx}` whose source has **no** `'use client'` directive at top-of-file AND is `async` OR reads `cookies()` / `headers()` from `next/headers` / `fetch` at module scope. The test body calls `render(<Component />)` from `@testing-library/react`.

**Smell:** React Testing Library renders components in a JSDOM client environment. Server Components are `async`, `await` server-side data, and must be executed by Next.js's RSC pipeline — JSDOM does not run them. The test either throws (`ReactElement is not valid because it's async`) or appears to pass because RTL silently renders the promise-returning component as empty output. Either way, the test doesn't exercise the SUT.

**Carve-out:** do not flag when the test explicitly imports React's upcoming experimental RSC test renderer (`react-dom/server`'s `renderToString(await ServerComponent())`) and awaits the server component before passing its rendered output to RTL — that pattern is a valid integration-rubric shape, not a unit test (route via the file-shape table).

**Example (smell):**
```tsx
// app/dashboard/page.tsx
import { cookies } from 'next/headers';
export default async function Dashboard() {
  const session = (await cookies()).get('session');
  const rows = await db.user.findMany();
  return <ul>{rows.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// __tests__/Dashboard.test.tsx (smell — unit-rubric test of a Server Component)
import { render, screen } from '@testing-library/react';
import Dashboard from '@/app/dashboard/page';

test('renders users', () => {
  render(<Dashboard />);  // ← does not execute the async server component
  expect(screen.getByRole('list')).toBeInTheDocument();
});
```

**Rewrite (intent):** route to integration sub-lane A. Test via a real DB fixture (Prisma / Drizzle / TypeORM / Knex) and a `fetch` against `next start` running the page, OR extract the server-side logic (the DB call, the cookie-read) into a plain TS helper and unit-test the helper with `nodejs-core.md` patterns.

---

### `nextjs.HC-2` — `jest.mock('next/navigation', ...)` with a hand-rolled router that pins method names

**Applies to:** `unit, integration`

**Detection:** `(jest|vi)\.mock\(['"]next/navigation['"]` followed by a factory that returns an object literal declaring `useRouter`, `usePathname`, `useSearchParams`, `useParams`, `redirect`, or `notFound` with hand-built implementations (e.g. `useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() })`).

**Smell:** hand-rolling `next/navigation` pins the mock to whatever subset of the API the author thought about on the day they wrote the test. When Next.js evolves — adds a method, deprecates one, changes a signature — the hand-built mock silently passes a type-check against an outdated surface. The real router's `push` accepts a `NavigateOptions` second argument (added in Next.js 13.4); hand-built mocks typically don't model it.

**Rewrite (intent):** use [`next-router-mock`](https://github.com/scottrippey/next-router-mock) (see `nextjs.POS-1`) — it provides a `memoryRouter` that implements the full `next/navigation` surface and is maintained against Next.js's evolving API. Or, better, inject the navigation behaviour the SUT needs as a callback (`onNavigate`) and avoid module mocking entirely.

---

### `nextjs.HC-3` — `toMatchSnapshot()` of an App-Router server-rendered tree

**Applies to:** `unit, integration` — refines core `HC-10`.

**Detection:** `\.toMatchSnapshot\(` applied to the rendered output (either `container.firstChild`, `prettyDOM(container)`, the returned `ReactElement` tree, or a string from `renderToString(...)`) of a component imported from `app/**/*.{tsx,jsx}` that is not a Client Component.

**Smell:** the snapshot pins not only the business-visible output but also Next.js-internal hydration markers (`<!--$--><!--/$-->`), RSC payload identifiers, `id="__next"` / `id="__NEXT_DATA__"` attributes, and Server Component boundary comments. These change between Next.js minor versions even when the user-visible rendering is unchanged — the test fails on a routine Next.js upgrade without any SUT change.

**Carve-out:** do not flag when the snapshot is a targeted string comparison of a specific user-facing value (a heading text, a formatted number) extracted via `screen.getByRole(...)` rather than a tree-wide snapshot. That's a scoped assertion, not a characterization snapshot.

**Rewrite (intent):** replace the snapshot with role-based / label-based assertions per `nodejs.POS-7`: `expect(screen.getByRole('heading', { level: 1, name: /welcome/i })).toBeInTheDocument()`. For JSON contract stability, keep the snapshot at the Route Handler layer where the payload's shape is defined by an OpenAPI / Zod schema and the schema carves out `HC-10` automatically.

---

### `nextjs.HC-4` — Route Handler test asserting on internal `cookies()` / `headers()` reads instead of the returned `Response`

**Applies to:** `unit, integration` — refines core `I-HC-B1`.

**Detection:** a test of a file at `app/**/route.{ts,tsx}` that `jest.mock('next/headers')` / `vi.mock('next/headers')` to substitute `cookies()` / `headers()`, then asserts on the mock's invocation (`expect(cookies).toHaveBeenCalled()`) rather than on the handler's returned `Response`.

**Smell:** the test is pinning the handler's *internal* interaction with platform APIs instead of the handler's *observable contract* (status, body, headers of the returned `Response`). A refactor that switches from `cookies()` to `request.cookies` silently breaks the test even though the response contract is unchanged. Every Route Handler test should assert on the returned `Response`; mocks of `next/headers` are valid only when the test needs to set up the *input* (a cookie the handler reads), not the assertion target.

**Rewrite (intent):**
```ts
// Before (smell):
vi.mock('next/headers', () => ({ cookies: vi.fn(() => ({ get: () => null })) }));
test('returns 401 when no session', async () => {
  await GET(new Request('http://localhost/api/me'));
  expect(cookies).toHaveBeenCalled();  // ← pinning internal call
});

// After (intent):
test('returns 401 when no session', async () => {
  const res = await GET(new Request('http://localhost/api/me'));
  expect(res.status).toBe(401);
  expect(await res.json()).toEqual({ error: 'unauthenticated' });
});
```

Use `cookies` / `headers` injection at the boundary if the handler's shape requires it (Next.js 15+ `cookies()` is async — inject a pre-awaited value as a handler argument rather than mocking the module).

---

## Framework-specific low-confidence smells (`nextjs.LC-*`)

### `nextjs.LC-1` — `jest.mock('next/cache' | 'next/headers')` where the test never asserts invocation

**Applies to:** `unit, integration`

**Detection:** `(jest|vi)\.mock\(['"]next/(cache|headers)['"]` at the top of a test file, with no subsequent `.toHaveBeenCalled*` / `expect(<mockedExport>).*` assertion anywhere in the file referencing the mocked module.

**Why low-confidence:** the mock is carved out by `nextjs-core.md § Carve-outs` (platform boundary — see below). But if the test doesn't *use* what it mocked, the mock is dead code carrying a maintenance cost (must be kept in sync with Next.js's API surface). May also indicate the test author started to write an interaction assertion and abandoned it.

**Rewrite (intent):** either add the interaction assertion that motivated the mock, or remove the mock — the carve-out allows it but doesn't require it.

---

### `nextjs.LC-2` — Mid-migration state: both `proxy.{ts,js}` and `middleware.{ts,js}` present in the same project

**Applies to:** `unit, integration` — actually a repo-level signal, but tests that target *either* file pick up this flag.

**Detection:** both `proxy.{ts,js}` and `middleware.{ts,js}` exist in the same project root (or both in `src/`).

**Why low-confidence:** legitimate mid-migration state (the v16 codemod has been partially applied). Flag as a `P3` remediation item — run `npx @next/codemod@canary middleware-to-proxy .` to complete the migration, OR remove the stale file if the migration was intentional. Tests should be migrated alongside the file: a test named `middleware.test.ts` against the new `proxy.ts` file is internally inconsistent.

**Rewrite (intent):** complete the codemod (both the file and its tests); commit; remove the stale file.

---

## Framework-specific positive signals (`nextjs.POS-*`)

### `nextjs.POS-1` — `next-router-mock` with `memoryRouter` for client-component tests

**Applies to:** `unit`

**Detection:** `import(?: { \w+ })? from ['"]next-router-mock['"]` OR `jest\.mock\(['"]next/navigation['"],.*next-router-mock` OR `vi\.mock\(['"]next/navigation['"],.*next-router-mock`.

**Why positive:** `next-router-mock` is a community-maintained, actively-developed (v1+ as of April 2026) drop-in for `next/navigation` that implements the full `memoryRouter` surface and tracks Next.js's API evolution. Using it instead of a hand-rolled mock (see `nextjs.HC-2`) means the test stays typed-correct against Next.js upgrades.

---

### `nextjs.POS-2` — Playwright E2E set up per Next.js's `with-playwright` example

**Applies to:** `e2e`

**Detection:** `playwright.config.{ts,js,mjs}` at the project root whose `webServer` config points at `next build && next start` (or `pnpm start` / `npm start` resolving to the same) — matches the [Next.js official Playwright guide](https://nextjs.org/docs/app/guides/testing/playwright) verbatim.

**Why positive:** the official Next.js testing guide points E2E users to the Playwright setup path. Running against `next start` (production build) rather than `next dev` (dev-mode with hot reload and dev-only overlays) catches production-only issues that dev-mode hides — chunking, static optimization, production RSC payload shape. No `@next/playwright` package is referenced in the current guide; using `@playwright/test` directly is correct.

---

### `nextjs.POS-3` — Route Handler tested as `handler(new Request(url))` → `Response` round-trip

**Applies to:** `integration`

**Detection:** a test of a file at `app/**/route.{ts,tsx}` that imports the named-export handler (`GET` / `POST` / etc.), constructs a `new Request(url, { method, body, headers })`, awaits the handler's return, and asserts on `res.status` / `await res.json()` / `res.headers.get(...)`.

**Why positive:** this is the Next.js idiomatic Route Handler test shape. The boundary under test is the HTTP contract — exactly what `I-POS-6` rewards. No module-level mocking of `next/headers` / `next/cache` needed; the handler's collaborators are exercised through the real Request. Counterpart to `nextjs.HC-4`.

---

### `nextjs.POS-4` — Server Action tested with a real DB fixture + post-invocation DB-state assertion

**Applies to:** `integration`

**Detection:** a test of a file containing `'use server'` OR at `app/**/actions.{ts,js}` that imports the action function, constructs a per-test DB fixture (Prisma / Drizzle / TypeORM / Knex against Testcontainers or a per-test schema), calls the action, and asserts on the DB rows the action wrote. Bonus if the test also asserts on `revalidatePath` / `revalidateTag` side effects via a spy or captured call log.

**Why positive:** Server Actions write through to the DB and trigger cache revalidation; testing them requires exercising both. A DB-backed test matches `I-POS-5` (hermetic) when the fixture is per-test.

---

### `nextjs.POS-5` — Proxy / middleware unit-tested via `next/experimental/testing/server` helpers

**Applies to:** `unit, integration` — the helpers span both rubrics depending on what's asserted.

**Detection:** `import { unstable_doesProxyMatch, isRewrite, getRewrittenUrl, getRedirectUrl } from 'next/experimental/testing/server'` in a test file targeting `proxy.{ts,js}` or `middleware.{ts,js}`.

**Why positive:** stable since Next.js v15.1, documented directly on the `proxy.js` file-convention page. `unstable_doesProxyMatch` verifies the `matcher` config covers an intended URL (routing correctness); `isRewrite` / `getRewrittenUrl` / `getRedirectUrl` read the returned `NextResponse`'s semantics without the test hand-rolling its own decoder. Using these helpers keeps proxy tests precise (the `matcher` config and the response together define the contract, and the helpers test both).

---

## Carve-outs

Patterns that look like `nodejs.*` or core smells but are idiomatic in Next.js and must not be flagged:

- **Do not flag `nodejs.HC-1` / `HC-5`** when `jest.mock(...)` / `vi.mock(...)` targets any of `next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, `client-only`, `next/server`, `next/image`. These are **Next.js platform boundaries** — the module is provided by the framework, not by the repo's own code. Same semantic status as mocking `fetch` / `node:http` in plain Node. This is the single most important carve-out in this file; without it, every App Router test using `useRouter` / `cookies` / `headers` / `revalidatePath` false-positives.

- **Do not flag `HC-10`** (snapshot tests pinning unspecified output) when the snapshot target is:
  - A Next.js Route Handler's JSON response whose schema is published via an OpenAPI document OR a Zod schema exported from the same `route.ts` file (Zod is the dominant schema choice in the Next.js ecosystem; when `const schema = z.object({ ... })` is exported alongside the handler, the schema **is** the contract).
  - A Server Action's return value whose shape is documented as an exported TypeScript type in the same file.

- **Do not flag `nodejs.LC-U1`** (module-mock of same-layer code, unit-rubric) when `jest.mock` targets an `@/components/...` path OR any relative path resolving to a Client Component (`'use client'` at top-of-file) AND the test is of a server-rendered parent. Parent Server Components cannot execute child Client Components in the same test pass — the mock is not a scope leak, it's a necessary stand-in.

- **Do not flag `HC-5`** / `nodejs.HC-1` when the mock target is `next/dynamic` used to stub out a heavyweight client-only chunk. `next/dynamic` is a platform API; mocks of it replace a Next-provided code-splitting primitive, not a same-layer collaborator.

- **Do not flag `nodejs.LC-2`** (`@ts-expect-error` / `@ts-ignore` in test) when the comment is immediately followed by `new Request('<url>', { body: ... })` constructing a request whose body deliberately violates the Zod schema the handler validates. Next.js Route Handler tests legitimately need to feed invalid payloads to exercise the 400-path, and TypeScript strictly types `Request`'s init; the ignore is documenting the deliberate-invalidity, not hiding a drift.

---

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../SKILL.md#sut-surface-enumeration) — step 2.5 of the deep-mode workflow. This section **extends** `nodejs-core.md`'s five-class enumeration with Next.js-specific patterns. Classes deferred entirely to `nodejs-core.md` are marked as such; classes with additional Next.js patterns below are layered *on top of* the `nodejs-core.md` patterns (both fire; de-duplicate at the audit-output stage).

### `Gap-API` (Next.js additions)

**Server Actions.** Enumerate:

- Files whose top-of-file directive is `'use server'`: glob `app/**/*.{ts,tsx,js,jsx}` and `src/**/*.{ts,tsx,js,jsx}`; for each, read the first non-comment line of the file. If it matches `^\s*['"]use server['"]\s*;?\s*$`, every `export async function <name>(` in the file is a Server Action.
- Files containing an inline `'use server'` directive inside a function body: a file whose *first* line is not `'use server'` but which contains `^\s*['"]use server['"]\s*;?\s*$` as the first statement inside a `function` / `async function` body. Those functions are individually Server Actions even though the file is not a Server Actions file.
- Conventional location: `app/**/actions.{ts,js}` — by convention (not enforced by Next.js), projects collect Server Actions into a file named `actions.ts`. Enumerate all exported async functions as likely Server Actions regardless of directive (flag as `medium` confidence if the directive is absent — may be a server-side helper that happens to live here).

**Server Components (as SUT targets under integration sub-lane A).** Enumerate:

- Default exports from `app/**/page.{tsx,jsx}` and `app/**/layout.{tsx,jsx}` in files **without** a `'use client'` directive.
- Default exports from `app/**/loading.{tsx,jsx}`, `app/**/error.{tsx,jsx}`, `app/**/not-found.{tsx,jsx}`, `app/**/template.{tsx,jsx}` (all Server Components by default).
- Each page / layout IS the testable surface for sub-lane A: the test invokes the component with a real DB fixture + real cookies / headers plumbing.

### `Gap-Route` (Next.js additions)

**Next.js Route Handlers.** Enumerate:

- Glob `app/**/route.{js,ts,jsx,tsx}`. For each match, derive the route path from the parent-directory chain under `app/`, honouring Next.js's route group (`(name)`) and dynamic segment (`[slug]`, `[[...slug]]`, `[...slug]`) conventions. Example: `app/api/users/[id]/route.ts` → route template `/api/users/[id]`.
- For each file, grep for exports matching `^export (async )?(function )?(?:const\s+)?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b` — these are the supported HTTP method exports per the [Route Handlers API reference](https://nextjs.org/docs/app/api-reference/file-conventions/route).
- A single `route.ts` file exporting multiple methods is multiple route entries (one per `<path> <METHOD>` pair).
- A test that only calls the route and asserts a URL, heading, `200`, `201`, or `NextResponse` existence is `referenced-weak`. Strong coverage requires the route's contract oracle: body/header/problem shape, auth decision, validation error, state mutation, redirect, rewrite, or cache/session side effect.

**Pages Router API routes.** Enumerate:

- Glob `pages/api/**/*.{js,ts,jsx,tsx}`. Derive the path from the filename (Next.js Pages Router convention: `pages/api/users/[id].ts` → `/api/users/[id]`).
- For each file, the default export is the handler. The HTTP method is typically handled by branching on `req.method` inside the handler — record the entry as `<path> <ALL_METHODS>` with a note that the test should cover each branch.

**Proxy / middleware matcher config.** Enumerate:

- Read `proxy.{ts,js}` (v16+) OR `middleware.{ts,js}` (legacy) from the project root and `src/` root.
- Parse `export const config = { matcher: ... }` — the `matcher` value is either a string, a string array, or an array of matcher objects (`{ source, has, missing, locale }`). Enumerate the matched path patterns as **protected path classes** feeding into the auth-matrix enumeration below.

### `Gap-Migration`

**Defer to [`nodejs-core.md § SUT surface enumeration § Gap-Migration`](nodejs-core.md#grep-patterns-per-gap-class)** — Prisma / Drizzle / TypeORM / Knex patterns apply unchanged. Next.js does not introduce its own migration system.

### `Gap-Throw` (Next.js additions)

**Defer to [`nodejs-core.md § Gap-Throw`](nodejs-core.md#grep-patterns-per-gap-class) for `throw new *Error` patterns.** Next.js additions:

- `throw notFound\(\s*\)` — from `next/navigation`; signals a Next-semantic 404 (renders `not-found.tsx`). The exception type is internal; what matters is that a test should exercise the caller's 404 path.
- `throw redirect\(['"](?P<url>[^'"]+)['"]` — from `next/navigation`; signals a Next-semantic 3xx redirect (handled by the RSC framework). Tests should verify the redirect target.
- `throw unauthorized\(\s*\)` — from `next/navigation` (v15+); signals a 401 path rendering `unauthorized.tsx`.
- `throw forbidden\(\s*\)` — from `next/navigation` (v15+); signals a 403 path rendering `forbidden.tsx`.

For each occurrence, record the containing function and whether a test references both the function and the Next-semantic control-flow (either by checking the response status for Route Handlers, or by checking that the `not-found` / `error` boundary rendered the expected page).

### `Gap-Validate`

**Defer to [`nodejs-core.md § Gap-Validate`](nodejs-core.md#grep-patterns-per-gap-class)** — Zod / Yup / Joi / `class-validator` patterns apply unchanged. Zod is the dominant Next.js choice; Zod schemas co-located with Route Handlers or Server Actions are a strong `HC-10` carve-out signal (see Carve-outs above).

### Auth matrix enumeration (Next.js additions)

**Extends [`nodejs-integration.md § Auth matrix enumeration`](nodejs-integration.md#auth-matrix-enumeration).** Next.js-specific patterns add to the `nodejs-integration.md` endpoint-enumeration pass:

- **Proxy / middleware `matcher` config** — parsed above; enumerate the matched path classes as the protected-path envelope (every path matching a `matcher` pattern is subject to whatever auth logic the proxy / middleware implements).
- **Auth.js v5 `auth()` call-sites** — grep Route Handlers, Server Components, Server Actions, and proxy / middleware files for `(?:const|let)\s+\w+\s*=\s*await\s+auth\s*\(\s*\)` OR `auth\s*\(\s*(req|request)` (API-route variant that takes `req`/`res`). Each call-site is an auth-enforcement point; the enclosing handler / component is a protected endpoint.
- **Legacy NextAuth v4 `getServerSession`** — grep for `getServerSession\s*\(\s*(req|authOptions|options)` anywhere in the SUT. Record as legacy; recommend migration to `auth()` per [authjs.dev migration guide](https://authjs.dev/getting-started/migrating-to-v5).
- **`useSession()` on the client** — hook from `next-auth/react`. Not an auth-enforcement point (runs in the browser; a determined user can bypass) but indicates the rendering branches on session state; relevant to component tests.

Cross-reference against the required auth scenario columns from
`nodejs-integration.md` and add scheme-specific cells when applicable. For
Next.js, pay special attention to Auth.js session cookies, proxy / middleware
matchers, Server Actions with cookie-backed forms, CSRF protection implemented
in route handlers or actions, logout invalidation, SameSite cross-site
behavior, and session rotation after sign-in or privilege changes. A
Playwright or Route Handler test that only proves valid navigation or
valid-token success is `referenced-weak` for these negative cells. Emit
`Gap-AuthZ` rows for uncovered cells.

### Migration upgrade-path enumeration

**Defer entirely to [`nodejs-integration.md § Migration upgrade-path enumeration`](nodejs-integration.md#migration-upgrade-path-enumeration).** No Next.js-specific migration system.

### Confidence annotations (Next.js additions)

- `Gap-API` Server Actions: **high** (the `'use server'` directive is a hard declaration of the surface).
- `Gap-API` Server Components: **medium** (some are render-only pass-throughs with no independently testable logic; verify via mutation testing or manual read before acting).
- `Gap-Route` Route Handlers: **high** (file location + method export pattern is deterministic).
- `Gap-Route` proxy / middleware `matcher`: **high** for the matcher's enumerated path classes; `medium` for whether the proxy's logic for a given class is covered (the matcher is the envelope; the logic inside the proxy function is the thing tests must cover).

---

## Mutation tool

Inherits from [`nodejs-core.md § Mutation tool`](nodejs-core.md#mutation-tool). Stryker Mutator JS is the tool for the whole JS/TS stack, including Next.js. Next.js-specific known-limitation caveats (App Router SWC pipeline, React Server Components) are already documented in [`nodejs-core.md § 5. Known SUT limitations § Next.js App Router source files`](nodejs-core.md#5-known-sut-limitations).

**When a Next.js SUT is audited:** the limitation "probable but not officially documented" applies. First-audit workflow: attempt the run; if it succeeds, remove the caveat from `nodejs-core.md`. If it fails with RSC-related errors (CS-type errors in the Stryker cleartext reporter, or a `transformer` failure in the Jest / Vitest runner output), report state C and recommend the extract-to-library workaround — move the server-side logic under `app/` to a plain TS library outside `app/`, reference it from Server Components / Route Handlers / Server Actions as thin adapters, and mutate the library.
