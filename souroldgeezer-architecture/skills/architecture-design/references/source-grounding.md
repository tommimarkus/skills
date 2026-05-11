# Source Grounding

The dediren package is the agent-editable model, SVG is the primary visual
proof, and OEF is optional compatibility output. Behavioral evals are original
synthetic cases derived from local package workflow, references, lifting rules,
and fixtures.

- `../../../docs/architecture-reference/architecture.md`: local reference;
  evals cover mode selection, source quality, readiness, render evidence, and
  optional export evidence.
- `references/procedures/**`: local procedure contracts; evals paraphrase
  behavior without copying package artifacts.
- `references/fixtures/dediren/basic/**`: local fixture; evals reference the
  workflow shape, not third-party diagrams or examples.
- Repo-local Extract feedback: keep source-backed groups for evidenced
  ownership, hosting, trust, environment, or dependency boundaries.
- Repo-local incremental extraction feedback: locate groups in `model.json`
  under `plugins.generic-graph.views[].groups` and avoid grouping simple linear
  process flows unless responsibility, trust, participant, or orchestration
  boundaries change the architectural reading.
- User-supplied downstream OEF validation: use synthetic scenarios unless the
  current task supplies evidence; report supplied evidence without bundling it.
