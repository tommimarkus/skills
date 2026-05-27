# Source Grounding

Behavioral evals are original synthetic cases derived from this repo's
software-design workflow, reference, smell catalog, extensions, and calibration
notes. They do not copy external prompts, code, examples, diagrams, tables, or
documentation.

- Core: `../../../docs/software-reference/software-design.md`,
  `references/smell-catalog.md`, `references/principles-catalog.md`,
  `references/pattern-catalog.md`, and `references/evals/model-pressure.md`;
  all repo-authored.
- Smell taxonomy and calibration sources: Lacerda/Petrillo/Pimenta/Gueheneuc
  "Code smells and refactoring"
  `https://www.sciencedirect.com/science/article/pii/S0164121220300881`,
  Sharma/Spinellis "A survey on software smells"
  `https://www.spinellis.gr/pubs/jrnl/2018-JSS-smells-survey/html/journal.pdf`,
  Suryanarayana/Samarthyam/Sharma "Refactoring for Software Design Smells"
  `https://www.oreilly.com/library/view/refactoring-for-software/9780128013977/`,
  Fowler's refactoring catalog `https://refactoring.com/catalog/`, SEI ATAM
  `https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method-2/`,
  and DORA maintainability/loose-coupling
  `https://dora.dev/capabilities/code-maintainability/` and
  `https://dora.dev/capabilities/loosely-coupled-teams/`. External links ground
  source roles only; smell-card wording, codes, examples, and eval prompts are
  repo-authored.
- .NET facts: .NET project SDK
  `https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview`,
  dependency injection
  `https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/basics`,
  and EF Core modeling `https://learn.microsoft.com/en-us/ef/core/modeling/`.
- Rust facts: Cargo workspaces/features
  `https://doc.rust-lang.org/cargo/reference/workspaces.html`,
  `https://doc.rust-lang.org/cargo/reference/features.html`, Rust visibility
  `https://doc.rust-lang.org/reference/visibility-and-privacy.html`, and API
  Guidelines `https://rust-lang.github.io/api-guidelines/`.
- Java facts: JLS packages/modules
  `https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html`, Maven POM
  `https://maven.apache.org/pom.html`, and Gradle Java/source-set docs
  `https://docs.gradle.org/current/userguide/java_plugin.html`.
- TypeScript facts: project references
  `https://www.typescriptlang.org/docs/handbook/project-references.html`,
  modules `https://www.typescriptlang.org/docs/handbook/modules/reference.html`,
  TSConfig `https://www.typescriptlang.org/tsconfig/`, Node.js package metadata
  `https://nodejs.org/api/packages.html`, and npm `package.json`
  `https://docs.npmjs.com/cli/v11/configuring-npm/package-json/`.
- Shell facts: GNU Bash manual, Z Shell manual, POSIX Shell Command Language,
  Apple Terminal guidance, and Microsoft WSL docs for interpreter and platform
  mechanics.
- Python facts: Python docs, Python Packaging User Guide, PEP 621, PEP 723, and
  uv docs for entrypoint, packaging, and script mechanics.
- Pattern sources: GoF publisher catalog; Fowler enterprise survey
  `https://martinfowler.com/articles/enterprisePatterns.html`, PoEAA
  `https://martinfowler.com/eaaCatalog/`, Strangler Fig
  `https://martinfowler.com/bliki/StranglerFigApplication.html`, EIP
  `https://www.enterpriseintegrationpatterns.com/`, Microsoft Learn pattern/DI
  pages, and AWS Strangler Fig guidance.
- Principle sources: the core reference source basis.

External links ground source roles only. All smell codes, card wording, prompts,
examples, and design heuristics are repo-authored and must not reproduce source
prose, examples, tables, figures, or code.
