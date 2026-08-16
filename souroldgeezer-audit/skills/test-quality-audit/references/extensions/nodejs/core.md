# Extension: Node.js / TypeScript — core

Shared core for the Node.js / TypeScript test-quality-audit extension. This file is loaded **whenever a Node.js project is detected in the audit target**, before step 0b (rubric selection). It owns only what all three rubrics need: detection signals, test-type dispatch, test-double classification, genuinely rubric-neutral smells (`Applies to: unit, integration, e2e`), and carve-outs; deep-mode procedures (SUT surface enumeration, determinism verification, and the Stryker Mutator JS mutation tool declaration) live in [`deep.md`](deep.md).

Rubric-scoped content lives in the addons:

- [`unit-integration.md`](unit-integration.md) — `Applies to: unit, integration` smells that need in-process access to the SUT (module mocking, test doubles, fake timers, parameterised input partitions). Loaded on the unit and integration paths only.
- [`unit.md`](unit.md) — `Applies to: unit` smells (React Testing Library implementation-selectors, module-level mocking of owned collaborators, etc.).
- [`integration.md`](integration.md) — `nodejs.I-*` smells, auth matrix enumeration, migration upgrade-path enumeration (Prisma / Drizzle / TypeORM / Knex).
- [`e2e.md`](e2e.md) — Playwright-primary E2E smells and positive signals; Cypress and WebdriverIO covered as carve-outs only.

Covers Jest, Vitest, Mocha, Node's built-in `node:test` runner, Sinon, testdouble, React Testing Library + `@testing-library/user-event`, fast-check, and the four dominant Node ORMs (Prisma, Drizzle, TypeORM, Knex). Playwright / Cypress / WebdriverIO routing lives here; per-stack E2E smells live in [`e2e.md`](e2e.md). Stryker Mutator JS is the declared mutation tool (declaration lives in [`deep.md`](deep.md)).

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
- **ESM flag.** `package.json` with `"type": "module"` OR runner config file using `.mjs` extension OR source files using `.mjs` extensions. Changes Stryker's runner selection (see [`deep.md § Mutation testing`](deep.md#mutation-testing) and [`mutation-nodejs.md § 5. Known SUT limitations`](../../procedures/mutation-nodejs.md#5-known-sut-limitations)).
- **Monorepo flag.** `package.json` with a `workspaces` field (array of glob patterns) OR `pnpm-workspace.yaml` OR `lerna.json` OR `nx.json` OR `turbo.json`. Changes detection scope: each workspace is audited independently, and mutation testing runs per-workspace rather than at the repo root.

---

## Test type detection signals

Consumed by [SKILL.md § 0b (Rubric selection)](../../../SKILL.md). Declares which patterns route a Node.js test to the integration or E2E rubric instead of the unit rubric. A test with no matching integration or E2E signal defaults to the unit rubric — explicit and backwards compatible.

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

Once a file is routed to E2E, classify each test into a sub-lane (`F` / `A` / `P` / `S`) using the signals in [SKILL.md § 0b step 5](../../../SKILL.md):

- `@tag('a11y')` / `test.describe('a11y', ...)` / `@axe-core/playwright` / `cypress-axe` / `axe-core` import → sub-lane **A**.
- `@tag('perf')` / `web-vitals` npm package / `PerformanceObserver` / Lighthouse CI import → sub-lane **P**.
- `@tag('security')` / assertions on CSP / cookie jar / cross-origin iframe / tampered-cookie behavior → sub-lane **S**.
- Otherwise → sub-lane **F**.

### Mixed-file handling

When a single test file contains multiple patterns — some tests use only mocked dependencies, some construct `testcontainers`, some drive a browser via `@playwright/test` — classify each test method individually. A test is unit, integration, *or* E2E under exactly one rubric; never more than one. The audit records the chosen rubric (and, for E2E, the sub-lane) per test so the reader can audit the dispatch itself.

