# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local software-design workflow, bundled reference, smell catalog, and
extensions. They do not copy external prompts, code, examples, diagrams, tables,
or documentation.

- Source: `../../../docs/software-reference/software-design.md`.
  Handling: local bundled reference owned by this repo; eval prompts are
  original synthetic scenarios for mode selection, boundary reasoning, evidence
  contracts, and specialist delegation.
- Source: `references/smell-catalog.md` and `extensions/*.md`.
  Handling: local smell and extension contracts; eval cases exercise extension
  selection and output shape without reproducing project code.

- Source: `references/pattern-catalog.md`.
  Handling: local bundled reference owned by this repo; pattern descriptions are
  limited to repo-authored decision criteria and anchored to the existing
  software-design source basis. Synthetic evals exercise pattern selection,
  pattern rejection, and ceremony review without copying third-party pattern
  descriptions, diagrams, tables, or examples.
- Source: `references/evals/model-pressure.md`.
  Handling: local calibration notes and synthetic pressure prompts. Use this
  file before expanding pattern or stack guidance so generic base-model
  knowledge does not get repackaged as bundled skill prose.
- Source: Rust Project docs at `https://doc.rust-lang.org/cargo/reference/workspaces.html`,
  `https://doc.rust-lang.org/cargo/reference/features.html`, and
  `https://doc.rust-lang.org/reference/visibility-and-privacy.html`, and Rust
  API Guidelines at `https://rust-lang.github.io/api-guidelines/`.
  Handling: linked for Rust crate/workspace/API platform facts; extension
  smells are original repo-authored design heuristics and do not copy examples,
  tables, or prose.
- Source: Oracle Java Language Specification chapter 7 at
  `https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html`, Apache Maven
  POM reference at `https://maven.apache.org/pom.html`, and Gradle Java Plugin /
  Java testing docs at `https://docs.gradle.org/current/userguide/java_plugin.html`
  and `https://docs.gradle.org/current/userguide/java_testing.html`.
  Handling: linked for Java package, module, build, source-set, and dependency
  facts; extension smells are original repo-authored design heuristics and do
  not copy examples, tables, or prose.
