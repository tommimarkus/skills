# Extension: Next.js — integration-rubric addon

Addon to [nextjs-core.md](nextjs-core.md) loaded **only when step 0b selects the integration rubric**. Carries framework-specific smells and procedures that apply exclusively under the integration rubric:

- Integration-only high-confidence smells (`nextjs.I-HC-*`) for Server Components, Server Actions, Route Handlers, and proxy / middleware tests.
- Integration-only low-confidence smells and positive signals.
- An **auth-matrix extension** layering Auth.js v5 `auth()` / proxy `matcher` enumeration on top of [`nodejs-integration.md § Auth matrix enumeration`](nodejs-integration.md#auth-matrix-enumeration).
- **No Next.js-specific migration-upgrade-path procedure** — defers entirely to [`nodejs-integration.md § Migration upgrade-path enumeration`](nodejs-integration.md#migration-upgrade-path-enumeration). Next.js does not introduce its own migration system.

**Prerequisite:** [`nodejs-core.md`](nodejs-core.md), [`nextjs-core.md`](nextjs-core.md), and [`nodejs-integration.md`](nodejs-integration.md) must already be loaded. This file refines integration-rubric behaviour on top of all three. `nextjs.I-*` smells are additional to `nodejs.I-*` smells, not replacements. The rubric-neutral smells in `nextjs-core.md` (`nextjs.HC-1` through `HC-4`, `LC-1` through `LC-2`, `POS-1` through `POS-5`) apply under the integration rubric too — they declare `Applies to: unit, integration`. Do not re-list them here.

---

## Framework-specific high-confidence integration smells (`nextjs.I-HC-*`)

### `nextjs.I-HC-A1` — Server Component / Server Action test with DB client constructed at module scope

**Applies to:** `integration` — refines `nodejs.I-HC-A2` for the Next.js-specific case where the `'use server'` boundary makes the DB-client position especially load-bearing.

**Detection:** a test file targets `app/**/page.{tsx,jsx}` (Server Component) or `app/**/actions.{ts,js}` / a file with `'use server'` directive (Server Action), AND the test declares `const prisma = new PrismaClient()` / `const db = drizzle(...)` / `new DataSource(...)` / `knex(...)` at module scope and reuses it across multiple test methods without per-test reset.

**Smell:** Server Components and Server Actions execute in Next.js's request-scoped runtime, where each request gets its own DB context. A test that mirrors "production" wiring must recreate the same per-request isolation; a module-scope client + reuse across tests is the test-quality equivalent of mutating a shared Cache API key across requests in production — it "works" but masks real-world scoping behaviour. Matches `nodejs.I-HC-A2` but with a sharper Next.js framing.

**Rewrite (intent):** per-test transaction with rollback (`prisma.$transaction(async tx => { ... })`), per-test truncate, or per-test schema. For Server Actions that call `revalidatePath` / `revalidateTag`, also verify the revalidation side effect — see `nextjs.I-HC-A2` below.

---

### `nextjs.I-HC-A2` — Server Action test doesn't verify `revalidatePath` / `revalidateTag` side effect

**Applies to:** `integration` — refines core `I-HC-A10`.

**Detection:** a test of a Server Action (file at `app/**/actions.{ts,js}` or containing `'use server'`) where the action's source calls `revalidatePath(...)` or `revalidateTag(...)` from `next/cache`, AND the test body neither mocks these functions with an interaction assertion nor asserts on the observable consequence (a subsequent `fetch` with the revalidated tag returns fresh data).

**Smell:** `revalidatePath` / `revalidateTag` are the mechanism by which a Server Action signals "the data you cached is stale; serve fresh on next read". A Server Action that writes to the DB but forgets to call `revalidateTag` leaves cached consumer routes displaying stale data. A test that exercises the DB write without verifying the revalidation signal misses half the contract.

**Example (smell):**
```ts
// app/actions.ts
'use server';
export async function updateUser(id: string, data: Partial<User>) {
  await db.user.update({ where: { id }, data });
  revalidateTag(`user:${id}`);  // ← not verified by the test
}

// test (smell)
test('updates the user', async () => {
  await updateUser('u1', { name: 'Ada' });
  const row = await db.user.findUnique({ where: { id: 'u1' } });
  expect(row?.name).toBe('Ada');  // DB side verified; revalidation not
});
```

**Rewrite (intent):** either (a) mock `next/cache`'s `revalidateTag` (carved out as a platform boundary — see `nextjs-core.md § Carve-outs`) and assert `expect(revalidateTag).toHaveBeenCalledWith('user:u1')`, OR (b) E2E-test the full round-trip — this is often cleaner as an `nextjs.E-POS-F2` — but for sub-lane A coverage, the interaction assertion is the idiomatic check.

---

### `nextjs.I-HC-B1` — Route Handler auth test uses a forged `next/headers` cookies mock bypassing the real proxy / middleware chain

**Applies to:** `integration` — refines `nodejs.I-HC-B1`.

**Detection:** a Route Handler test where `jest.mock('next/headers')` / `vi.mock('next/headers')` is used to return a hand-built cookies object that would have *failed* the project's proxy / middleware auth check if the real chain had run — e.g. the test presents a cookie value that wouldn't actually authenticate in production, but the handler accepts it because the mock bypasses validation.

**Smell:** the test lies about what the production request pipeline would accept. Route Handlers in Next.js sit downstream of the proxy / middleware chain, which is where session validation, CSRF checks, and token verification happen. Mocking `cookies()` at the handler level sidesteps that pipeline and makes the test pass for requests that production would reject.

**Rewrite (intent):** either (a) test the handler in isolation against a known-valid session fixture produced by the real session-sign helper (so the cookie would survive the real proxy), OR (b) move the auth coverage to a dedicated proxy / middleware test using `unstable_doesProxyMatch` + the returned `NextResponse.status` (see `nextjs.POS-5`). The handler test then trusts the proxy contract and tests only the handler's logic beyond auth.

---

### `nextjs.I-HC-B2` — Proxy / middleware test asserts only `NextResponse.next()` call vs no-call, without verifying redirect / status

**Applies to:** `integration` — refines `I-HC-B1`.

**Detection:** a test of `proxy.{ts,js}` or `middleware.{ts,js}` that invokes the function with a `NextRequest` and asserts only `expect(res).toBe(NextResponse.next())` OR `expect(res.constructor.name).toBe('NextResponse')` — without additional assertions on `res.status`, `res.headers.get('Location')` (for redirects), `res.headers.get('Set-Cookie')`, or the rewritten URL.

**Smell:** the test passes for any proxy that returns *something*. It doesn't verify that the proxy's decision — pass-through, redirect, rewrite, or block — matches the request's properties. A regression that swaps `NextResponse.redirect('/login')` for `NextResponse.next()` on an unauthenticated request passes this test.

**Rewrite (intent):** use the [`next/experimental/testing/server`](https://nextjs.org/docs/app/api-reference/file-conventions/proxy#unit-testing-experimental) helpers (`isRewrite`, `getRewrittenUrl`, `getRedirectUrl`) — see `nextjs.POS-5` in `nextjs-core.md` and `nextjs.I-POS-2` below. Alternatively, assert on `res.status` / `res.headers.get('Location')` directly for redirect cases.

---

## Framework-specific integration positive signals (`nextjs.I-POS-*`)

### `nextjs.I-POS-1` — Proxy / middleware test with real `NextRequest` + assertion on returned `NextResponse`

**Applies to:** `integration`

**Detection:** a test of `proxy.{ts,js}` / `middleware.{ts,js}` that constructs `new NextRequest(new URL('https://example.com/path'), { ...init })`, awaits the exported `proxy` / `middleware` function's return, and asserts on `res.status` / `res.headers.get('Location')` / `res.headers.get('Set-Cookie')` / `res.cookies.get(...)`.

**Why positive:** the proxy / middleware function is tested through its real contract (a `NextRequest` in, a `NextResponse` out). Collaborator platform APIs (`cookies()`, `headers()`) are exercised through the real request object rather than mocked. Matches `I-POS-6` (asserts on published contract).

---

### `nextjs.I-POS-2` — Proxy / middleware test uses `unstable_doesProxyMatch` to verify `matcher` config

**Applies to:** `integration`

**Detection:** `import { unstable_doesProxyMatch } from 'next/experimental/testing/server'` in a proxy / middleware test file, with at least one call of the form `expect(unstable_doesProxyMatch({ config, nextConfig, url })).toBe(true | false)`. Often paired with `nextjs.I-POS-1` for response-assertion.

**Why positive:** the `matcher` config and the response together define the proxy's contract. Asserting on `doesProxyMatch` alone is incomplete (a matcher that fires correctly but does the wrong thing in the body is still broken — that's `nextjs.I-HC-B2`); asserting on the response alone is incomplete (a response that's correct for the requests the test sent but wouldn't fire for the requests the matcher should intercept is still broken). Testing both proves the routing envelope (what gets intercepted) *and* the logic (what the interception does).

---

## Auth matrix enumeration (Next.js layer)

**Extends [`nodejs-integration.md § Auth matrix enumeration`](nodejs-integration.md#auth-matrix-enumeration).** The `nodejs-integration.md` procedure already enumerates protected endpoints via Passport / Auth.js v5 `auth()` / legacy NextAuth / NestJS guards. This section layers Next.js-specific endpoint sources and auth-scenario detection on top.

### Next.js-specific protected-endpoint sources

In addition to the patterns in `nodejs-integration.md § Protected-endpoint patterns`:

- **Proxy / middleware `matcher` config** — every URL matching any pattern in `export const config = { matcher: ... }` in `proxy.{ts,js}` / `middleware.{ts,js}` is subject to the proxy's auth logic. Enumerate the matcher patterns from the SUT surface enumeration (see `nextjs-core.md § SUT surface enumeration § Gap-Route § Proxy / middleware matcher config`) and treat each as a protected path class.
- **Auth.js v5 `auth()` call-sites in Server Components, Route Handlers, and Server Actions** — grep `(?:const|let)\s+\w+\s*=\s*await\s+auth\s*\(\s*\)` across `app/**/*.{ts,tsx,js,jsx}`. Each hit is an auth-enforcement point; the containing handler / component / action is a protected endpoint.
- **Legacy NextAuth v4 `getServerSession`** — grep `getServerSession\s*\(\s*(req|authOptions|options)` in Route Handlers and `getServerSideProps`. Record as legacy; recommend migration to `auth()` per https://authjs.dev/getting-started/migrating-to-v5.

### Auth-scenario detection — Next.js refinements

Use the core six columns from `nodejs-integration.md` (`anonymous`, `token-expired`, `token-tampered`, `insufficient-scope`, `sufficient-scope`, `cross-user`) plus any scheme-specific cells made applicable by Auth.js sessions, proxy / middleware, cookie-backed Server Actions, or browser form posts. Next.js-specific detection hints:

- **`anonymous`** — a proxy test that invokes the proxy function with a `NextRequest` carrying no `session` cookie and asserts the returned `NextResponse.status === 307` (redirect) with `Location === '/login'` OR `status === 401`. For Route Handlers: same shape but using `GET(new Request(...))`.
- **`sufficient-scope`** — a test that constructs a session token via the project's session-sign helper (typically a `signIn` test-helper, or Auth.js's `encode` with the project's `NEXTAUTH_SECRET`), sets it as the `session` cookie on the `NextRequest`, and asserts on success behaviour.
- **`token-expired`** — for Auth.js sessions with a `maxAge`, craft a session whose `expires` field is in the past. For JWTs used by Auth.js or a custom scheme, standard `exp` in the past.
- **`not-before` / `wrong-issuer` / `wrong-audience` / `wrong-token-type`** — for custom JWT/OIDC schemes, craft tokens with future `nbf`, rejected `iss`, rejected `aud`, or a token type/scheme that the route should reject.
- **`token-tampered`** — a session cookie whose signature doesn't validate (a test-helper that re-signs with a wrong secret, or a cookie whose JSON body has been modified post-signing).
- **`insufficient-scope`** — a session whose `user.role` / `user.permissions` / custom claim lacks the required value for the target endpoint. Auth.js's session-callback often attaches these; the test-helper can produce a session with the missing claim.
- **`cross-user`** — a session for user A presented against a resource belonging to user B (common in multi-tenant or per-user-resource apps). Detect the applicability by checking the endpoint path for per-user segments (`/api/users/<userId>/*`, `/app/users/<userId>/*`) or request bodies with `userId` / `tenantId` / `orgId` fields.
- **`logout-invalidated` / `session-rotation` / `session-fixation` / `csrf-invalid`** — for Auth.js/session-cookie or Server Action form flows, assert logout invalidates the old cookie, privileged session changes rotate where required, a pre-login session id is not retained after login, and missing/invalid CSRF tokens are rejected. Valid-session-only tests are `referenced-weak` for these cells.

### Next.js auth carve-outs

- **Proxy with no `matcher`** — a proxy / middleware file with no `export const config` runs on every request. Treat the protected-path envelope as "all routes"; every endpoint in the app is nominally subject to the proxy's logic. This is rare but legitimate (a logging proxy, a request-tracing proxy); flag as `LC` if no auth logic is present in the proxy body.
- **`useSession()` on the client** — not an auth-enforcement point (the hook reads session state; the client can lie). Exclude from the protected-endpoint enumeration. Relevant only for component tests.
- **`nodejs.I-HC-B1` / `nextjs.I-HC-B1` already fires** — a test flagged under either of these is the same gap as the auth matrix rows. Emit one finding per endpoint, not one per test; reference all applicable codes.

---

## Migration upgrade-path enumeration

**Defer entirely to [`nodejs-integration.md § Migration upgrade-path enumeration`](nodejs-integration.md#migration-upgrade-path-enumeration).** Next.js projects overwhelmingly use one of the four Node-ecosystem ORMs (Prisma, Drizzle, TypeORM, Knex); the enumeration patterns and the three-condition upgrade-path test detection there apply unchanged.

If a Next.js project uses a different migration mechanism (e.g. hand-written SQL invoked from a Server Action, or Supabase / Turso-managed migrations managed via external tooling), flag as a **limitation** in the audit output rather than emitting `Gap-MigUpgrade` — the patterns in `nodejs-integration.md` will miss those migrations entirely, and the audit should say so explicitly.
