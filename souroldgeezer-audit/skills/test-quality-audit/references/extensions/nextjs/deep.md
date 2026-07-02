# Extension: Next.js — deep (Deep mode only)

Loaded only in Deep mode. For smells, detection, and carve-outs see [core](core.md).

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../../../SKILL.md) — step 2.5 of the deep-mode workflow. This section **extends** `../nodejs/core.md`'s five-class enumeration with Next.js-specific patterns. Classes deferred entirely to `../nodejs/core.md` are marked as such; classes with additional Next.js patterns below are layered *on top of* the `../nodejs/core.md` patterns (both fire; de-duplicate at the audit-output stage).

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

**Defer to [`../nodejs/deep.md § Gap-Migration`](../nodejs/deep.md#grep-patterns-per-gap-class)** — applies unchanged.

### `Gap-Throw` (Next.js additions)

**Defer to [`../nodejs/deep.md § Gap-Throw`](../nodejs/deep.md#grep-patterns-per-gap-class) for `throw new *Error` patterns.** Next.js additions:

- `throw notFound\(\s*\)` — from `next/navigation`; signals a Next-semantic 404 (renders `not-found.tsx`). The exception type is internal; what matters is that a test should exercise the caller's 404 path.
- `throw redirect\(['"](?P<url>[^'"]+)['"]` — from `next/navigation`; signals a Next-semantic 3xx redirect (handled by the RSC framework). Tests should verify the redirect target.
- `throw unauthorized\(\s*\)` — from `next/navigation` (v15+); signals a 401 path rendering `unauthorized.tsx`.
- `throw forbidden\(\s*\)` — from `next/navigation` (v15+); signals a 403 path rendering `forbidden.tsx`.

For each occurrence, record the containing function and whether a test references both the function and the Next-semantic control-flow (either by checking the response status for Route Handlers, or by checking that the `not-found` / `error` boundary rendered the expected page).

### `Gap-Validate`

**Defer to [`../nodejs/deep.md § Gap-Validate`](../nodejs/deep.md#grep-patterns-per-gap-class)** — applies unchanged. Zod schemas co-located with Route Handlers or Server Actions are a strong `HC-10` carve-out signal (see Carve-outs above).

### Auth matrix enumeration (Next.js additions)

**Extends [`../nodejs/integration.md § Auth matrix enumeration`](../nodejs/integration.md#auth-matrix-enumeration).** Next.js-specific additions:

- **Proxy / middleware `matcher` config** — parsed above; enumerate the matched path classes as the protected-path envelope (every path matching a `matcher` pattern is subject to whatever auth logic the proxy / middleware implements).
- **Auth.js v5 `auth()` call-sites** — grep Route Handlers, Server Components, Server Actions, and proxy / middleware files for `(?:const|let)\s+\w+\s*=\s*await\s+auth\s*\(\s*\)` OR `auth\s*\(\s*(req|request)` (API-route variant that takes `req`/`res`). Each call-site is an auth-enforcement point; the enclosing handler / component is a protected endpoint.
- **Legacy NextAuth v4 `getServerSession`** — grep for `getServerSession\s*\(\s*(req|authOptions|options)` anywhere in the SUT. Record as legacy; recommend migration to `auth()` per [authjs.dev migration guide](https://authjs.dev/getting-started/migrating-to-v5).
- **`useSession()` on the client** — hook from `next-auth/react`. Not an auth-enforcement point (runs in the browser; a determined user can bypass) but indicates the rendering branches on session state; relevant to component tests.

Cross-reference against `../nodejs/integration.md` auth scenario columns. Next.js attention areas: Auth.js session cookies, proxy / middleware matchers, Server Actions with cookie-backed forms, CSRF, logout invalidation, SameSite, session rotation after sign-in or privilege changes. Valid-navigation or valid-token-only tests → `referenced-weak`. Emit `Gap-AuthZ` rows for uncovered cells.

### Migration upgrade-path enumeration

**Defer to [`../nodejs/integration.md § Migration upgrade-path enumeration`](../nodejs/integration.md#migration-upgrade-path-enumeration)** — applies unchanged.

### Confidence annotations (Next.js additions)

- `Gap-API` Server Actions: **high** (the `'use server'` directive is a hard declaration of the surface).
- `Gap-API` Server Components: **medium** (some are render-only pass-throughs with no independently testable logic; verify via mutation testing or manual read before acting).
- `Gap-Route` Route Handlers: **high** (file location + method export pattern is deterministic).
- `Gap-Route` proxy / middleware `matcher`: **high** for the matcher's enumerated path classes; `medium` for whether the proxy's logic for a given class is covered (the matcher is the envelope; the logic inside the proxy function is the thing tests must cover).

---

## Mutation tool

Inherits from [`../nodejs/deep.md § Mutation testing`](../nodejs/deep.md#mutation-testing). Stryker Mutator JS is the tool for the whole JS/TS stack, including Next.js. Next.js-specific known-limitation caveats (App Router SWC pipeline, React Server Components) are already documented in [`mutation-nodejs.md § 5. Known SUT limitations § Next.js App Router source files`](../../procedures/mutation-nodejs.md#5-known-sut-limitations).

**When a Next.js SUT is audited:** the limitation "probable but not officially documented" applies. First-audit workflow: attempt the run; if it succeeds, remove the caveat from `../nodejs/core.md`. If it fails with RSC-related errors (CS-type errors in the Stryker cleartext reporter, or a `transformer` failure in the Jest / Vitest runner output), report state C and recommend the extract-to-library workaround — move the server-side logic under `app/` to a plain TS library outside `app/`, reference it from Server Components / Route Handlers / Server Actions as thin adapters, and mutate the library.
