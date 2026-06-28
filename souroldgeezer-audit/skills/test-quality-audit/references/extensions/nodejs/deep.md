# Extension: Node.js / TypeScript — deep (Deep mode only)

Loaded only in Deep mode (SUT enumeration, determinism, mutation). For smells,
detection, and carve-outs see [core](core.md).

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../../../SKILL.md) — step 2.5 of the deep-mode workflow. This section declares the Node.js / TypeScript grep patterns the audit agent uses to enumerate testable symbols in a SUT and cross-reference them against a test project. Applies under both the unit and integration rubrics; not run under the E2E rubric.

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

Search the test project (test glob from § Detection signals, excluding `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, `StrykerOutput/` / `.stryker-tmp/`) for at least one of:

- **`Gap-API`** — `covered-strong`: symbol name as identifier + assertion on return value, side effect, error, state, or domain outcome. Word-boundary presence only → `referenced-weak`; import/setup only → `referenced-incidental`.
- **`Gap-Route`** — `covered-strong`: route template as string literal + assertion on the route's published contract (status + body/header/auth/domain outcome, validation error, or problem code). Partial match or status-only → `referenced-weak`.
- **`Gap-Migration`** — migration identifier as path literal or string in a test body, or test imports/executes the migration file.
- **`Gap-Throw`** — error type *and* containing method name both appear in the test body, and the assertion expects that error or public error envelope. Either alone, or happy-path only → probable gap.
- **`Gap-Validate`** — validated field name in a test body that also references the schema binding/class and omits or violates the field. For Zod: `<schema>.safeParse(...)` / `.parse(...)` with invalid payload + failure assertion. Valid-payload-only → `referenced-weak`.

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

Consumed by [SKILL.md § Determinism verification](../../../SKILL.md) — step 4.5 of the deep-mode workflow. Applies under unit and integration rubrics; not run under the E2E rubric (browser-dominated suites are too expensive to rerun cheaply).

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
- **E2E projects:** never run. Browser-driven suites require different tooling (see [SKILL.md § Determinism verification](../../../SKILL.md)).

---

## Mutation testing

Stryker Mutator JS is the Node.js / TypeScript mutation tool. Load
[../../procedures/mutation-nodejs.md](../../procedures/mutation-nodejs.md) only
in Deep mode when mutation evidence is requested or the Deep audit reaches the
mutation section. Quick audits must not load or apply mutation setup guidance.
