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
- Source: architect-facing validation handoff scenarios involving downstream
  tool reports such as import errors, model validation output, or schema
  validation output.
  Handling: synthetic scenario only; no vendor output, screenshots, schemas, or
  issue text copied into eval cases.
