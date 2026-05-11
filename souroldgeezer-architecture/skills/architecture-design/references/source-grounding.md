# Source Grounding

The architecture package exists because dediren source is the agent-editable
model and SVG is the primary visual proof. OEF is an optional compatibility
export. Behavioral evals are repo-authored synthetic cases derived from the
dediren package workflow, architecture reference, source lifting rules, and
fixture package.

- Source: `../../../docs/architecture-reference/architecture.md`.
  Handling: local bundled reference owned by this repo; eval prompts are
  original synthetic scenarios for mode selection, package source quality,
  readiness classification, render evidence, and optional export evidence.
- Source: `references/procedures/**`.
  Handling: local procedure contracts; eval cases paraphrase the expected
  behavior without copying model, layout, render, or export artifacts.
- Source: `references/fixtures/dediren/basic/**`.
  Handling: local package fixture; eval cases refer to the workflow shape and
  not to third-party diagrams or copied examples.
- Source: user-supplied downstream validation reports for optional OEF exports.
  Handling: synthetic scenario only unless the user provides concrete evidence
  in the current task; report supplied evidence in Review output without
  bundling it into the skill.
