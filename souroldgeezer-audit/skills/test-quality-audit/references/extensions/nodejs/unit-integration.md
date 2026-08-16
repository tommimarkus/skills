# Extension: Node.js / TypeScript — unit + integration smells

`Applies to: unit, integration` framework smells — defects needing in-process
access to the SUT (module mocking, test doubles, fake timers, parameterised
input partitions). Loaded on the unit and integration paths only, never on E2E.
Three-rubric smells stay in [`core.md`](core.md).

## Framework-specific high-confidence smells (`nodejs.HC-*`)

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
## Framework-specific low-confidence smells (`nodejs.LC-*`)

### `nodejs.LC-1` — Type coercion of a hand-built mock to the SUT's type (TS-only)

**Applies to:** `unit, integration`

**Detection:** (only when the TS flag is set) `as unknown as (?P<type>[A-Z]\w+)` in a test body, OR `as (?P<type>jest\.Mocked<\w+>|Mocked<\w+>)` applied to a hand-built object literal that was **not** produced by `jest.mocked(mod)` / `vi.mocked(mod)`.

**Why low-confidence:** the test is lying to the type-checker about what it built. If the SUT's collaborator interface evolves — new methods, renamed fields, optional → required — the hand-built mock doesn't get the signal, and the test passes a type-check against the old shape.

**Rewrite (intent):** use `jest.mocked(mod)` or `vi.mocked(mod)` after `jest.mock(...)` so the mock carries the real type; for partial hand-builts, use `Partial<T>` + `as T` only at the injection boundary with a comment explaining why.

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
