# Extension: Node.js / TypeScript — core

Shared core for the Node.js / TypeScript test-quality-audit extension. This file is loaded **whenever a Node.js project is detected in the audit target**, before step 0b (rubric selection). It owns everything that is not rubric-exclusive: detection signals, test-type dispatch, test-double classification, rubric-neutral smells, carve-outs, SUT surface enumeration, determinism verification, and the Stryker Mutator JS mutation tool declaration.

Rubric-exclusive content lives in the rubric addons:

- [`nodejs-unit.md`](nodejs-unit.md) — `Applies to: unit` smells (React Testing Library implementation-selectors, module-level mocking of owned collaborators, etc.).
- [`nodejs-integration.md`](nodejs-integration.md) — `nodejs.I-*` smells, auth matrix enumeration, migration upgrade-path enumeration (Prisma / Drizzle / TypeORM / Knex).
- [`nodejs-e2e.md`](nodejs-e2e.md) — Playwright-primary E2E smells and positive signals; Cypress and WebdriverIO covered as carve-outs only.

Covers Jest, Vitest, Mocha, Node's built-in `node:test` runner, Sinon, testdouble, React Testing Library + `@testing-library/user-event`, fast-check, and the four dominant Node ORMs (Prisma, Drizzle, TypeORM, Knex). Playwright / Cypress / WebdriverIO routing lives here; per-stack E2E smells live in [`nodejs-e2e.md`](nodejs-e2e.md). Stryker Mutator JS is declared as the mutation tool.

## Detection signals

Load this extension when the audit target contains any of:

- `package.json` at any depth with one of the following in `dependencies` or `devDependencies`:
  - Test runners: `jest`, `@jest/globals`, `vitest`, `vitest/globals`, `mocha`, `ava`.
  - Assertion / matcher libraries: `chai`, `expect`, `@testing-library/jest-dom`.
  - Test doubles: `sinon`, `testdouble`.
  - Component testing: `@testing-library/react`, `@testing-library/vue`, `@testing-library/svelte`, `@testing-library/dom`, `@testing-library/user-event`.
  - Property-based: `fast-check`, `@fast-check/vitest`, `@fast-check/jest`, `jsverify`.
  - Contract / HTTP: `supertest`, `msw`.
  - Containers: `testcontainers`, any `@testcontainers/*` scoped package.
  - E2E: `@playwright/test`, `playwright`, `cypress`, `webdriverio`, `puppeteer`.
  - Mutation: `@stryker-mutator/core`.
- Runner config files at any depth: `jest.config.{js,ts,cjs,mjs,json}`, `vitest.config.{js,ts,cjs,mjs,mts,cts}`, `.mocharc.{js,cjs,mjs,json,yml,yaml}`, `ava.config.{js,cjs,mjs}`.
- `.ts` / `.tsx` / `.js` / `.mjs` / `.cjs` file with `import { test } from 'node:test'` or `require('node:test')` — identifies the Node built-in runner.
- A `"test"` script in `package.json` that invokes any of: `jest`, `vitest`, `mocha`, `ava`, `node --test`, `tsx --test`, `stryker`.

Detection glob shortcuts: `**/package.json`, `**/*.{test,spec}.{js,jsx,ts,tsx,mjs,cjs}`, `**/__tests__/**/*.{js,jsx,ts,tsx}`, `**/test/**/*.{js,ts}`, `**/tests/**/*.{js,ts}`.

### Language-flavor flags (affect downstream behavior)

Record these on detection; several smells and the mutation-tool config depend on them:

- **TS flag.** `tsconfig.json` present anywhere in the target tree. Gates `nodejs.LC-1` (type coercion of mock) and `nodejs.LC-2` (`@ts-expect-error` / `@ts-ignore` in test), and signals the need for `@stryker-mutator/typescript-checker` in the mutation tool install.
- **ESM flag.** `package.json` with `"type": "module"` OR runner config file using `.mjs` extension OR source files using `.mjs` extensions. Changes Stryker's runner selection (see § Mutation tool § Known SUT limitations).
- **Monorepo flag.** `package.json` with a `workspaces` field (array of glob patterns) OR `pnpm-workspace.yaml` OR `lerna.json` OR `nx.json` OR `turbo.json`. Changes detection scope: each workspace is audited independently, and mutation testing runs per-workspace rather than at the repo root.

---

## Test type detection signals

Consumed by [SKILL.md § 0b (Rubric selection)](../../skills/test-quality-audit/SKILL.md). Declares which patterns route a Node.js test to the integration or E2E rubric instead of the unit rubric. A test with no matching integration or E2E signal defaults to the unit rubric — explicit and backwards compatible.

### Integration rubric signals — sub-lane A (in-process)

Route the test to integration sub-lane A when any of these are present:

- **Project-level.** Directory name contains `integration` (case-insensitive, e.g. `tests/integration/`, `__tests__/integration/`), OR the `package.json` "test:integration" script is the one invoking the test.
- **Construction of real adjacent dependencies.**
  - `testcontainers` import: `import { GenericContainer, Network } from 'testcontainers'` or any `@testcontainers/<db>` scoped package (`@testcontainers/postgresql`, `@testcontainers/mysql`, `@testcontainers/mongodb`, `@testcontainers/redis`, `@testcontainers/kafka`, etc.).
  - ORM clients constructed against a real database: `new PrismaClient(...)` / `drizzle({ client: new Pool(...) })` / `new DataSource({ type: 'postgres', ... })` (TypeORM) / `knex({ client: 'pg', ... })` where the connection target is **not** `:memory:` / `sqlite::memory:` / `better-sqlite3` in-memory.
  - Raw driver clients against a localhost port: `new Pool({ host: 'localhost' | '127.0.0.1', port: 5432..5439 })` (Postgres), `createConnection(...)` (MySQL), `new MongoClient('mongodb://localhost:27017')`, `new Redis({ host: 'localhost', port: 6379 })` (ioredis / redis).
- **Supertest against an in-process app.** `import request from 'supertest'` plus `request(app)` where `app` is an Express / Fastify / Hono / Koa / Nest application instance. This is sub-lane A (in-process) when the app is constructed in the test file; sub-lane B when it targets a deployed URL string.
- **Framework-specific integration harnesses.** `Test.createTestingModule(...)` from `@nestjs/testing`; `FastifyInstance` injection via `fastify.inject({ method, url, payload })`.

### Integration rubric signals — sub-lane B (out-of-process contract)

Route the test to integration sub-lane B when any of these are present:

- **Supertest against a deployed URL.** `request('https://api.example.com')` or `request('http://localhost:3000')` where the target is a URL string, not an app instance — exercises the SUT through its public HTTP surface.
- **Raw `fetch(url, ...)` / `node:http` / `undici` client calls against a deployed base URL** with assertions on response status / body / headers, typically driven by an `API_BASE_URL` env var.
- **MSW (Mock Service Worker) in pass-through mode.** `import { setupServer } from 'msw/node'` with handlers using `passthrough()` or `bypass()` to hit real upstreams. This is sub-lane B territory — you're contract-testing against a real remote service.
- **Pact / consumer-driven contract test.** `import { Pact } from '@pact-foundation/pact'` or `import { PactV3, MatchersV3 }`.

### Unit rubric signals (default)

Route to the unit rubric (the default) when:

- The test instantiates the SUT directly (`const sut = new OrderService(mockRepo, mockClock)`) with `jest.fn()` / `vi.fn()` / `sinon.stub` dependencies, and
- The file does not import or construct any of the integration-rubric markers above, and
- The file does not import any of the E2E-rubric markers below.

### E2E rubric signals

Route the test to the E2E rubric when any of these are present:

- **Project-level.** Directory named `e2e/` / `end-to-end/` / `playwright/` / `cypress/`, OR a top-level `playwright.config.{ts,js,mjs}` / `cypress.config.{ts,js,mjs}` / `wdio.conf.{ts,js,mjs}` config file.
- **Framework imports.**
  - Playwright: `import { test, expect } from '@playwright/test'` or `import { chromium, firefox, webkit } from 'playwright'`.
  - Cypress: any `cy.*` call in the test body, `describe(...)` loaded by Cypress runner config, or `import 'cypress'`.
  - WebdriverIO: `import { browser, $, $$ } from '@wdio/globals'` or `wdio.conf` presence.
  - Puppeteer: `import puppeteer from 'puppeteer'` plus `browser.newPage()`.
- **Browser-session construction.** `browser.newContext()` / `context.newPage()` / `page.goto(...)` / `cy.visit(...)` / `$('#selector').click()`.

Once a file is routed to E2E, classify each test into a sub-lane (`F` / `A` / `P` / `S`) using the signals in [SKILL.md § 0b step 5](../../skills/test-quality-audit/SKILL.md):

- `@tag('a11y')` / `test.describe('a11y', ...)` / `@axe-core/playwright` / `cypress-axe` / `axe-core` import → sub-lane **A**.
- `@tag('perf')` / `web-vitals` npm package / `PerformanceObserver` / Lighthouse CI import → sub-lane **P**.
- `@tag('security')` / assertions on CSP / cookie jar / cross-origin iframe / tampered-cookie behavior → sub-lane **S**.
- Otherwise → sub-lane **F**.

### Mixed-file handling

When a single test file contains multiple patterns — some tests use only mocked dependencies, some construct `testcontainers`, some drive a browser via `@playwright/test` — classify each test method individually. A test is unit, integration, *or* E2E under exactly one rubric; never more than one. The audit records the chosen rubric (and, for E2E, the sub-lane) per test so the reader can audit the dispatch itself.

---

## Test double classification

Required reading for auditors: [../../docs/quality-reference/unit-testing.md § 7.1](../../docs/quality-reference/unit-testing.md) — the Fowler taxonomy (Dummy / Stub / Spy / Mock / Fake) that core smells like `HC-5` and `HC-6` are scoped to.

Jest, Vitest, Sinon, `node:test` `mock`, and `testdouble` all produce test doubles through one construction syntax but serve different roles in the taxonomy. Classify each double before applying interaction-pinning smells. The rule: **a double is a Mock only when the test body verifies it** (asserts on calls received). A double that is only set up to return values, never verified, is a Stub.

### Jest

- **Dummy:** `jest.fn()` passed in but never interrogated (no `.toHaveBeenCalled*` anywhere).
- **Stub:** `jest.fn().mockReturnValue(x)` / `jest.fn().mockResolvedValue(x)` / `jest.fn().mockRejectedValue(err)` / `jest.fn().mockImplementation(fn)` with **no** subsequent `.toHaveBeenCalled*` assertion on the same fn.
- **Spy:** `jest.spyOn(obj, 'method')` without `.mockImplementation` / `.mockReturnValue` (records calls, delegates to real).
- **Mock (verified stub):** any `.toHaveBeenCalled()` / `.toHaveBeenCalledWith(...)` / `.toHaveBeenCalledTimes(N)` / `.toHaveBeenLastCalledWith(...)` / `.toHaveBeenNthCalledWith(...)` on the double anywhere in the test body. This is the lens under which `HC-5`, `HC-6`, `nodejs.HC-1` apply.
- **Auto-mock:** `jest.mock('path', factory?)` at module level. Every exported function of the mocked module becomes a `jest.fn()`; interpret per-export using the rules above. `jest.mocked(mod)` is a typed wrapper — see `nodejs.POS-1`.

### Vitest

API-compatible with Jest. Map `jest.*` → `vi.*` for every primitive:

- **Stub:** `vi.fn().mockReturnValue(x)` / `vi.fn().mockResolvedValue(x)` / `vi.fn().mockImplementation(fn)` without verification.
- **Spy:** `vi.spyOn(obj, 'method')` without override.
- **Mock:** any `.toHaveBeenCalled*` on the double.
- **Auto-mock:** `vi.mock('path', factory?)`. `vi.mocked(mod)` is the typed wrapper.
- **Hoisted factory:** `vi.hoisted(() => ...)` — required when the factory references variables declared above `vi.mock`. Classification of the produced doubles follows the normal rules.

### Sinon

- **Stub:** `sinon.stub(obj, 'method').returns(x)` / `.resolves(x)` / `.rejects(err)` / `.callsFake(fn)` with no `sinon.assert.called*` anywhere in the test body.
- **Spy:** `sinon.spy(obj, 'method')` or `sinon.spy()` — records calls, delegates to real if on an existing object.
- **Mock (pre-declared):** `const mock = sinon.mock(obj); mock.expects('method').once().withArgs(...)` — pre-declared expectation, verified via `mock.verify()`. Always a Mock regardless of whether `verify()` appears.
- **Mock (verification-style):** a Stub or Spy that has `sinon.assert.calledWith(stub, ...)` / `sinon.assert.calledOnce(stub)` / `stub.calledOnceWith(...)` / `stub.calledWith(...)` asserted on it.

### `node:test` (Node built-in)

- **Stub:** `t.mock.fn(original?, implementation?)` or `context.mock.fn(...)` without reading `.mock.calls`.
- **Mock:** same fn with `assert.strictEqual(fn.mock.callCount(), N)` / iterating `fn.mock.calls` with strict count expectations.
- **Module mock:** `t.mock.module('path', { exports: { ... } })` (Node 22.3+, stability 1.0 — experimental). Requires Node to be started with `--experimental-test-module-mocks`. `{ namedExports, defaultExport }` are accepted but deprecated in favor of `{ exports: { default, ... } }`. Per-export classification follows the rules above. See https://nodejs.org/api/test.html#class-mockmodulecontext.
- **Timer mock:** `t.mock.timers.enable({ apis: ['setTimeout'] })` and `t.mock.timers.tick(ms)` — see `nodejs.POS-5`.

### testdouble (`testdouble` / `td`)

- **Stub:** `td.replace('path', { method: td.func() })` or `td.when(obj.method()).thenReturn(x)` without a `td.verify(...)` call.
- **Mock:** any `td.verify(obj.method(...))` / `td.verify(obj.method(...), { times: N })` on the double.

### Fakes (working implementations)

Types named `Fake*`, `InMemory*`, or any custom class that implements the real interface with a recording / in-memory / shortcut body are Fowler **fakes**, not mocks. Examples: `pg-mem` in-memory Postgres, `fake-indexeddb`, a hand-written `InMemoryOrderRepository` matching the production `OrderRepository` interface. Do not apply `HC-5` / `HC-6` / `nodejs.HC-1` to fakes. Fakes are a positive under the integration rubric — see `nodejs.I-POS-1`.

### Interpretation rules

- **Mixed use in one test.** If a test body constructs a `jest.fn()` that is treated as a stub (no `.toHaveBeenCalled*`) *and* another `jest.fn()` that is verified (mock), classify each double independently. Smells like `HC-5` apply only to the mocked collaborator.
- **One mock per finding.** If a test has three mock collaborators and only one is over-verified, the finding names the offending collaborator rather than marking the entire test as `HC-6`.
- **`jest.mock('path')` resolution.** The first argument of `jest.mock(...)` / `vi.mock(...)` must be resolved against the project's module graph to classify the smell. If the path resolves under `node_modules/`, the mock target is a process boundary (no smell — carve-out). If it resolves inside the repo's `src/` / `app/` / `lib/` tree, the mock target is same-layer code; apply `nodejs.HC-1` (same-package scope leak) or the unit-rubric `nodejs.LC-U1` depending on the relationship to the SUT.
- **Auto-mock of a module that exports only types / constants.** Not a double — suppress all interaction-pinning smells.