---

## Test double classification

Required reading for auditors: [unit-testing.md § 7.1](../../../../../docs/quality-reference/unit-testing.md) — the Fowler taxonomy (Dummy / Stub / Spy / Mock / Fake) that core smells like `HC-5` and `HC-6` are scoped to.

Jest, Vitest, Sinon, `node:test` `mock`, and `testdouble` all produce test doubles through one construction syntax but serve different roles in the taxonomy. Classify each double before applying interaction-pinning smells. The rule: **a double is a Mock only when the test body verifies it** (asserts on calls received). A double that is only set up to return values, never verified, is a Stub.

### Jest

- **Dummy:** `jest.fn()` passed in but never interrogated (no `.toHaveBeenCalled*` anywhere).
- **Stub:** `jest.fn().mockReturnValue(x)` / `jest.fn().mockResolvedValue(x)` / `jest.fn().mockRejectedValue(err)` / `jest.fn().mockImplementation(fn)` with **no** subsequent `.toHaveBeenCalled*` assertion on the same fn.
- **Spy:** `jest.spyOn(obj, 'method')` without `.mockImplementation` / `.mockReturnValue` (records calls, delegates to real).
- **Mock (verified stub):** any `.toHaveBeenCalled()` / `.toHaveBeenCalledWith(...)` / `.toHaveBeenCalledTimes(N)` / `.toHaveBeenLastCalledWith(...)` / `.toHaveBeenNthCalledWith(...)` on the double anywhere in the test body. This is the lens under which `HC-5`, `HC-6`, `nodejs.HC-1` apply.
- **Auto-mock:** `jest.mock('path', factory?)` at module level. Every exported function of the mocked module becomes a `jest.fn()`; interpret per-export using the rules above. `jest.mocked(mod)` is a typed wrapper — see `nodejs.POS-1`.

### Vitest

API-compatible with Jest; apply the Jest rules above substituting `vi.*` for `jest.*`. Vitest-specific addition:

- **Hoisted factory:** `vi.hoisted(() => ...)` — required when the factory references variables declared above `vi.mock`. Classification of produced doubles follows the normal rules.

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

- **Mixed use in one test.** Classify each double independently; interaction-pinning smells apply only to the verified collaborator.
- **One mock per finding.** Name the offending collaborator, not the whole test.
- **`jest.mock('path')` resolution.** Resolve the first argument against the module graph. Path under `node_modules/` → process boundary (no smell). Path inside `src/` / `app/` / `lib/` → same-layer code; apply `nodejs.HC-1` or `nodejs.LC-U1`.
- **Auto-mock of a module that exports only types / constants.** Not a double — suppress all interaction-pinning smells.

---

## Framework-specific high-confidence smells (`nodejs.HC-*`)

These apply under **all three** rubrics — each is a defect a browser-driven spec can commit too. Unit+integration smells live in [`unit-integration.md`](unit-integration.md), unit-only in [`unit.md`](unit.md), integration-only in [`integration.md`](integration.md).



### `nodejs.HC-3` — Floating promise in a test body

**Applies to:** `unit, integration, e2e`

**Detection:** a call returning `Promise<T>` at the top level of a test body without `await`, `return`, or a `.then` / `.catch` chain. Heuristics: any method called `*Async`, any method whose resolved type is `Promise<T>`, any `fetch(...)`, any `supertest(...).get(...).send(...)` without a trailing `.expect(...)`. Also flag when the `async` test function body contains such a call on its own statement line and the test subsequently asserts without awaiting.

**Smell:** a floating promise means the assertion runs before the async operation resolves. Tests pass because nothing fails synchronously; the actual failure is a silent unhandled rejection reported in the next tick (often suppressed by the test runner). Mechanically equivalent to no assertion.

**Example (smell):**
```ts
test('creates an order', async () => {
    service.createOrder(input); // returns a promise — not awaited
    expect(repo.save).toHaveBeenCalled();
});
```

