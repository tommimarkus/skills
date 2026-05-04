# Extension: Node.js / TypeScript — integration-rubric addon

Addon to [nodejs-core.md](nodejs-core.md) loaded **only when step 0b selects the integration rubric**. Carries framework-specific smells and procedures that apply exclusively under the integration rubric:

- Integration-only high-confidence smells (`nodejs.I-HC-*`) that refine core `I-HC-A*` / `I-HC-B*` codes.
- The **auth matrix enumeration** procedure (step 2.6 of the deep-mode workflow) — integration-only because auth enforcement is an HTTP-seam concern.
- The **migration upgrade-path enumeration** procedure (step 2.7) — integration-only because migrations run against a real data store. Covers Prisma, Drizzle, TypeORM, and Knex.

**Prerequisite:** `nodejs-core.md` must already be loaded. This file uses the test-type detection signals, test double classification, carve-outs, SUT surface enumeration, determinism verification, and Stryker JS mutation tool declared there.

The rubric-neutral smells in `nodejs-core.md` (`nodejs.HC-1` through `nodejs.HC-7`, `nodejs.LC-1` through `LC-7`, `nodejs.POS-*`) all apply under the integration rubric too — they declare `Applies to: unit, integration`. Do not re-list them here.

---

## Framework-specific high-confidence integration smells (`nodejs.I-HC-*`)

### `nodejs.I-HC-A1` — `supertest(app)` against a shared app instance with no per-test data scoping

**Applies to:** `integration` — refines core `I-HC-A2` / `I-HC-A4`.

**Detection:** a test file declares `const app = <express|fastify|hono|nestApp>()` at module scope (or imports a long-lived app factory) and multiple test methods call `request(app).get(...)` / `.post(...)` without per-test data scoping — no per-test unique keys, no per-test tenant / partition / schema reset, no `beforeEach` truncation.

**Smell:** the shared app instance amortizes construction (which is legitimate — see `nodejs.I-POS-3`) but the data seen by each test is whatever the previous test wrote. Tests pass in isolation and fail in the suite, or vice versa. Running tests in parallel (Vitest, Jest 29+ workers) exposes this as order-dependent flake.

**Example (smell):**
```ts
const app = buildApp();

test('POST /orders creates a row', async () => {
  await request(app).post('/orders').send({ sku: 'A' }).expect(201);
});

test('GET /orders returns the rows', async () => {
  const res = await request(app).get('/orders').expect(200);
  expect(res.body).toHaveLength(1); // depends on POST having run first
});
```

