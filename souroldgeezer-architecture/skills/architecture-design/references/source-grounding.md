# Source Grounding

Behavioral evals are original synthetic cases from local workflow, references,
lifting rules, and fixtures. Dediren source is editable; SVG is visual proof;
OEF is optional compatibility output.

- `../../../docs/architecture-reference/architecture.md`: local reference for
  mode, source quality, readiness, render, and export evidence.
- `references/procedures/**` and `references/fixtures/dediren/basic/**`: local
  contracts/fixtures; evals paraphrase behavior, not artifacts.
- Repo feedback: source-backed groups belong in `model.json` under
  `plugins.generic-graph.views[].groups`; avoid grouping simple linear process
  flows unless responsibility, trust, participant, or orchestration changes the
  reading.
- Local dediren 0.8.3 review: the bundled dediren 0.8.3 runtime enforces
  ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
  `TechnologyNode`, reports close parallel route channels, and adds semantic
  group roles plus cross-group route validation coverage.
- User-supplied downstream OEF or Lead EA feedback becomes synthetic coverage;
  report supplied evidence without bundling it.
- The standards review notes are local, ignored working notes under
  `docs/notes/archimate-32-conformity/`; shipped guidance paraphrases them and
  does not copy ArchiMate manual prose.
- The session-scoped agent-friendly extracted ArchiMate 3.2 reference
  rechecked conformance boundaries, viewpoints, customization, grouping,
  connectors, Business `Representation`, and Application Interface/Service
  semantics. It must not be copied into shipped artifacts.
- Current dediren provides `validate --plugin generic-graph --profile
  archimate` as the source-level ArchiMate semantic gate; plain `validate`
  remains structural schema validation.
- The skill distinguishes layout-only groups from semantic-boundary groups; a
  semantic Grouping claim needs `semantic_source_id` to a `Grouping` source node.
  Relationship connectors and junctions remain unsupported in package source.