**Rewrite (intent):** `await` the async call before asserting.

**Note:** projects using `@typescript-eslint/no-floating-promises` catch this at lint time. When that rule is configured in the project and the test file is not ignored, downgrade severity to `info` — the lint has already spoken.

---

### `nodejs.HC-4` — Real-clock read in a test body without fake timers installed

**Applies to:** `unit, integration, e2e` — refines core `HC-11` for the Node idiom.

**Detection:** any of the following in a test body: `new Date()`, `Date.now()`, `performance.now()`, `process.hrtime()`, `process.hrtime.bigint()` — with **no** preceding `jest.useFakeTimers()` / `vi.useFakeTimers()` / `sinon.useFakeTimers(...)` / `t.mock.timers.enable(...)` in the same test or its `beforeEach`. The presence of the fake-timers install anywhere upstream in the current test's scope is sufficient to suppress the flag.

**Smell:** the test reads the real clock. Tests that use the real clock pass when the author runs them and fail at midnight, on daylight-saving transitions, on slow CI runners, or at time-zone boundaries. Core `HC-11` covers the general case; this refines detection to the Node idiom.

**Carve-out:** if the test calls `Date.now()` / `new Date().toISOString()` solely to generate a unique identifier (e.g. `const id = \`test-${Date.now()}\``) and the value is not used in an assertion, do not flag. The canonical unique-id generation pattern is benign.

**Rewrite (intent):** install fake timers and pin the clock. Under the unit and integration rubrics that is the Jest / Vitest / Sinon idiom — see `nodejs.POS-5` in [`unit-integration.md`](unit-integration.md). Under the E2E rubric the browser owns the clock, so pin it with Playwright's `page.clock.install({ time })` / `page.clock.setFixedTime(...)` before navigation rather than a runner-level fake-timer install.

---



### `nodejs.HC-7` — `.resolves.*` / `.rejects.*` without `await`

**Applies to:** `unit, integration, e2e`

**Detection:** `expect\((?P<promise>[^)]+)\)\.(resolves|rejects)\.` without a preceding `await` or `return` on the `expect(...)` call.

**Smell:** Jest's and Vitest's `.resolves` / `.rejects` matchers return a thenable that must be awaited (or returned from the test function) for the assertion to actually run. An un-awaited `.resolves.toBe(...)` / `.rejects.toThrow(...)` silently skips — the test passes regardless of the promise's outcome. Jest's own docs call this out: see https://jestjs.io/docs/asynchronous (§ ".resolves / .rejects") — "Be sure to return the assertion — if you omit this `return` statement, your test will complete before the promise returned from `fetchData` is resolved ... potentially leading to false positives or unexpected test behavior."

**Example (smell):**
```ts
test('resolves to user', () => {
    expect(getUser(1)).resolves.toEqual({ id: 1, name: 'Ada' }); // missing await
});
```

**Rewrite (intent):** make the test `async` and `await expect(...)`.

---

### `nodejs.HC-8` — Detached promise, timer, worker, or subtest with no observable completion or failure outcome

**Applies to:** `unit, integration, e2e`.

**Detection:** a test starts asynchronous work (`void promise`, an unawaited `.then(...)`, `setTimeout` / `setInterval`, `new Worker(...)`, or `t.test(...)`) but does not await, return, join, clear, terminate, or otherwise observe its completion, failure, cancellation, or resulting public state. The API name alone is not evidence: inspect the test's asserted outcome and its teardown.

**Smell:** detached work can settle after the test runner reports success, hide a rejection, keep the event loop alive, or leak into a later test. A call-count assertion is insufficient when the contract concerns the work's outcome.

**Rewrite (intent):** retain the promise or worker handle, await its result or rejection, use runner-aware subtest completion, and clear or terminate scheduled/background work in teardown. Assert the contract-visible result, failure, cancellation, or cleanup state rather than merely that an API was called.

