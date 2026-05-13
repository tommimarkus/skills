# Source Grounding

Behavioral evals are original synthetic cases derived from local workflow,
references, lifting rules, and fixtures. Dediren package source is
agent-editable; SVG is visual proof; OEF is optional compatibility output.

- `../../../docs/architecture-reference/architecture.md`: local reference for
  mode selection, source quality, readiness, render, and export evidence.
- `references/procedures/**` and `references/fixtures/dediren/basic/**`: local
  contracts/fixtures; evals paraphrase behavior, not package artifacts.
- Repo feedback: source-backed groups belong in `model.json` under
  `plugins.generic-graph.views[].groups`; avoid grouping simple linear process
  flows unless responsibility, trust, participant, or orchestration changes the
  reading.
- Local dediren 0.3.0 release review: the bundled dediren 0.3.0 runtime
  enforces ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
  `TechnologyNode`, for technology nodes, and reports close parallel route
  channels in layout validation.
- User-supplied downstream OEF or Lead EA feedback becomes synthetic coverage;
  report supplied evidence without bundling it.
