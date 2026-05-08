# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local test-quality workflow, bundled quality references, and existing
golden-corpus maintenance process. They do not copy external prompt text, code,
examples, fixtures, schemas, diagrams, logos, or screenshots.

- Source: `../../../docs/quality-reference/unit-testing.md`,
  `../../../docs/quality-reference/integration-testing.md`,
  `../../../docs/quality-reference/e2e-testing.md`, and
  `../../../references/test-quality-audit-*`.
  Handling: local bundled references owned by this repo; eval prompts are
  original synthetic scenarios for rubric selection, scope, and evidence limits.
- Source: `references/golden-corpus/index.md` and
  `references/golden-corpus/test-quality-audit-cases.jsonl`.
  Handling: local maintenance evidence; behavioral evals are separate synthetic
  cases and do not copy corpus prompts or expected outputs.
- Source: Rust Project docs at `https://doc.rust-lang.org/cargo/guide/tests.html`,
  `https://doc.rust-lang.org/cargo/commands/cargo-test.html`, and
  `https://doc.rust-lang.org/rustc/tests/index.html`; cargo-nextest docs at
  `https://nexte.st/` and `https://nexte.st/docs/running/`; and cargo-mutants
  docs at `https://mutants.rs/`, `https://mutants.rs/mutants-out.html`, and
  `https://mutants.rs/mutants.html`.
  Handling: linked for Rust test-runner and mutation-tool facts; extension
  rules are original repo-authored quality heuristics and do not copy examples
  or prose.
- Source: JUnit User Guide at `https://docs.junit.org/6.0.3/overview.html`,
  Apache Maven Surefire JUnit Platform docs at
  `https://maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html`,
  Gradle Java testing docs at
  `https://docs.gradle.org/current/userguide/java_testing.html`, TestNG docs at
  `https://testng.org/`, Mockito javadoc at
  `https://site.mockito.org/javadoc/current/org/mockito/Mockito.html` and
  `https://www.javadoc.io/static/org.mockito/mockito-core/5.12.0/org/mockito/MockedStatic.html`,
  Testcontainers for Java JUnit 5 docs at
  `https://java.testcontainers.org/test_framework_integration/junit_5/`,
  Playwright Java JUnit docs at `https://playwright.dev/java/docs/junit`, and
  PIT docs at `https://pitest.org/quickstart/maven/`.
  Handling: linked for Java runner, test-double, container lifecycle, browser
  fixture, and mutation-tool facts; extension rules are original repo-authored
  quality heuristics and do not copy examples or prose.
