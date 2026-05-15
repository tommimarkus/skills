# Source Grounding

Behavioral evals are original synthetic cases from local workflow, references,
lifting rules, and fixtures.

- `../../../docs/architecture-reference/architecture.md`: local authority.
- `references/procedures/**` and `references/fixtures/dediren/basic/**`: local
  contracts; evals paraphrase behavior, not artifacts.
- Repo feedback: source-backed groups belong in `model.json` under
  `plugins.generic-graph.views[].groups`; simple linear flows stay ungrouped
  unless responsibility, trust, participant, or orchestration changes reading.
- The bundled dediren 0.8.4 runtime enforces ArchiMate® 3.2 relationship
  endpoint legality, expects `Node`, not `TechnologyNode`, reports close
  parallel route channels, and validates semantic group routes.
- The standards review notes are local, ignored working notes under
  `docs/notes/archimate-32-conformity/`; shipped guidance paraphrases them.
- The session-scoped agent-friendly extracted ArchiMate 3.2 reference rechecked
  conformance boundaries, viewpoints, customization, grouping, connectors, and
  Application Interface/Service semantics; do not copy it into shipped files.
- `validate --plugin generic-graph --profile archimate` is the semantic gate;
  plain `validate` is schema validation. Layout-only groups are not
  semantic-boundary groups; semantic Grouping needs `semantic_source_id`;
  relationship connectors and junctions remain unsupported.
- Package feedback: serialize ELK layout evidence; inspect valid SVGs for
  density, hub fanout, long routes, group balance, and mixed concerns; separate
  hand-authored source/policies from generated render metadata/layout/SVG/OEF.
- Repo ownership feedback: `tools/dediren-linux/**` is an imported upstream
  artifact. Tool defects belong upstream; issue-filing mechanics are
  agent-local. This repo changes repo-owned guidance, fixtures, and docs unless
  importing a new upstream release bundle.
