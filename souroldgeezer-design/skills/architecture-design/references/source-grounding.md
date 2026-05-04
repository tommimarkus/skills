# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local architecture workflow, reference, procedures, and fixture contracts.
They do not copy external diagrams, schemas, screenshots, specification text,
tool output, or example models.

- Source: `../../../docs/architecture-reference/architecture.md`.
  Handling: local bundled reference owned by this repo; eval prompts are
  original synthetic scenarios for mode selection, OEF materialization,
  readiness classification, and static-vs-render evidence.
- Source: `references/procedures/**`, `references/scripts/**`, and
  `references/fixtures/README.md`.
  Handling: local procedure and fixture contracts; eval cases paraphrase the
  expected behavior without copying fixture XML, JSON, or rendered images.