---

## Framework-specific high-confidence smells (`nodejs.HC-*`)

These smells apply under both the unit and integration rubrics (`Applies to: unit, integration`). Unit-only framework smells live in [`nodejs-unit.md`](nodejs-unit.md); integration-only framework smells live in [`nodejs-integration.md`](nodejs-integration.md).

### `nodejs.HC-1` — `jest.mock('<relative-path>')` / `vi.mock('<relative-path>')` on an in-repo module in the SUT's same-layer scope

**Applies to:** `unit, integration`

**Detection:** `(jest|vi)\.mock\(['"](?P<path>\.{1,2}/[^'"]+)['"]` at module level of a test file. Resolve `path` against the test file's directory. The mock target is **same-layer** when it resolves under the SUT's own parent directory or a sibling `src/` path (i.e. the author's own code, not an external package).

**Smell:** module-level mocking of the SUT's own collaborators pins the internal boundary. Refactors that move logic between the SUT and its collaborator break the test without changing observable behavior. The test is characterization of the current module graph.

**Carve-out — platform boundaries:** do not flag when the mock target is `fetch`, `node:http`, `node:https`, `undici`, `node-fetch`, `axios`, `got`, an `@octokit/*` package, an AWS / Azure / GCP SDK, `nodemailer`, a database driver (`pg`, `mysql2`, `mongodb`, `redis`, `ioredis`), `fs` / `node:fs`, or any package resolved from `node_modules/`. These are process boundaries. Carved out here to share the rule across the whole Node stack.

**Carve-out — Next.js platform modules** (when `nextjs` extension is loaded): do not flag when the mock target is `next/navigation`, `next/headers`, `next/cache`, `next/font/*`, `server-only`, or `client-only`.

**Example (smell):**
```ts
// In OrderServiceTests.ts, SUT at ../services/OrderService.ts
jest.mock('../services/pricing');
import { OrderService } from '../services/OrderService';
// OrderService imports ./pricing; the mock replaces the collaborator
```

**Rewrite (intent):** inject the collaborator as a constructor / function parameter rather than importing it. The test provides a `jest.fn()` at call time; the mock target is a parameter, not a module path.

---

### `nodejs.HC-2` — Vacuous interaction assertion: `.toHaveBeenCalledWith(expect.anything())` or all `expect.any(*)` args

**Applies to:** `unit, integration`

**Detection:** a `.toHaveBeenCalledWith(...)` whose arguments are entirely `expect.anything()` / `expect.any(Function)` / `expect.any(Object)` without any concrete value assertion. Refines core `HC-6`.

**Smell:** the test asserts that the collaborator was called *with something*, which is equivalent to asserting it was called at all. The expected-value information has been deleted. Any refactor changing the argument shape will still pass.

**Example (smell):**
```ts
expect(repo.save).toHaveBeenCalledWith(expect.anything(), expect.any(Object));
```

**Rewrite (intent):** either assert on a specific field of the argument (`.toHaveBeenCalledWith(expect.objectContaining({ orderId: 'abc-123' }))`) or — preferably — replace the interaction assertion with an assertion on the SUT's return value or a published side effect.

---

### `nodejs.HC-3` — Floating promise in a test body

**Applies to:** `unit, integration`

**Detection:** a call returning `Promise<T>` at the top level of a test body without `await`, `return`, or a `.then` / `.catch` chain. Heuristics: any method called `*Async`, any method whose resolved type is `Promise<T>`, any `fetch(...)`, any `supertest(...).get(...).send(...)` without a trailing `.expect(...)`. Also flag when the `async` test function body contains such a call on its own statement line and the test subsequently asserts without awaiting.

**Smell:** a floating promise means the assertion runs before the async operation resolves. Tests pass because nothing fails synchronously; the actual failure is a silent unhandled rejection reported in the next tick (often suppressed by the test runner). Mechanically equivalent to no assertion.

**Example (smell):**
```ts
test('creates an order', async () => {
    service.createOrder(input); // returns a promise — not awaited
    expect(repo.save).toHaveBeenCalled();
});
```

**Rewrite (intent):**
```ts
test('creates an order', async () => {
    await service.createOrder(input);
    expect(repo.save).toHaveBeenCalled();
});
```

**Note:** projects using `@typescript-eslint/no-floating-promises` catch this at lint time. When that rule is configured in the project and the test file is not ignored, downgrade severity to `info` — the lint has already spoken.

---

### `nodejs.HC-4` — Real-clock read in a test body without fake timers installed

**Applies to:** `unit, integration` — refines core `HC-11` for the Node idiom.

**Detection:** any of the following in a test body: `new Date()`, `Date.now()`, `performance.now()`, `process.hrtime()`, `process.hrtime.bigint()` — with **no** preceding `jest.useFakeTimers()` / `vi.useFakeTimers()` / `sinon.useFakeTimers(...)` / `t.mock.timers.enable(...)` in the same test or its `beforeEach`. The presence of the fake-timers install anywhere upstream in the current test's scope is sufficient to suppress the flag.

**Smell:** the test reads the real clock. Tests that use the real clock pass when the author runs them and fail at midnight, on daylight-saving transitions, on slow CI runners, or at time-zone boundaries. Core `HC-11` covers the general case; this refines detection to the Node idiom.

**Carve-out:** if the test calls `Date.now()` / `new Date().toISOString()` solely to generate a unique identifier (e.g. `const id = \`test-${Date.now()}\``) and the value is not used in an assertion, do not flag. The canonical unique-id generation pattern is benign.

**Rewrite (intent):** install fake timers (`vi.useFakeTimers(); vi.setSystemTime(new Date('2026-01-01T00:00:00Z'))`) and drive time explicitly — see `nodejs.POS-5`.

---

### `nodejs.HC-5` — Structural-only assertion on complex return: `.toEqual({...lots of expect.any(...)})`

**Applies to:** `unit, integration` — refines core `LC-2`.

**Detection:** a `.toEqual(...)` / `.toMatchObject(...)` whose expected object has **more than one** field and **every** field value is `expect.any(*)` / `expect.anything()` / `expect.stringMatching(/.*/)` / `expect.arrayContaining([])` with no concrete values.

**Smell:** the test asserts the shape of the return but not its content. Any implementation that returns something with those field types passes, including broken ones that return default-constructed stand-ins.

**Rewrite (intent):** either (a) assert the whole object against a spec-derived expected value, or (b) replace the structural assertion with targeted assertions on the fields whose values the SUT actually computes.

---

### `nodejs.HC-6` — `spyOn(Math, 'random')` / env-var mock with a pasted-literal return

**Applies to:** `unit, integration`

**Detection:** `jest.spyOn(Math, 'random').mockReturnValue(\s*(?P<value>0?\.\d+)\s*)` or `Math.random = jest.fn(() => <literal>)` or `process.env.<NAME> = '<literal>'` in the test body where `<literal>` appears as a magic number / string with no named-constant declaration or linked spec comment. Also matches the Vitest / Sinon analogs.

**Smell:** the test pins the SUT to a specific randomness / environment snapshot. The literal was almost certainly copied from a single observed run — characterization. Refactors that change how the seed or env value feeds the SUT break the test.

**Rewrite (intent):** inject the randomness source or env reader as a dependency; the test provides a deterministic generator. For env vars, use a typed config object passed into the SUT constructor.

---

### `nodejs.HC-7` — `.resolves.*` / `.rejects.*` without `await`

**Applies to:** `unit, integration`

**Detection:** `expect\((?P<promise>[^)]+)\)\.(resolves|rejects)\.` without a preceding `await` or `return` on the `expect(...)` call.

**Smell:** Jest's and Vitest's `.resolves` / `.rejects` matchers return a thenable that must be awaited (or returned from the test function) for the assertion to actually run. An un-awaited `.resolves.toBe(...)` / `.rejects.toThrow(...)` silently skips — the test passes regardless of the promise's outcome. Jest's own docs call this out: see https://jestjs.io/docs/asynchronous (§ ".resolves / .rejects") — "Be sure to return the assertion — if you omit this `return` statement, your test will complete before the promise returned from `fetchData` is resolved ... potentially leading to false positives or unexpected test behavior."

**Example (smell):**
```ts
test('resolves to user', () => {
    expect(getUser(1)).resolves.toEqual({ id: 1, name: 'Ada' }); // missing await
});
```

**Rewrite (intent):**
```ts
test('resolves to user', async () => {
    await expect(getUser(1)).resolves.toEqual({ id: 1, name: 'Ada' });
});
```

---

## Framework-specific low-confidence smells (`nodejs.LC-*`)

These smells apply under both the unit and integration rubrics. Unit-only low-confidence smells live in [`nodejs-unit.md`](nodejs-unit.md).

### `nodejs.LC-1` — Type coercion of a hand-built mock to the SUT's type (TS-only)

**Applies to:** `unit, integration`

**Detection:** (only when the TS flag is set) `as unknown as (?P<type>[A-Z]\w+)` in a test body, OR `as (?P<type>jest\.Mocked<\w+>|Mocked<\w+>)` applied to a hand-built object literal that was **not** produced by `jest.mocked(mod)` / `vi.mocked(mod)`.

**Why low-confidence:** the test is lying to the type-checker about what it built. If the SUT's collaborator interface evolves — new methods, renamed fields, optional → required — the hand-built mock doesn't get the signal, and the test passes a type-check against the old shape.

**Rewrite (intent):** use `jest.mocked(mod)` or `vi.mocked(mod)` after `jest.mock(...)` so the mock carries the real type; for partial hand-builts, use `Partial<T>` + `as T` only at the injection boundary with a comment explaining why.

---

### `nodejs.LC-2` — `@ts-expect-error` / `@ts-ignore` in test body

**Applies to:** `unit, integration`

**Detection:** `// @ts-expect-error` or `// @ts-ignore` anywhere inside a test function body.

**Why low-confidence:** sometimes legitimate (the test deliberately exercises a compile-time-invalid call to verify a runtime guard). More often hides a drift between the test's intent and the SUT's evolved signature; the test passes because TypeScript stops checking at the comment.

**Rewrite (intent):** if the test exercises a runtime guard against bad input, use `as never` / `as unknown` with a linked comment citing the guard; otherwise, fix the shape and remove the directive.

---

### `nodejs.LC-3` — `.only` / `fdescribe` / `fit` committed

**Applies to:** `unit, integration`

**Detection:** `(it|test|describe)\.only\(` / `^\s*fdescribe\(` / `^\s*fit\(` / `^\s*ftest\(` in a test file.

**Why low-confidence:** the author left a focused-run marker in. The suite still passes locally but runs only the focused test, suppressing everything else. On CI, some configurations fail closed (good); others silently run only the focused test (bad).

**Rewrite (intent):** remove the `.only` / `f*` prefix before committing. Configure the test runner to fail on `.only` when present. Vitest defaults `allowOnly` to `false` under CI (auto-detected via `std-env`) and `true` locally — set `allowOnly: false` in `vitest.config` to fail everywhere, or use the `--allowOnly` CLI flag. Jest does not ship a first-party `.only`-forbidden flag; an ESLint rule (`jest/no-focused-tests` from `eslint-plugin-jest`) is the idiomatic enforcement.

---

### `nodejs.LC-4` — `.skip` / `xit` / `.todo` with no linked issue

**Applies to:** `unit, integration` — refines core `LC-9`.

**Detection:** `(it|test|describe)\.(skip|todo)\(` or `^\s*xit\(` / `^\s*xtest\(` where the test or an immediately-preceding comment contains no URL, issue reference (`#\d+`, `ISSUE-\d+`), ticket identifier, or flake history pointer.

**Why low-confidence:** a skip without a documented reason becomes the permanent home for the flake. Refines `LC-9` for the Jest / Vitest / Mocha idiom.

**Rewrite (intent):** add a comment linking to the issue that will re-enable the test, or remove the test entirely if its intent is unclear.

---

### `nodejs.LC-5` — Custom matcher used with no reachable `expect.extend` declaration

**Applies to:** `unit, integration`

**Detection:** a `.toBeXyz(...)` / `.matchXyz(...)` call whose matcher name is not one of the built-in Jest / Vitest / Chai matchers, with **no** `expect.extend({ toBeXyz: ... })` reachable from the test file's import graph (imports of `jest.setup.{js,ts}` / `vitest.setup.{js,ts}` / `globalSetup` resolve the declaration if present).

**Why low-confidence:** the matcher is either broken (the declaration was lost) or registered through a mechanism the audit can't see (a global-setup import resolved at runtime). Flag for manual review; the author can dismiss if the registration is truly centralized.

**Rewrite (intent):** import the declaration directly from the setup file, or add a top-of-file comment pointing at it. Make the registration discoverable from the test file.

---

### `nodejs.LC-6` — `beforeEach` mutates `let`-bound SUT without `afterEach` reset

**Applies to:** `unit, integration` — refines core `HC-8`.

**Detection:** `let\s+(?P<name>\w+)` at describe / file scope followed by a `beforeEach` that mutates the binding (`<name> = new ...` / `<name>.push(...)` / `<name>.someProp = ...`), with **no** `afterEach` reset in the same describe block.

**Why low-confidence:** shared mutable state is a flake source. The intent was usually "fresh SUT per test" but the test relies on `beforeEach` order rather than ownership. A parallel test runner (Vitest) or sharded CI can expose this as order-dependence.

**Rewrite (intent):** `const sut = <factory>()` inside each test body, or `beforeEach(() => { sut = new ... })` paired with `afterEach(() => { sut = null! })`.

---

### `nodejs.LC-7` — `it.each` / `test.each` missing contract-derived boundary rows

**Applies to:** `unit, integration` — refines core `LC-11`.

**Detection:** an `it.each(...)` / `test.each(...)` / `describe.each(...)` whose data has a numeric parameter (`number`, `bigint`), string parameter, collection parameter (`T[]`, `string[]`, `Set<T>`, `Map<K, V>`), parser input, enum/state value, or schema-validated field. Collect every row. First inspect the visible contract:

- Zod / Yup / Joi / class-validator rules such as `.min(...)`, `.max(...)`, `.length(...)`, `.email()`, `.regex(...)`, `@MinLength`, `@MaxLength`, and custom `.refine(...)`.
- Branch predicates and guard clauses around numeric, string, collection, date, or enum inputs.
- Route params and request-body schemas.
- TypeScript literal unions / enums when runtime code branches on them.

Flag when no row covers the contract-derived boundary coverage items, or when rows cover only generic sentinels while richer edges are visible. Examples:

- A schema `.min(6).max(15)` needs `5/6` and `15/16`; `''` alone is `sentinel-only`.
- A quantity rule `1..10` needs `0/1` and `10/11`; `5` plus `[]` on an unrelated parameter is partial at best.
- A `test.each` that repeats valid roles but never covers a forbidden role is positive-only for auth/authorization partitions.

When no richer contract is visible, fall back to generic sentinel signals:

- Numeric: `0`, `1`, `-1`, `Number.MAX_SAFE_INTEGER`, `Number.MIN_SAFE_INTEGER`, `Infinity`, `NaN` (scale to context — `NaN` / `Infinity` apply to `number` but not `bigint`).
- String: `""` (empty), single-character literal, `null` / `undefined` (only where the signature allows it).
- Collection: `[]`, `[singleItem]`, `null` / `undefined` (where the signature allows).

**Why low-confidence:** boundary-value analysis is standard, but the test may be intentionally scoped to a narrow partition. Always report `Boundary evidence` as `contract-derived`, `partial`, `sentinel-only`, or `unknown`.

**Rewrite (intent):** add rows or separate `test(...)` cases for each boundary the function is specified to handle.

---

## Framework-specific positive signals (`nodejs.POS-*`)

### `nodejs.POS-1` — `jest.mocked(mod)` / `vi.mocked(mod)` typed auto-mock wrapper

**Applies to:** `unit, integration`

**Detection:** `import { ... }` from a module followed by `jest.mock('<path>')` (or `vi.mock('<path>')`) plus `const mocked = jest.mocked(<Import>)` (or `vi.mocked`) at the top of the test file. Assertions use `mocked.someExport.mockReturnValue(...)` with full type safety.

**Why positive:** typed auto-mocks track the real module's exports through the TS checker. When the real module changes signature, the test's mocked call-site fails to compile — the drift is visible at commit time rather than at runtime on CI. Strictly better than hand-building a mock object and casting.

---

### `nodejs.POS-2` — `expect.extend(...)` with domain-invariant custom matchers

**Applies to:** `unit, integration`

**Detection:** `expect.extend({ <matcherName>: ... })` registered in a setup file, where `<matcherName>` names a domain invariant (`toBeAValidIsbn`, `toBeMonotonicallyIncreasing`, `toContainAllRequiredFields`) rather than a structural shape.

**Why positive:** a domain-named custom matcher expresses intent directly. Tests read as specifications (`expect(result).toBeAValidIsbn()`) instead of structural probes.

---

### `nodejs.POS-3` — Property-based test harness (`fast-check`, `@fast-check/vitest`, `jsverify`)

**Applies to:** `unit, integration` — refines core `POS-9`.

**Detection:** `import fc from 'fast-check'` plus `fc.assert(fc.property(fc.integer(), ..., (a, b) => ...))`, OR `import { test } from '@fast-check/vitest'` with `test.prop(...)`, OR `import jsc from 'jsverify'` with `jsc.forall(...)`.

**Why positive:** a property-based test expresses a domain invariant over a generated input space instead of pinning a finite set of examples. Correct implementations pass for the whole domain; characterization tests written from observed output cannot be phrased this way.

---

### `nodejs.POS-4` — `it.each` / `test.each` with meaningfully varied expected values

**Applies to:** `unit, integration` — refines core `POS-4`.

**Detection:** an `it.each(...)` / `test.each(...)` whose rows produce distinct expected values (not all identical — that would be core `LC-8`) and map to named equivalence classes or contract-derived boundary values.

**Why positive:** the parameterization is doing real work — each row is a different specification statement. When rows include contract-derived boundary values, this signals disciplined test design. Do not award this signal for arbitrary sentinel rows when a richer contract is visible.

---

### `nodejs.POS-5` — Fake-timer install + `setSystemTime` pattern

**Applies to:** `unit, integration`

**Detection:** `jest.useFakeTimers()` (or `vi.useFakeTimers()` / `sinon.useFakeTimers({...})` / `t.mock.timers.enable({ apis: [...] })`) followed by `jest.setSystemTime(new Date('<ISO>'))` / `vi.setSystemTime(new Date('<ISO>'))` / `clock.tick(ms)` in Arrange.

**Why positive:** the idiomatic way to make time-sensitive code deterministic in Node.js. Tests pin the "now" and advance time explicitly via `vi.advanceTimersByTime(ms)` / `jest.advanceTimersByTime(ms)` / `clock.tick(ms)`. Not an `HC-11` smell — this is the fix.

---

### `nodejs.POS-6` — MSW at the process boundary instead of module-level HTTP mocking

**Applies to:** `unit, integration`

**Detection:** `import { setupServer } from 'msw/node'` plus `const server = setupServer(...handlers)` plus `beforeAll(() => server.listen())` / `afterAll(() => server.close())` / `afterEach(() => server.resetHandlers())`. Handlers use `http.get(...)` / `http.post(...)` from `msw` to define the contract.

**Why positive:** MSW intercepts at the HTTP-request level — requests leave the SUT code path fully intact and are caught at the network boundary. No `jest.mock('axios')` / `jest.mock('node-fetch')` required. The contract the test declares is the real-world contract (status, body, headers) rather than a module's internal API.

---

### `nodejs.POS-7` — `@testing-library/react` accessible-name queries + `userEvent.setup()` (component testing idiom)

**Applies to:** `unit` — primarily a unit-rubric positive for React component tests.

**Detection:** any of `screen.getByRole(...)`, `screen.getByLabelText(...)`, `screen.getByPlaceholderText(...)`, `screen.getByText(...)`, `screen.findByRole(...)` plus `import userEvent from '@testing-library/user-event'` with `const user = userEvent.setup()` per test (v14+ idiom).

**Why positive:** accessible-name locators are the priority-1 queries per React Testing Library guidance — they read as user-observable behavior. `userEvent.setup()` per test provides a fresh interaction session with shared keyboard / pointer state across calls in the same test, and is the blessed v14+ pattern. Tests written this way specify what the user can do, not how the DOM is structured.

---

## Carve-outs

Patterns that look like core smells but are idiomatic in Node.js / TypeScript and must not be flagged:

- **Do not flag `HC-5`** (mock-return-then-mock-called-with) when the mock target is a process boundary — `fetch`, `node:http`, `node:https`, `undici`, `node-fetch`, `axios`, `got`, `@octokit/*`, AWS / Azure / GCP SDKs, `nodemailer`, DB drivers (`pg`, `mysql2`, `mongodb`, `redis`, `ioredis`), `fs` / `node:fs`. These are legitimate mocks at the process boundary; the same rule applies to `nodejs.HC-1` (see its own carve-out above).

- **Do not flag `HC-11`** (hardcoded clock values) when fake timers are installed in the same test body or a preceding `beforeEach` — `jest.useFakeTimers()` / `vi.useFakeTimers()` / `sinon.useFakeTimers(...)` / `t.mock.timers.enable(...)`. That is the idiomatic way to control time in Node.js.

- **Do not flag `LC-1`** (mocking same-layer code) when the mocked type is an interface owned by the tested module *and* the project has a documented "test via seams" / "interface-segregation" convention (e.g. a `CLAUDE.md`, `README.md`, or ADR stating that interfaces exist specifically for testability). Ask before flagging if ambiguous.

- **Do not flag `LC-7`** (excessive setup) when the setup is constructing a `Testcontainers` stack (`new GenericContainer(...).withEnvironment(...).start()`), `supertest(app)` with a non-trivial app, `new NestApplication(...)` / `Test.createTestingModule(...).compile()` (safety net for NestJS projects until a dedicated extension exists), a `@playwright/test` `webServer` config, or a `vitest.config` `globalSetup` bringing up a real backend for an E2E run. Under the new dispatch model (see [SKILL.md § 0b (Rubric selection)](../../skills/test-quality-audit/SKILL.md)), these are **routing signals into the integration or E2E rubric** — tests using them should be audited under that rubric where heavy setup is expected, not the unit rubric at all. This carve-out stays in force as a **safety net** for cases where the dispatch is uncertain.

- **Do not flag `HC-10`** (snapshot tests pinning unspecified output) when the snapshot target is:
  - A JSON response whose schema is published via an OpenAPI document (any `openapi.{yaml,json}`) in the repo, OR
  - A `@testing-library/jest-dom` accessible-tree snapshot (output of `prettyDOM(container)` or similar), OR
  - A Zod / Yup / Joi schema parse result where the schema is co-located with the SUT and exported from the same module — the schema **is** the contract.

- **Do not flag `nodejs.HC-1`** (module-level mock of same-layer code) when the mocked module's path resolves to `node_modules/` (external package — by definition a process / library boundary).

---

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../../skills/test-quality-audit/SKILL.md) — step 2.5 of the deep-mode workflow. This section declares the Node.js / TypeScript grep patterns the audit agent uses to enumerate testable symbols in a SUT and cross-reference them against a test project. Applies under both the unit and integration rubrics; not run under the E2E rubric.

