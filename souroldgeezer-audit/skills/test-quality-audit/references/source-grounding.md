# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local test-quality workflow, bundled quality references, and existing
golden-corpus maintenance process. They do not copy external prompt text, code,
examples, fixtures, schemas, diagrams, logos, or screenshots.

- Source: `../../../docs/quality-reference/unit-testing.md`,
  `../../../docs/quality-reference/integration-testing.md`,
  `../../../docs/quality-reference/e2e-testing.md`, and
  `references/`.
  Handling: local bundled references owned by this repo; eval prompts are
  original synthetic scenarios for rubric selection, scope, and evidence limits.
- Source: [`golden-corpus/index.md`](golden-corpus/index.md) and
  `golden-corpus/test-quality-audit-cases.jsonl`.
  Handling: local maintenance evidence; behavioral evals are separate synthetic
  cases and do not copy corpus prompts or expected outputs.
- Source: `../../../docs/audit-reference/audit-craft.md`,
  `../../../docs/audit-reference/materiality.md`, and
  `../../../docs/audit-reference/sampling-projection.md`.
  Handling: local bundled references owned by this repo; eval cases exercise
  audit craft, materiality, and sampling projection output contracts and do not
  reproduce rubric prose.
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
- Source: Python `asyncio` task and structured-concurrency documentation at
  `https://docs.python.org/3/library/asyncio-task.html`, asynchronous context
  manager semantics at
  `https://docs.python.org/3/reference/datamodel.html#asynchronous-context-managers-and-async-with`,
  pytest-asyncio guidance at `https://pytest-asyncio.readthedocs.io/`, and the
  ASGI lifespan specification at `https://asgi.readthedocs.io/en/latest/specs/lifespan.html`.
  Handling: linked for task completion/cancellation, async resource ownership,
  and application startup/shutdown facts; Python extension rules are original
  repo-authored quality heuristics and do not copy examples or prose.
- Source: Node.js test-runner documentation at `https://nodejs.org/api/test.html`
  and React Effect documentation at `https://react.dev/reference/react/useEffect`.
  Handling: linked for Node detached-work/subtest lifecycle and React Effect
  cleanup facts; rules require observable outcomes for detached work, Effect
  cleanup, and application lifecycle ownership, and use original repo-authored
  examples rather than copied source material.
- Source: Baldassarre et al., “Studying Test-Driven Development and its
  Retainment Over a Six-month Time Span,” at
  `https://arxiv.org/abs/2105.03312`.
  Handling: linked for the observed combination of more tests and stronger
  fault-detection capability in that study; it grounds the rule that test-count
  growth alone is informational, not a smell.
- Source: Memon et al., “Taming Google-Scale Continuous Testing,” at
  `https://research.google/pubs/taming-google-scale-continuous-testing/`.
  Handling: linked for continuous-testing workload scale, latency, and cost
  pressures; guidance remains project-budgeted rather than importing Google's
  operating thresholds.
- Source: Koochakzadeh and Garousi, “A Tester-Assisted Methodology for Test
  Redundancy Detection,” at `https://doi.org/10.1155/2010/932686`.
  Handling: linked for coverage-based redundancy false-positive risk and the
  use of mutation evidence plus review; no source prose or examples are copied.
- Source: Alégroth, Feldt, and Kolström, “Maintenance of Automated Test Suites
  in Industry: An Empirical study on Visual GUI Testing,” at
  `https://arxiv.org/abs/1602.01226`.
  Handling: linked for the study's finding that frequent maintenance was less
  costly than infrequent large maintenance in its visual GUI-suite setting;
  guidance treats this as qualitative, scoped evidence, not a universal cadence.