---

## Framework-specific low-confidence smells (`nodejs.LC-*`)

These apply under all three rubrics. See [`unit-integration.md`](unit-integration.md) and [`unit.md`](unit.md) for the narrower lanes.


### `nodejs.LC-2` — `@ts-expect-error` / `@ts-ignore` in test body

**Applies to:** `unit, integration, e2e`

**Detection:** `// @ts-expect-error` or `// @ts-ignore` anywhere inside a test function body.

**Why low-confidence:** sometimes legitimate (the test deliberately exercises a compile-time-invalid call to verify a runtime guard). More often hides a drift between the test's intent and the SUT's evolved signature; the test passes because TypeScript stops checking at the comment.

**Rewrite (intent):** if the test exercises a runtime guard against bad input, use `as never` / `as unknown` with a linked comment citing the guard; otherwise, fix the shape and remove the directive.

---

### `nodejs.LC-3` — `.only` / `fdescribe` / `fit` committed

**Applies to:** `unit, integration, e2e`

**Detection:** `(it|test|describe)\.only\(` / `^\s*fdescribe\(` / `^\s*fit\(` / `^\s*ftest\(` in a test file.

**Why low-confidence:** the author left a focused-run marker in. The suite still passes locally but runs only the focused test, suppressing everything else. On CI, some configurations fail closed (good); others silently run only the focused test (bad).

**Rewrite (intent):** remove the `.only` / `f*` prefix before committing. Configure the test runner to fail on `.only` when present. Vitest defaults `allowOnly` to `false` under CI (auto-detected via `std-env`) and `true` locally — set `allowOnly: false` in `vitest.config` to fail everywhere, or use the `--allowOnly` CLI flag. Jest does not ship a first-party `.only`-forbidden flag; an ESLint rule (`jest/no-focused-tests` from `eslint-plugin-jest`) is the idiomatic enforcement. Under the E2E rubric, `test.only` is the Playwright analog — set `forbidOnly` in `playwright.config` (the standard pattern is `forbidOnly: !!process.env.CI`) so a committed focus marker fails the run.

---

### `nodejs.LC-4` — `.skip` / `xit` / `.todo` with no linked issue

**Applies to:** `unit, integration, e2e` — refines core `LC-9`.

**Detection:** `(it|test|describe)\.(skip|todo)\(` or `^\s*xit\(` / `^\s*xtest\(` — plus `test.fixme(` under the E2E rubric, Playwright's idiom for a known-broken spec — where the test or an immediately-preceding comment contains no URL, issue reference (`#\d+`, `ISSUE-\d+`), ticket identifier, or flake history pointer.

**Why low-confidence:** a skip without a documented reason becomes the permanent home for the flake. Refines `LC-9` for the Jest / Vitest / Mocha idiom.

**Rewrite (intent):** add a comment linking to the issue that will re-enable the test, or remove the test entirely if its intent is unclear.

---

### `nodejs.LC-5` — Custom matcher used with no reachable `expect.extend` declaration

**Applies to:** `unit, integration, e2e`

**Detection:** a `.toBeXyz(...)` / `.matchXyz(...)` call whose matcher name is not one of the built-in Jest / Vitest / Chai matchers, with **no** `expect.extend({ toBeXyz: ... })` reachable from the test file's import graph (imports of `jest.setup.{js,ts}` / `vitest.setup.{js,ts}` / `globalSetup` resolve the declaration if present).

**Why low-confidence:** the matcher is either broken (the declaration was lost) or registered through a mechanism the audit can't see (a global-setup import resolved at runtime). Flag for manual review; the author can dismiss if the registration is truly centralized.

**Rewrite (intent):** import the declaration directly from the setup file, or add a top-of-file comment pointing at it. Make the registration discoverable from the test file.

---



## Framework-specific positive signals (`nodejs.POS-*`)


### `nodejs.POS-2` — `expect.extend(...)` with domain-invariant custom matchers

