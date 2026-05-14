# Extensions

Load this index when stack-specific test quality rules may apply. Full rule
packs live under `../references/extensions/`.

Core signals:

- .NET: `.csproj`, `.sln`, xUnit, NUnit, MSTest, Moq, bUnit, Playwright,
  Selenium, or Stryker.NET -> `../references/extensions/dotnet/core.md`
- Java: `pom.xml`, `build.gradle*`, `settings.gradle*`, `src/test/java`,
  JUnit, TestNG, Mockito, AssertJ, Hamcrest, Testcontainers, REST Assured,
  Playwright Java, Selenium, Maven Surefire/Failsafe, Gradle `Test` tasks, or
  PIT -> `../references/extensions/java/core.md`
- Node.js / TypeScript: `package.json`, Jest, Vitest, Mocha, `node:test`,
  Testing Library, Playwright, Cypress, WebdriverIO, Supertest, MSW,
  Testcontainers, fast-check, or Stryker JS -> `../references/extensions/nodejs/core.md`
- Next.js: `next`, `next.config.*`, App Router, Pages Router, Route Handlers,
  `proxy.*`, legacy `middleware.*`, or `@next/*` -> `../references/extensions/nodejs/core.md`, then
  `../references/extensions/nextjs/core.md`
- Python: `pyproject.toml`, pytest/unittest, Hypothesis, pytest-asyncio,
  Playwright Python, Selenium, Django, Flask, FastAPI, Starlette, SQLAlchemy, or
  Alembic -> `../references/extensions/python/core.md`
- Robot Framework: `.robot`, `.resource`, `.tsv`, Robot packages, `robot`,
  `rebot`, `pabot`, or Robot XML / xUnit artifacts -> `../references/extensions/robotframework/core.md`
- Rust: `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`, `.cargo/config.toml`,
  `src/**/*.rs`, `tests/**/*.rs`, `#[test]`, `#[tokio::test]`,
  `cargo test`, `cargo nextest`, `proptest`, `quickcheck`, `mockall`,
  `testcontainers`, `assert_cmd`, or `cargo-mutants` -> `../references/extensions/rust/core.md`

After rubric selection, load the matching addon pack:

- Unit/component: `../references/extensions/dotnet/unit.md`,
  `../references/extensions/java/unit.md`, `../references/extensions/nodejs/unit.md`,
  `../references/extensions/nextjs/unit.md`, `../references/extensions/python/unit.md`,
  `../references/extensions/robotframework/unit.md`, `../references/extensions/rust/unit.md`
- Integration: `../references/extensions/dotnet/integration.md`,
  `../references/extensions/java/integration.md`, `../references/extensions/nodejs/integration.md`,
  `../references/extensions/nextjs/integration.md`, `../references/extensions/python/integration.md`,
  `../references/extensions/robotframework/integration.md`, `../references/extensions/rust/integration.md`
- E2E: `../references/extensions/dotnet/e2e.md`,
  `../references/extensions/java/e2e.md`, `../references/extensions/nodejs/e2e.md`,
  `../references/extensions/nextjs/e2e.md`, `../references/extensions/python/e2e.md`,
  `../references/extensions/robotframework/e2e.md`, `../references/extensions/rust/e2e.md`

When several layers apply, compose them: test-artifact packs own runner/test
semantics, SUT-stack packs own source-level gaps and mutation tools, and
platform-superset packs may carve out base-stack findings only for exact
platform boundaries. If two packs identify the same issue, report one owner and
cite the other as evidence.