### SUT identification

For a given test project or test directory:

1. Start at the test file's location and walk up to the nearest enclosing `package.json`.
2. Read that `package.json`'s `main`, `module`, `exports`, and `types` fields. These declare the package's public entry points.
3. If the package has `"workspaces"` (monorepo), also resolve every workspace-relative import path used by tests in the target to identify adjacent SUT packages.
4. The SUT surface is the transitive import graph reachable from the declared entry points, excluding any file under `node_modules/`, `dist/`, `build/`, `.next/`, `out/`, `coverage/`, `__tests__/`, `test/`, `tests/`, `e2e/`.

If the repo has no `package.json` `exports` / `main` field and no TS `index.ts`, fall back to: every `.ts` / `.tsx` / `.js` / `.mjs` / `.cjs` file under `src/` / `lib/` / `app/` (whichever exists) is candidate SUT surface.

### Grep patterns per gap class

All patterns are case-sensitive ripgrep expressions applied to the SUT's source files (after the exclusions above). Each match returns a symbol identifier plus `file:line`.

**`Gap-API` — public exports (functions, classes, constants).** Multi-line aware. Detection patterns:

- Named function / async function: `^\s*export\s+(async\s+)?function\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(`.
- Named class: `^\s*export\s+(abstract\s+)?class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(extends|implements|\{)`.
- Named const / let / var with function / arrow-function value: `^\s*export\s+(const|let|var)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*[:=]` — keep the match when the RHS is a function expression (`= function`, `= async function`, `= (...) =>`, `= async (...) =>`).
- Default export: `^\s*export\s+default\s+(?:async\s+)?(?:function|class)(?:\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*))?`.
- Re-exports: `^\s*export\s+\{\s*(?P<names>[^}]+)\s*\}\s+from\s+'` — split `<names>` on comma; each is a re-export from the referenced module.

