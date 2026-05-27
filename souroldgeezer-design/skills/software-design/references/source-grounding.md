# Source Grounding

Behavioral evals are original synthetic cases derived from this repo's
software-design workflow, reference, smell catalog, extensions, and calibration
notes. They do not copy external prompts, code, examples, diagrams, tables, or
documentation.

- Core: `../../../docs/software-reference/software-design.md`,
  `references/smell-catalog.md`, `references/pattern-catalog.md`, and
  `references/evals/model-pressure.md`; all repo-authored.
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

External links ground platform mechanics only. All smell codes and design
heuristics are repo-authored and must not reproduce source prose.
