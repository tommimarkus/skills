# Extensions

Load this index when stack-specific test quality rules may apply. Full rule
packs live under `../../../references/test-quality-audit-extensions/`.

Core signals:

- .NET: `.csproj`, `.sln`, xUnit, NUnit, MSTest, Moq, bUnit, Playwright,
  Selenium, or Stryker.NET -> `dotnet-core.md`
- Node.js / TypeScript: `package.json`, Jest, Vitest, Mocha, `node:test`,
  Testing Library, Playwright, Cypress, WebdriverIO, Supertest, MSW,
  Testcontainers, fast-check, or Stryker JS -> `nodejs-core.md`
- Next.js: `next`, `next.config.*`, App Router, Pages Router, Route Handlers,
  `proxy.*`, legacy `middleware.*`, or `@next/*` -> `nodejs-core.md`, then
  `nextjs-core.md`
- Python: `pyproject.toml`, pytest/unittest, Hypothesis, pytest-asyncio,
  Playwright Python, Selenium, Django, Flask, FastAPI, Starlette, SQLAlchemy, or
  Alembic -> `python-core.md`
- Robot Framework: `.robot`, `.resource`, `.tsv`, Robot packages, `robot`,
  `rebot`, `pabot`, or Robot XML / xUnit artifacts -> `robotframework-core.md`

After rubric selection, load the matching addon pack:

- Unit/component: `dotnet-unit.md`, `nodejs-unit.md`, `nextjs-unit.md`,
  `python-unit.md`, `robotframework-unit.md`
- Integration: `dotnet-integration.md`, `nodejs-integration.md`,
  `nextjs-integration.md`, `python-integration.md`,
  `robotframework-integration.md`
- E2E: `dotnet-e2e.md`, `nodejs-e2e.md`, `nextjs-e2e.md`, `python-e2e.md`,
  `robotframework-e2e.md`

When several layers apply, compose them: test-artifact packs own runner/test
semantics, SUT-stack packs own source-level gaps and mutation tools, and
platform-superset packs may carve out base-stack findings only for exact
platform boundaries. If two packs identify the same issue, report one owner and
cite the other as evidence.
