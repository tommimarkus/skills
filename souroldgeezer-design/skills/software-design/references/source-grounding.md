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
