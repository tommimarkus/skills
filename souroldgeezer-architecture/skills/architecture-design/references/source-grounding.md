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
- Local dediren 0.5.0 release review: the bundled dediren 0.5.0 runtime
  enforces ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
  `TechnologyNode`, for technology nodes, and reports close parallel route
  channels in layout validation.
- User-supplied downstream OEF or Lead EA feedback becomes synthetic coverage;
  report supplied evidence without bundling it.
- The standards review notes are local, ignored working notes under
  `docs/notes/archimate-32-conformity/`; shipped guidance paraphrases those
  findings and does not copy ArchiMate manual prose.
- The agent-friendly extracted ArchiMate 3.2 reference under
  `ARCHIMATE32_AGENT_REF/` was used as session-scoped recheck evidence for
  conformance boundaries, viewpoint mechanism, customization, grouping,
  relationship connectors, Business `Representation`, and Application
  Interface/Application Service semantics. It is derived from the local PDF and
  should not be copied into shipped artifacts.
- Dediren 0.5.0 introduced `validate --plugin generic-graph --profile
  archimate` as the source-level ArchiMate semantic validation gate. Plain
  `validate` remains structural schema validation.
- The skill distinguishes dediren layout/source groups from ArchiMate Grouping
  elements, and treats relationship connectors and junctions as unsupported in
  package source until first-class runtime support exists.