Exclude matches whose declaration is marked `@internal` via a preceding JSDoc comment `/** @internal */`, or whose file path matches `*.internal.ts`.

**`Gap-Route` — HTTP route registrations.** Detection patterns:

- Express / Koa / Hono: `(?P<app>\w+)\.(?P<method>get|post|put|delete|patch|all|use)\s*\(\s*['"](?P<route>[^'"]+)['"]` where `<app>` is not a reserved name.
- Fastify: `(?P<app>\w+)\.(?P<method>get|post|put|delete|patch|route)\s*\(\s*\{[^}]*url\s*:\s*['"](?P<route>[^'"]+)['"]` for object-form, or `(?P<app>\w+)\.(?P<method>get|post|put|delete|patch)\s*\(\s*['"](?P<route>[^'"]+)['"]` for shorthand.
- NestJS controllers: `@Controller\s*\(\s*['"]?(?P<prefix>[^'"\)]*)['"]?\s*\)` plus `@(?P<method>Get|Post|Put|Delete|Patch)\s*\(\s*['"]?(?P<path>[^'"\)]*)['"]?\s*\)` — concatenate prefix + path.
- tRPC: `(?P<router>\w+Router)\s*=\s*router\s*\(\s*\{` plus nested `.(query|mutation)\(` — capture the procedure name.