**Applies to:** `unit, integration, e2e`

**Detection:** `expect.extend({ <matcherName>: ... })` registered in a setup file, where `<matcherName>` names a domain invariant (`toBeAValidIsbn`, `toBeMonotonicallyIncreasing`, `toContainAllRequiredFields`) rather than a structural shape.

**Why positive:** a domain-named custom matcher expresses intent directly. Tests read as specifications (`expect(result).toBeAValidIsbn()`) instead of structural probes.

---





### `nodejs.POS-8` — Detached-work completion, failure, or cleanup is observed through the test contract

**Applies to:** `unit, integration, e2e`.

**Detection:** a test keeps a promise, timer, worker, or `node:test` subtest handle and awaits/returns/joins it, clears or terminates it when applicable, then asserts an observable result, propagated failure, cancellation, or released resource. Do not award this signal for awaiting an API name without an observable outcome.

**Why positive:** the test owns asynchronous work for its full lifetime, so completion and failure cannot silently escape its result. It proves the behavior callers depend on rather than incidental scheduling.

**Rewrite (intent):** keep this shape when background work is part of the contract; retain the explicit observable outcome if implementation details change.

---

## Carve-outs

Patterns that look like core smells but are idiomatic in Node.js / TypeScript and must not be flagged:

- **Do not flag `HC-5`** (mock-return-then-mock-called-with) when the mock target is a process boundary — `fetch`, `node:http`, `node:https`, `undici`, `node-fetch`, `axios`, `got`, `@octokit/*`, AWS / Azure / GCP SDKs, `nodemailer`, DB drivers (`pg`, `mysql2`, `mongodb`, `redis`, `ioredis`), `fs` / `node:fs`. These are legitimate mocks at the process boundary; the same rule applies to `nodejs.HC-1` (see its own carve-out above).

- **Do not flag `HC-11`** (hardcoded clock values) when fake timers are installed in the same test body or a preceding `beforeEach` — `jest.useFakeTimers()` / `vi.useFakeTimers()` / `sinon.useFakeTimers(...)` / `t.mock.timers.enable(...)`. That is the idiomatic way to control time in Node.js.

- **Do not flag `LC-1`** (mocking same-layer code) when the mocked type is an interface owned by the tested module *and* the project has a documented "test via seams" / "interface-segregation" convention (e.g. a `CLAUDE.md`, `README.md`, or ADR stating that interfaces exist specifically for testability). Ask before flagging if ambiguous.

- **Do not flag `LC-7`** (excessive setup) when the setup is constructing a `Testcontainers` stack (`new GenericContainer(...).withEnvironment(...).start()`), `supertest(app)` with a non-trivial app, `new NestApplication(...)` / `Test.createTestingModule(...).compile()` (safety net for NestJS projects until a dedicated extension exists), a `@playwright/test` `webServer` config, or a `vitest.config` `globalSetup` bringing up a real backend for an E2E run. Under the new dispatch model (see [SKILL.md § 0b (Rubric selection)](../../../SKILL.md)), these are **routing signals into the integration or E2E rubric** — tests using them should be audited under that rubric where heavy setup is expected, not the unit rubric at all. This carve-out stays in force as a **safety net** for cases where the dispatch is uncertain.

- **Do not flag `HC-10`** (snapshot tests pinning unspecified output) when the snapshot target is:
  - A JSON response whose schema is published via an OpenAPI document (any `openapi.{yaml,json}`) in the repo, OR
  - A `@testing-library/jest-dom` accessible-tree snapshot (output of `prettyDOM(container)` or similar), OR
  - A Zod / Yup / Joi schema parse result where the schema is co-located with the SUT and exported from the same module — the schema **is** the contract.

- **Do not flag `nodejs.HC-1`** (module-level mock of same-layer code) when the mocked module's path resolves to `node_modules/` (external package — by definition a process / library boundary).

---
