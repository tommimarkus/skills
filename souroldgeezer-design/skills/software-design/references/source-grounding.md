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