**`Gap-Migration` — database migration files.** Detection patterns:

- **Prisma:** glob `prisma/migrations/*/migration.sql`. Migration identifier is the parent directory name (e.g. `20260101120000_add_users_table`).
- **Drizzle:** glob `drizzle/*.sql` (the default `out:` path set by `drizzle-kit generate`). Identifier is the filename stem. Also read `drizzle.config.{ts,js}` to detect a non-default `out:` path and glob accordingly.
- **TypeORM:** glob `**/migrations/*.ts` (or `**/migrations/*.js`) for classes that match `class\s+(?P<name>[A-Z]\w+)\s+implements\s+MigrationInterface`. Identifier is the class name.
- **Knex:** glob `**/migrations/*.{ts,js}` for modules exporting `async function up(knex)` and `async function down(knex)` (or `exports.up = async function(knex)` for CJS). Identifier is the filename stem.

**`Gap-Throw` — exception / error throw sites.** Detection patterns:

- `throw\s+new\s+(?P<type>[A-Z][A-Za-z0-9_]*(Error|Exception))\s*\(` — capture the error type.
- Record the containing function / method name by walking up from the match to the nearest enclosing `function`, `async function`, arrow-function assigned to a const, or class method. Report as `<methodName>: <ErrorType>`.
- Exclude bare re-throws (`throw err;` / `throw error;`).

**`Gap-Validate` — validation schema declarations.** Detection patterns:

- **Zod:** `z\.(object|string|number|bigint|boolean|array|tuple|record|union)\s*\(` — capture the containing `const` binding and the chained method calls for `.min(...)` / `.max(...)` / `.email()` / `.url()` / `.regex(...)` / `.refine(...)`. A schema with chained refinements is a validation contract.
- **Yup:** `(?:yup|Yup)\.(object|string|number|array|mixed)\s*\(` with chained `.required()` / `.min()` / `.max()` / `.email()` / `.url()` / `.matches()`.
- **Joi:** `Joi\.(object|string|number|array|boolean|date)\s*\(` with chained `.required()` / `.min()` / `.max()` / `.email()` / `.uri()` / `.pattern()`.
- **class-validator decorators:** `@(IsEmail|IsUrl|IsString|IsNumber|IsInt|IsPositive|IsNegative|MinLength|MaxLength|Length|Matches|IsDate|IsArray|ArrayMinSize|ArrayMaxSize|ValidateNested)\s*\(` on a class property declaration. Capture the containing class name and the property name.

### Cross-reference matching

