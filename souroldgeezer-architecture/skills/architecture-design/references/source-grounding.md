# Source Grounding

Behavioral evals are original synthetic cases from local workflow, references,
lifting rules, and fixtures.

- `../../../docs/architecture-reference/architecture.md`: local authority.
- `references/procedures/**` and `references/fixtures/dediren/basic/**`: local
  contracts; evals paraphrase behavior, not artifacts.
- Repo feedback: source-backed groups belong in `model.json` under
  `plugins.generic-graph.views[].groups`; simple linear flows stay ungrouped
  unless responsibility, trust, participant, or orchestration changes reading.
- The bundled dediren 0.9.0 runtime enforces ArchiMate® 3.2 relationship
  endpoint legality, expects `Node`, not `TechnologyNode`, reports close
  parallel route channels, validates semantic group routes, and uses
  `plugins.generic-graph.semantic_profile` for generated ArchiMate render
  metadata without requiring the OEF export plugin.
- The standards review notes are local, ignored working notes under
  `docs/notes/archimate-32-conformity/`; shipped guidance paraphrases them.
- The session-scoped agent-friendly extracted ArchiMate 3.2 reference rechecked
  conformance boundaries, viewpoints, customization, grouping, connectors, and
  Application Interface/Service semantics; do not copy it into shipped files.
- `validate --plugin generic-graph --profile archimate` is the semantic gate;
  plain `validate` is schema validation. Layout-only groups are not
  semantic-boundary groups; semantic Grouping needs `semantic_source_id`;
  relationship connectors and junctions remain unsupported.
- Package feedback: dediren 0.9.0 allows parallel per-view ELK layout with
  serial rerun as a diagnostic fallback; inspect valid SVGs for density, hub
  fanout, long routes, group balance, and mixed concerns; separate hand-authored
  source/policies from generated render metadata/layout/SVG/OEF.
- Repo ownership feedback: `tools/dediren-linux/**` is an imported upstream
  artifact. Tool defects belong upstream; issue-filing mechanics are
  agent-local. This repo changes repo-owned guidance, fixtures, and docs unless
  importing a new upstream release bundle.
- Render metadata follow-up: skills issue `#50` and upstream
  `tommimarkus/dediren#1` showed that dediren 0.8.4 emitted generic render
  metadata unless `archimate-oef` was listed for an ArchiMate package. Dediren
  0.9.0 fixed this through explicit `generic-graph.semantic_profile` support,
  so guidance now keeps `archimate-oef` export-only again.
- Layout concurrency follow-up: skills issue `#51` refreshed the historical
  `#47` ELK concurrency guidance; dediren 0.9.0 evidence confirms parallel
  per-view layout batches passing, with serial rerun kept only as a diagnostic
  fallback.