**Rewrite (intent):** scope data per test. Either generate a unique key per test (`const tenantId = crypto.randomUUID()`; include it in the request payload and assertion), open a per-test DB transaction (`beforeEach(() => prisma.$executeRaw\`BEGIN\`)`; `afterEach(() => prisma.$executeRaw\`ROLLBACK\`)`), or truncate per test (`beforeEach(() => db.executeMany(['TRUNCATE orders'])))`.

---

### `nodejs.I-HC-A2` — ORM client constructed at module scope, reused across tests with no reset

**Applies to:** `integration` — refines core `I-HC-A4`.

**Detection:** any of:

- `const prisma = new PrismaClient()` at module scope with no `afterEach` / `afterAll` cleanup visible.
- `const db = drizzle(...)` at module scope with no per-test reset.
- `new DataSource({ ... })` (TypeORM) at module scope used across multiple test methods.
- `const knex = knexInstance(...)` at module scope with no `knex.schema.dropTable` / truncate between tests.

**Smell:** the ORM client is fine to share (connection pooling is the point), but the *data* it sees must be scoped per test. Reuse of the client without a `$transaction` rollback / truncate / per-test schema means the first test's rows are the second test's seed data.

**Example (smell):**
```ts
const prisma = new PrismaClient();

test('creates a user', async () => {
  const u = await prisma.user.create({ data: { email: 'a@x' } });
  expect(u.id).toBeDefined();
});

test('lists users', async () => {
  const users = await prisma.user.findMany();
  expect(users).toHaveLength(1); // passes — depends on prior test
});
```

**Rewrite (intent):** truncate per test in `beforeEach` (`await prisma.$executeRaw\`TRUNCATE "User" CASCADE\``), OR use a per-test schema / tenant / partition key, OR wrap each test in an interactive transaction that is deliberately rolled back by throwing from inside the callback (`await prisma.$transaction(async (tx) => { ...; throw new Rollback(); })` with a try/catch that silences the sentinel error — Prisma's `$transaction` commits on success and rolls back on any thrown error).

---

### `nodejs.I-HC-A3` — Testcontainers started in `beforeAll` with no `afterAll` teardown

**Applies to:** `integration` — refines core `I-HC-A9`.

**Detection:** `beforeAll\s*\([^)]*\)` containing `new GenericContainer(...).start()` or a `@testcontainers/*` scoped-package `.start()` call, with **no** `afterAll\s*\([^)]*\)` calling `container.stop()` / `.close()` in the same file.

**Smell:** the container keeps running after the test file finishes. On a single run the container leaks; under watch mode or a large suite, multiple parallel container starts exhaust Docker resources. The test suite is relying on external cleanup (CI teardown, Docker prune) that local runs don't have.

**Rewrite (intent):**
```ts
let container: StartedTestContainer;

beforeAll(async () => {
  container = await new GenericContainer('postgres:16').start();
});

afterAll(async () => {
  await container.stop();
});
```

---

### `nodejs.I-HC-B1` — `supertest` / `fetch` against an auth-protected endpoint with no `Authorization` header and no 401 negative test

**Applies to:** `integration` — refines core `I-HC-B7`.

**Detection:** the test calls `request(app).<method>('<route>')` (or `fetch('<url>')`) against a route whose handler requires authentication (Passport, JWT middleware, Auth.js v5 `auth()`, legacy NextAuth `getServerSession`, Express `requireAuth`-named middleware) **without** (a) sending an `Authorization` header, (b) setting a cookie known to represent a valid session, or (c) asserting `401`/`403` for a negative case.

**Smell:** the test exercises only the happy path through real middleware but never validates auth behavior. The test "passes" for any implementation that lets anonymous requests through, including a broken one. When the endpoint's auth middleware is disabled in the test-only config (a common anti-pattern), the test is a straight-up lie.

**Example (smell):**
```ts
test('GET /admin/users returns ok', async () => {
  const res = await request(app).get('/admin/users');
  expect(res.status).toBe(200); // happens to pass because dev-mode auth is permissive
});
```

**Rewrite (intent):** cover the full matrix per [integration-testing.md § 5.2 I-HC-B7](../../../docs/quality-reference/integration-testing.md) — anonymous (expect `401`), valid token/session (expect documented success), expired or not-yet-valid token (expect `401`), tampered/wrong-issuer/wrong-audience token where JWT/OIDC is used (expect `401`), insufficient scope/role (expect `403`), cross-user/tenant access where resources have owners (expect `403` or `404`), and cookie/session/CSRF lifecycle cells where the app owns them. For Auth.js v5, use the project session helper rather than bypassing the middleware.

---

### `nodejs.I-HC-B2` — MSW (Node) with `passthrough()` / `bypass()` to a real upstream

**Applies to:** `integration` — refines core `I-HC-B4`.

**Detection:** `import { setupServer } from 'msw/node'` plus handler definitions that forward to the real remote service rather than returning a stub — either `http.<method>('<upstream-url>', () => passthrough())` (from `import { passthrough } from 'msw'`) or a handler that calls `await fetch(bypass(request))` (from `import { bypass } from 'msw'`) and returns the result.

**Smell:** the integration test depends on a live external service over the network. CI runs become non-deterministic (the upstream rate-limits, returns a 500, or changes its response shape). The test is an integration sub-lane B masquerading as a unit / sub-lane A test — either call it what it is (contract test against staging) or stub the upstream explicitly.

**Rewrite (intent):** replace `passthrough()` with an explicit stub handler whose response shape comes from the upstream's OpenAPI spec / Pact / recorded fixture. If you genuinely need to exercise the real upstream, move the test to a separate contract suite that runs on a schedule, not on every PR.

---

## Framework-specific integration low-confidence smells (`nodejs.I-LC-*`)

### `nodejs.I-LC-1` — Hardcoded localhost URL / port in a test against `supertest` or `fetch`

**Applies to:** `integration` — refines core `I-HC-B4`.

**Detection:** `request\(['"]http[s]?://(localhost|127\.0\.0\.1):(?P<port>\d+)` or `fetch\(['"]http[s]?://(localhost|127\.0\.0\.1):(?P<port>\d+)` with a literal port number (e.g. `3000`, `5432`, `27017`) anywhere in the test body.

**Why low-confidence:** ports sometimes need to be hardcoded (dev-proxy conventions, in-repo containers bound to a known host port). More often the hardcode breaks parallel test runs (two test files fight for port `3000`) and prevents Testcontainers' dynamic port assignment from doing its job. The right shape is to read `container.getMappedPort(5432)` / `process.env.TEST_API_URL` / `app.address()`.

**Rewrite (intent):** call `request(app)` with the in-process app instance (no port at all — supertest runs it on an ephemeral port automatically) or use the Testcontainers mapped port.

---

## Framework-specific integration positive signals (`nodejs.I-POS-*`)

### `nodejs.I-POS-1` — Per-test fresh DB schema via Testcontainers or `pg-mem`

**Applies to:** `integration`

**Detection:** any of:

- `beforeEach\(async \(\) => \{[^}]*new PostgreSqlContainer\(` (per-test container — expensive but hermetic).
- `const mem = newDb\(\)` (pg-mem — in-memory Postgres) followed by per-test schema construction.
- A fresh-schema factory: `await db.schema.createSchema(\`test_\${testId}\`)` per test with the test's queries scoped to that schema.

**Why positive:** hermetic by construction — the test owns its data, has no shared state with other tests, and produces the same result twice in a row. Matches `I-POS-5` (hermetic) and `I-POS-4` (per-test data ownership).

---

### `nodejs.I-POS-2` — `server.use(...)` per-test handler override with MSW

**Applies to:** `integration`

**Detection:** `setupServer(...baseHandlers)` once at module scope, then `server.use(http.<method>('<url>', () => HttpResponse.json({...})))` inside specific test bodies to override a single handler for that test — followed by `server.resetHandlers()` in `afterEach` (which removes runtime handlers and restores the base set, per https://mswjs.io/docs/api/setup-server/reset-handlers).

**Why positive:** the default handlers represent the SUT's production HTTP boundary; per-test overrides let each test specify "for this case, the upstream returns X". Tests stay precise — the seam is the HTTP boundary, and each test declares exactly which edge of that seam it's exercising.

---

### `nodejs.I-POS-3` — `request(app)` against a per-file app factory

**Applies to:** `integration`

**Detection:** a test file that constructs `const app = await buildApp({ ...testOverrides })` in `beforeAll` (once per file) where the factory wires up real middleware, real routes, and real adjacent dependencies — but each test uses unique keys / per-test transactions for data.

**Why positive:** amortizes app-construction cost across the file's tests while keeping data ownership per-test. Matches `dotnet.POS-3` (shared immutable setup) with Node-idiomatic construction.

---

## Auth matrix enumeration

Consumed by [SKILL.md § Auth matrix enumeration](../SKILL.md#auth-matrix-enumeration) — step 2.6 of the deep-mode workflow. Integration-only: auth enforcement matrices target HTTP seams, which live under the integration rubric.

### Protected-endpoint patterns

Enumerate endpoints that require authentication:

- **Express / Koa / Hono — middleware application on a route.** Search for `app\.(get|post|put|delete|patch)\s*\(['"]<route>['"](?P<middlewares>[^)]*)\)` and examine the middleware arguments. Routes whose middleware list includes `passport.authenticate('<strategy>')`, `requireAuth`, `requireUser`, `ensureAuthenticated`, `verifyJwt`, or a name matching `/auth|jwt|session|login/i` are protected endpoints. Capture the route template and any policy argument.
- **Fastify — `preHandler` or `onRequest` hooks.** `fastify.route({ method: ..., url: ..., preHandler: <hookFn>, ... })` where `<hookFn>` references a known auth hook (`verifyJwt`, `authenticate`, `requireAuth`). Also global-hook registrations: `fastify.addHook('onRequest', authHook)` applied with a URL filter.
- **NestJS controllers — `@UseGuards(...)` decorator.** `@UseGuards\(\s*(?P<guard>\w+Guard)\s*\)` on a `@Controller(...)` class or `@Get(...)` / `@Post(...)` method. Capture the guard type. Also `@Public()` decorator explicitly marks anonymous routes; exclude those from the protected list.
- **Next.js Route Handlers — `auth()` call inside the handler.** `export async function (GET|POST|PUT|DELETE|PATCH)\(.*\)\s*\{[^}]*(await\s+)?auth\(` pattern (Auth.js v5). Also the legacy NextAuth v4 pattern: `getServerSession\(\s*(req|authOptions)`. Both indicate the handler checks session before responding.
- **Proxy / middleware `matcher` config.** `export const config = \{[^}]*matcher\s*:\s*(?P<matcher>[^}]+)\}` inside `proxy.{ts,js}` / `middleware.{ts,js}` at repo root — enumerate the matched path patterns as the protected-path envelope. (The `nextjs` extension's core file refines this to distinguish App Router / Pages Router path shapes.)

Record scope / policy / role requirements by capturing the policy argument (`@UseGuards(AdminGuard)` → `admin-only`; `requireAuth({ roles: ['admin'] })` → `admin-only`).

### Auth scenario detection in tests

For each enumerated endpoint, search the test project for each matrix column:

- **`anonymous`** — a test that calls `request(app).<method>('<route>')` (no `Authorization` header, no session cookie) and asserts `.expect(401)` / `.expect(403)`. Match `expect\(res\.status\)\.toBe\((401|403)\)` or `\.expect\((401|403)\)`.
- **`token-expired`** — a test that arranges a JWT with `exp` in the past. Match `jwt\.sign\(.*\{[^}]*exp\s*:\s*Math\.floor\(Date\.now\(\)\s*/\s*1000\)\s*-\s*\d+` or a test-helper named `expiredToken()` / `tokenWithExp(-<delta>)`.
- **`not-before`** — a test that arranges `nbf` in the future and asserts `401`.
- **`token-tampered`** — a test that arranges a token whose signing secret differs from the SUT's, or whose `alg` header is `none`. Match `jwt\.sign\(.*'<wrongSecret>'` or `alg\s*:\s*['"]none['"]`.
- **`wrong-issuer` / `wrong-audience` / `wrong-token-type`** — tests that present validly signed tokens with rejected `iss`, `aud`, or `typ` / scheme values, asserting `401`.
- **`insufficient-scope`** — a test that presents a session whose `role`/`scope`/`permissions` lack the endpoint's required value, asserting `.expect(403)`.
- **`sufficient-scope`** — a test that presents a session with the required role / scope, asserting the documented success code.
- **`cross-user`** — a test that presents user A's session against a resource created by user B (e.g. resource path `/api/users/<B_id>/orders`) and asserts `403` or `404`.
- **`logout-invalidated` / `idle-timeout` / `session-rotation` / `session-fixation` / `csrf-invalid`** — applicable when Express/Fastify/Nest/Next uses cookie-backed sessions, `express-session`, Auth.js cookies, CSRF middleware, or browser form posts. Cover by asserting logout invalidates the cookie, timeout is rejected, privilege changes rotate the session where required, a pre-login session id is not retained after login, and missing/invalid CSRF tokens are rejected.

### Carve-outs

- **Bare `@UseGuards(JwtAuthGuard)` / `requireAuth()` with no scope / role** — the endpoint has no scope / role requirement. The `insufficient-scope` cell is `n/a` for that endpoint; do not flag it as a gap.
- **Single-user product** — if the repo has no multi-tenant model (no per-user / per-org resource ownership), the `cross-user` cell is `n/a`. Detect by grepping for `userId` / `tenantId` / `orgId` / `ownerId` in the endpoint's path params or request body schema; if none, mark `n/a`.
- **Bearer-only APIs** — cookie/session and CSRF cells are `n/a` unless the app has cookie auth, server-side session state, browser form posts, or CSRF middleware.
- **`nodejs.I-HC-B1` already fires** — a test flagged under `nodejs.I-HC-B1` (happy-path-only against a protected endpoint) is the same gap as the auth matrix rows. Emit one finding per endpoint, not one per test; reference both codes.

---

## Migration upgrade-path enumeration

Consumed by [SKILL.md § Migration upgrade-path enumeration](../SKILL.md#migration-upgrade-path-enumeration) — step 2.7 of the deep-mode workflow. Integration-only: migrations run against a real data store.

### Migration enumeration patterns (per ORM)

Detect the project's ORM first (presence of the ORM package in `package.json` + its config file), then enumerate migrations using the ORM-specific pattern. Multiple ORMs in one repo are rare but possible (monorepo with a legacy + new service); enumerate each independently.

#### Prisma

- **File glob:** `**/prisma/migrations/*/migration.sql`.
- **Identifier:** the parent-directory name (e.g. `20260101120000_add_users_table`). The `migration.sql` file is the raw DDL.
- **Metadata:** `prisma/migrations/migration_lock.toml` declares the provider; use this to confirm the ORM target.

#### Drizzle

- **File glob:** default `out:` directory is `./drizzle`; regular migrations land as `./drizzle/<NNNN>_<name>.sql` (sequence-prefixed, e.g. `0000_initial_schema.sql`). `drizzle-kit generate --custom` writes SQL into a timestamped subdirectory (`./drizzle/<timestamp>_<name>/migration.sql`) — enumerate both shapes. Read `drizzle.config.{ts,js,mjs}` (the `out:` field passed to `defineConfig`) to detect a non-default output path (e.g. `out: './migrations'`) and glob accordingly.
- **Identifier:** for flat-file migrations, the filename stem (e.g. `0001_initial_schema`); for custom migrations, the parent-directory name.
- **Metadata:** `<out>/meta/_journal.json` lists the migrations in order with their `idx` / `when` / `tag` / `breakpoints`. Useful for determining upgrade ordering.

#### TypeORM

- **File glob:** default `**/migrations/*.{ts,js}`; the `DataSource` option `migrations: [...]` is authoritative — read it to detect a custom glob. Files are named `<timestamp>-<Name>.ts` (e.g. `1640000000000-InitialMigration.ts`).
- **Detection within file:** `class\s+(?P<name>[A-Z]\w+)(?:\d{13})?\s+implements\s+MigrationInterface` — the class name (minus the optional 13-digit timestamp suffix TypeORM appends) is the identifier.
- **Content:** each class exports `async up(queryRunner: QueryRunner): Promise<void>` and `async down(queryRunner: QueryRunner): Promise<void>`. `QueryRunner` is the documented interface for DDL/DML inside a migration (`createTable`, `addColumn`, `createIndex`, `query`, etc.).
- **DataSource config flags that affect enumeration:** `synchronize: false`, `migrations: [...]`, `migrationsRun: boolean` (auto-run migrations on `initialize()`), `migrationsTableName` (default `migrations`), `migrationsTransactionMode: 'all' | 'each' | 'none'`.

#### Knex

- **File glob:** `**/migrations/*.{ts,js}` (the default; override in `knexfile.{js,ts}` via `migrations.directory` — an array is also valid when combined with `sortDirsSeparately: true`). Read `knexfile` to detect custom directories.
- **Identifier:** filename stem (Knex prefixes with a UTC timestamp, e.g. `20260101120000_add_users_table.ts`).
- **Content:** each file exports `export async function up(knex: Knex): Promise<void>` and `export async function down(knex: Knex): Promise<void>` (or CJS `exports.up = ...`).
- **Applying migrations:** programmatic entry points are `knex.migrate.latest([config])` (run all pending migrations), `knex.migrate.up([config])` (run one), `knex.migrate.down([config])` (undo last or named), `knex.migrate.rollback([config], [all])`.

### Upgrade-path test detection

For each enumerated migration, search the test project for a test method that satisfies **all three** conditions:

1. **References the migration identifier.** Depending on the ORM:
   - Prisma: the test imports / shells out to `prisma migrate deploy` for a specific migration name, OR reads the `migration.sql` file, OR asserts on the schema state produced by that migration.
   - Drizzle: the test imports the migration file or invokes `migrate(db, { migrationsFolder: '...' })` (e.g. from `drizzle-orm/node-postgres/migrator` or the driver-matching migrator path) pointing at a directory containing the migration.
   - TypeORM: the test invokes `dataSource.runMigrations()` / `dataSource.undoLastMigration()` against a `DataSource` whose `migrations: [...]` glob resolves to the target migration, OR imports the migration class and calls `new <MigrationClassName>().up(queryRunner)` directly.
   - Knex: `import * as migration from '../../migrations/<filename>'` then `migration.up(knex)` / `migration.down(knex)`, OR `knex.migrate.latest({ directory })` pointing at the migration file's directory.
2. **Arranges non-empty seed data before the migration runs.** Search the test's Arrange block for `prisma.<table>.create(...)` / `db.insert(<table>).values(...)` (Drizzle) / `queryRunner.query('INSERT ...')` (TypeORM) / `knex('<table>').insert(...)` calls on tables the migration will transform, **before** the migration is invoked.
3. **Asserts post-migration state.** After the migration invocation, the test reads rows back and asserts a property of the returned data — either a schema-level assertion (column exists, type is correct) or a data-level assertion (seed row's value was transformed correctly).

If all three conditions fail, emit `Gap-MigUpgrade`. If condition 1 holds but 2 or 3 fail, emit `Gap-MigUpgrade` with a sharper note (e.g. "test exists but arranges no seed data — see `I-HC-A7`").

### ORM-specific carve-outs

- **Prisma `prisma migrate reset` / `--create-only` migrations.** Some migrations are intentionally data-only (seeds, backfills). A migration whose `migration.sql` contains only `INSERT INTO ...` / `UPDATE ...` with no `ALTER TABLE` / `CREATE TABLE` is a backfill; its upgrade-path test is the data assertion rather than a schema assertion. Recognize this shape and adjust the expected test pattern.
- **Drizzle-kit generated no-op migrations.** When a schema file changes in ways that don't produce SQL (e.g. renaming a constraint name), drizzle-kit can produce an empty migration. Suppress `Gap-MigUpgrade` for migrations whose `.sql` body contains only comments or `-- <empty>`.
- **TypeORM `queryRunner.query('<vendor-specific>')` migrations.** Vendor-specific SQL (e.g. Postgres `CREATE EXTENSION`) may be impossible to test against SQLite / H2; flag as `Gap-MigUpgrade` only if the project uses the same vendor across dev, test, and prod. If the test DB differs from prod, record the mismatch as a limitation rather than a gap.
- **Knex `--migrations-schema-name`.** Some repos put migrations in a dedicated schema (`public.migrations_lock`); enumerate those via the `knexfile`'s `migrations.schemaName` field.

### Repo-level carve-outs

- **Migration runner test.** If the repo has a single integration test that runs `prisma migrate deploy` / `migrate(db, { migrationsFolder })` (Drizzle) / `dataSource.runMigrations()` (TypeORM) / `knex.migrate.latest()` against seed data and asserts post-state for multiple migrations, suppress individual `Gap-MigUpgrade` entries for the migrations that are explicitly named in the runner test's assertion block. Note "covered transitively via migration-runner test".
- **Expand-only migration rule.** If the repo's `CLAUDE.md` or ADR documents an expand-only migration rule (every migration must be safe to deploy while old code is running), the upgrade-path test is doubly important — assertion confidence is `high`. If the rule is absent, confidence stays `high` but the recommendation softens from "required" to "strongly recommended".