For each enumerated symbol, search the test project (test glob from § Detection signals, excluding `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, `StrykerOutput/` / `.stryker-tmp/`) for at least one of:

- **`Gap-API`** — `covered-strong` only when the symbol name appears as an identifier and the same test asserts a return value, published side effect, error, state, or domain outcome. Word-boundary identifier presence (`\bcreateOrder\b`) by itself is `referenced-weak`; import/setup-only presence is `referenced-incidental`.
- **`Gap-Route`** — `covered-strong` only when the route template appears as a string literal and the same test asserts the route's published contract: status plus body/header/auth/domain outcome, state change, validation error, or problem code. Partial route matches and status-only happy-path assertions are `referenced-weak`, not coverage.
- **`Gap-Migration`** — the migration identifier appears as a path literal or string in any test body, or a test imports / executes the migration file directly.
- **`Gap-Throw`** — both the error type (e.g. `NotFoundError`) *and* the containing method name appear in the same test method body, and the assertion expects that error or the public error envelope. If only one appears, or the test only awaits the happy path, the throw site is a probable gap.
- **`Gap-Validate`** — the validated field name (e.g. `email`) appears in a test body that also references the schema's containing binding or class and intentionally omits or violates the field. For Zod, look for `<schemaName>.safeParse(...)` / `<schemaName>.parse(...)` calls with an invalid payload plus an assertion on failure. Valid-payload-only route tests are `referenced-weak`.

### Known indirect-coverage patterns (carve-outs)

These patterns suppress a false-positive `Gap-API` entry:

- A service method `createOrder` is covered indirectly when a Route Handler / controller / tRPC procedure that wraps it has a test, and the service type is imported / constructed inside that wrapper. Search for imports of the SUT symbol in handler files, then check whether the handler file's tests assert the handler's contract. If so, record the service method as "indirectly covered via `<handler>`" and suppress the `Gap-API` entry. If the handler test is status-only or happy-path-only, keep the service as `referenced-weak`.
- A Zod schema `UserSchema` is covered indirectly when any Route Handler test sends a request body that exercises the schema's fields and asserts validation success/failure. Valid-body-only tests can satisfy success coverage but do not suppress `Gap-Validate` entries for missing invalid-field branches.

### Confidence annotations

- `Gap-API`: **medium** — indirect coverage via controllers / handlers / facade exports is common in Node.js projects.
- `Gap-Route`, `Gap-Migration`: **high** — routes and migrations are registered by string / file identity with few indirect-coverage paths.
- `Gap-Throw`: **medium** — generic error-path tests often exercise the method without naming the exception type.
- `Gap-Validate`: **high** on serialization-layer schemas (Zod / Yup / Joi at the Route Handler boundary); **medium** on internal validators.

### Recommended `--mutate` follow-up

When the gap report lists a probable `Gap-API` finding on a SUT shape that Stryker JS supports, the audit agent may suggest a targeted mutation run to confirm: `npx stryker run --mutate "src/services/pricing.ts"` (fast — seconds).

---

## Determinism verification

Consumed by [SKILL.md § Determinism verification](../../skills/test-quality-audit/SKILL.md) — step 4.5 of the deep-mode workflow. Applies under unit and integration rubrics; not run under the E2E rubric (browser-dominated suites are too expensive to rerun cheaply).

### Cheap-rerun command

Pick the command based on the detected runner. Run the non-E2E test script twice, each with structured output for diffing:

**Jest:**
```bash
npx jest --silent --reporters=default --reporters=jest-junit \
  --testPathIgnorePatterns='/e2e/'
# Set JEST_JUNIT_OUTPUT_FILE=./.test-determinism/run1/junit.xml via env.
```

**Vitest:**
```bash
npx vitest run --reporter=junit --outputFile=./.test-determinism/run1/junit.xml \
  --exclude='**/e2e/**'
```

**`node:test`:**
```bash
node --test --test-reporter=junit --test-reporter-destination=./.test-determinism/run1/junit.xml
```

**Mocha:**
```bash
npx mocha --reporter mocha-junit-reporter \
  --reporter-option "mochaFile=./.test-determinism/run1/junit.xml" \
  'test/**/*.test.js'
```

Run twice (swap `run1` for `run2` on the second run). Diff the JUnit XML outputs: compare every `<testcase>` element's `pass/fail/skip` status between the two runs. Any test that diverges is a runtime-proven flake finding.

### Gating

- **Project size:** skip and recommend targeted rerun of top-N slowest tests when the test project has ≥ 500 test methods. Determine via `grep -rc "^\s*\(it\|test\)\.\?\(only\|skip\)\?\s*[('`]" '<test-dir>'` or similar.
- **Total elapsed time from run 1:** if run 1 takes more than 60 seconds, warn the user before running run 2. Abort if the user declines.
- **E2E projects:** never run. Browser-driven suites require different tooling (see [SKILL.md § Determinism verification](../../skills/test-quality-audit/SKILL.md)).

---

## Mutation tool

The core skill runs mutation testing conditionally in deep mode (see [SKILL.md § Mutation testing (conditional)](../../skills/test-quality-audit/SKILL.md)). It uses the subsections below to decide whether Stryker Mutator JS is available, how to run it, and whether the SUT is a shape the tool can handle. Applies under unit and integration rubrics; never run under the E2E rubric.

### 1. Tool name and link

**[StrykerJS (Stryker Mutator)](https://stryker-mutator.io/docs/stryker-js/introduction/)** — mutation testing for JavaScript and TypeScript. Runner-neutral (Jest / Vitest / Mocha / Karma / Cucumber all supported via dedicated runner plugins).

### 2. Install instructions

Install Stryker plus the runner matching the detected test runner. From the repo root:

```bash
npm install --save-dev @stryker-mutator/core
# Pick one based on the detected runner:
npm install --save-dev @stryker-mutator/jest-runner       # Jest
npm install --save-dev @stryker-mutator/vitest-runner     # Vitest
npm install --save-dev @stryker-mutator/mocha-runner      # Mocha
# TypeScript projects — adds compile-error elimination:
npm install --save-dev @stryker-mutator/typescript-checker
```

Create a minimal `stryker.conf.mjs` at the repo root:

```js
/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  packageManager: 'npm',
  reporters: ['clear-text', 'progress', 'html', 'json'],
  testRunner: 'vitest',                 // or 'jest' / 'mocha'
  coverageAnalysis: 'perTest',
  checkers: ['typescript'],             // omit on JS-only projects
  tsconfigFile: 'tsconfig.json',
  mutate: ['src/**/*.ts', '!src/**/*.test.ts', '!src/**/*.spec.ts'],
};
```

The default reporter set is `['clear-text', 'progress', 'html']`; adding `json` gives the audit agent a machine-readable report alongside the defaults. See https://stryker-mutator.io/docs/stryker-js/configuration/#reporters-string for the full reporter list.

Add `.stryker-tmp/` and `reports/mutation/` to `.gitignore`. Commit `stryker.conf.mjs`. Future contributors run `npm install` to get the pinned Stryker version from `package-lock.json`.

**Monorepo note:** in a workspaces repo, run Stryker from inside each workspace (with its own `stryker.conf.mjs`), not at the repo root — the mutation pass needs per-workspace `package.json` / runner context to resolve correctly.

### 3. Detection command

Check whether Stryker is installed and invokable from the audit target. The audit agent runs this before attempting a mutation run and skips the step gracefully if it exits non-zero.

```bash
# Side-effect-free check: prefer the local install (project-pinned) over global.
test -x node_modules/.bin/stryker \
  || npx --no-install stryker --version >/dev/null 2>&1
```

In a workspaces repo, run the detection inside the specific workspace being audited, not at the repo root.

### 4. Run command

Run from the **repo root or workspace root** (wherever `stryker.conf.mjs` lives).

**Baseline (full project):**

```bash
npx stryker run --reporters json,html,clear-text
```

- `--reporters json` produces `reports/mutation/mutation.json` — this is what the audit agent parses to extract scores and surviving-mutant details.
- `--reporters html` produces `reports/mutation/mutation.html` — browser-viewable report with inline surviving-mutant highlights for the user.
- `--reporters clear-text` produces the summary table printed at the end of the run.

**PR-scoped (fast):**

```bash
npx stryker run --since main
```

Mutates only files changed since `main`. Use when the audit target is a PR diff rather than the full suite.

**Single-file (demo / targeted):**

```bash
npx stryker run --mutate "src/services/pricing.ts"
```

Useful for demonstrating mutation testing on one file without waiting for a full run. Typical runtime: seconds.

**Useful flags:**

- `--mutationScore <threshold>` — configure the `thresholds.break` value in config. Used for CI gating, not audits.
- `--concurrency <N>` — override default parallelism. Default is half the available CPU cores; Stryker JS is IO-heavy and setting `concurrency: N` matching the runner's own worker count is often faster.
- `--incremental` — only re-mutate files changed since the last recorded incremental run (`reports/stryker-incremental.json`). Fastest for iterative local use once a baseline exists.
- `--dryRunOnly` — run the initial unmutated test pass and stop. Useful for debugging `stryker.conf.mjs` without paying for the full mutation run.
- `--logLevel debug` (or `trace`) — enable diagnostic logging when troubleshooting a failed run.

### 5. Known SUT limitations

Stryker JS cannot mutate every JavaScript / TypeScript SUT shape. Before attempting a run, the audit agent should check for each of these patterns and skip with the documented workaround if any match.

#### ESM-only packages (`"type": "module"` with no CJS interop layer)

- **How to detect:** `package.json` declares `"type": "module"` AND the project's runner config is Jest (Jest's ESM support is behind `--experimental-vm-modules` as of v29). Vitest is native ESM and doesn't hit this. The audit agent reads `package.json` and detects this combination.
- **Root cause:** Stryker's Jest runner sandboxes mutants using CJS module resolution. An ESM-only SUT — one that uses `import ... from '...'` with no bundler step and expects native Node ESM — trips the runner's module-loader assumptions. Vitest's runner is ESM-native and handles this cleanly.
- **Workaround:** if the project is Jest + ESM, either (a) migrate the test runner to Vitest (native ESM, often a one-hour migration) and use `@stryker-mutator/vitest-runner`, or (b) transpile-to-CJS via a Stryker `files` / `testRunnerNodeArgs` configuration hook — document the hook in `stryker.conf.mjs`. If neither is possible, skip with state C citing ESM-only + Jest.

#### TypeScript path aliases (`compilerOptions.paths`)

- **How to detect:** `tsconfig.json` declares a non-empty `compilerOptions.paths` mapping (e.g. `{ "@/*": ["src/*"] }`).
- **Root cause:** Stryker's `@stryker-mutator/typescript-checker` reads `tsconfig.json` at startup, but paths resolution only works when `tsconfigFile` is set in `stryker.conf.mjs`. Without it, mutants that import via `@/*` aliases fail to compile, producing false-positive `CompileError` mutants.
- **Workaround:** set `tsconfigFile: 'tsconfig.json'` in `stryker.conf.mjs` (or the path to the project-relative tsconfig). For monorepos, set the per-workspace tsconfig. This is a config fix, not a skip — the audit should recommend the one-line config change before skipping.

#### Monorepo workspaces (`package.json` with `"workspaces"`, pnpm-workspace.yaml, turbo.json, nx.json)

- **How to detect:** repo root has any of `package.json` with `"workspaces"`, `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`.
- **Root cause:** Stryker resolves the test runner and its deps relative to the directory where `stryker.conf.mjs` lives. Running at the repo root in a workspaces monorepo picks up the root `node_modules/` but tests live in `packages/*/test/` and depend on per-workspace dependencies.
- **Workaround:** run Stryker inside each workspace with its own `stryker.conf.mjs`. The audit should iterate over each workspace matching the detection signals and run Stryker separately per workspace, aggregating the per-workspace JSON reports.

#### Next.js App Router source files (`app/**/*.{ts,tsx}`) — probable but not officially documented

- **How to detect:** the `nextjs` extension is loaded and the target includes files under `app/`.
- **Root cause (provisional):** Next.js's App Router files are compiled by the Next SWC pipeline at build time, which applies Server Component / Client Component boundary transforms (`'use client'` / `'use server'` splits, RSC payload generation, server-only module stripping). Stryker's runner compiles mutants through the Jest / Vitest runner's transformer, which does not apply these Next transforms. Mutants of files under `app/` may compile but fail at runtime, or fail compilation entirely.
- **This is probable, not officially documented.** Stryker JS's docs do not currently call out Next.js App Router as an unsupported target (as of the reference audit — 2026-04). First-audit workaround: attempt the run. If it succeeds, remove this caveat and report the success; if it fails with RSC-related errors, treat as state C and recommend the extract-to-library workaround below.
- **Workaround (if confirmed unsupported):** extract server-side logic (pure services, validators, formatters) from `app/` into a plain TS library (e.g. `lib/` or a separate workspace package). Reference the library from `app/` — your Server Components / Route Handlers / Server Actions become thin adapters. Mutate the library, not `app/`. Matches the Blazor WASM workaround in [`dotnet-core.md`](dotnet-core.md).

#### Files the project intentionally excludes from tests

- **How to detect:** the test runner's config has `testPathIgnorePatterns` / `exclude` / `coveragePathIgnorePatterns` listing files or directories (type-only `.d.ts` files, generated code, vendored code).
- **Root cause:** files with no tests always produce `NoCoverage` mutants. They're not a Stryker limitation — they're a known gap that mutation testing correctly surfaces.
- **Workaround:** no workaround needed; the `NoCoverage` report entries are the valuable output. Filter them into the "no-coverage discoveries" subsection of the deep-mode output.

### 6. Output parser notes

Stryker's JSON reporter writes the standard [mutation-testing-elements report schema](https://github.com/stryker-mutator/mutation-testing-elements/blob/master/packages/report-schema/src/mutation-testing-report-schema.json) (`schemaVersion: "1.x"`). Fields the audit agent reads:

- **Report location:** `reports/mutation/mutation.json` relative to the config-file directory (configurable via the `jsonReporter.fileName` option). The HTML report lives at `reports/mutation/mutation.html`.
- **Top-level fields:** `schemaVersion`, `thresholds: { high, low }`, `framework`, `system`, `config`, `files`, `testFiles`. There is **no** top-level `mutationScore` in the JSON; the score is computed from the mutant status counts (the cleartext reporter does print `Mutation score: N.NN%` and `Mutation score based on covered code: N.NN%` — `/reports/html/index.html` also displays the computed score).
- **Per-file extraction:** iterate `files` (an object keyed by file path relative to the project root). For each file, iterate `mutants` and group by `status`. Meaningful statuses: `Killed`, `Survived`, `NoCoverage`, `Timeout`, `Ignored`, `CompileError`, `RuntimeError`, `Pending`.
- **Surviving-mutant details:** for each surviving mutant, extract `location.start.line` / `location.start.column`, `mutatorName`, `replacement`, and `statusReason` (populated by some reporters). This is the raw material for the "audit-vs-mutation disagreement" reconciliation in step 5 of deep-mode output. The mutant's `coveredBy` / `killedBy` arrays reference test IDs in the top-level `testFiles`.
- **Score derivation:** mutation score = `killed / (killed + survived + timeout)` (excludes `NoCoverage` / `Ignored` / `CompileError` / `RuntimeError`); mutation score including no-coverage = `killed / (killed + survived + timeout + noCoverage)`. Use the same formula the CLI prints.
- **Files entirely without tests:** filter for files whose mutant list has zero `Killed` + zero `Survived` + zero `Timeout` entries (all `NoCoverage` or `Ignored`). These are the "no test touches this file" findings the static audit cannot see.

### When to run it

**Always run in deep mode when the detection command succeeds**, regardless of which smells the static audit found. Mutation testing's highest-value output is the audit-vs-mutation disagreement: files rated `strong` by static audit that have surviving mutants. Those disagreements only surface if you run the tool unconditionally on a successful-audit suite.

If the suite has many `HC-1` / `HC-3` / `HC-5` / `HC-6` / `nodejs.HC-2` / `nodejs.HC-5` findings, the mutation run is especially valuable — those smells all indicate tests that execute code without verifying it, which mutation testing surfaces mechanically — but this is not a gating criterion.
