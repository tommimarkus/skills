# Source Grounding

Behavior evals are synthetic. Local authority:
`../../../docs/architecture-reference/architecture.md`.

- Source-backed groups belong in `model.json` under `plugins.generic-graph.views[].groups`; simple linear flows stay ungrouped unless responsibility, trust, participant, or orchestration changes reading.
- The bundled Dediren runtime enforces ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not `TechnologyNode`, reports close parallel route channels, supports `plugins.generic-graph.semantic_profile`, allows parallel per-view ELK layout, keeps serial rerun fallback.
- ArchiMate and UML are supported `generic-graph` semantic profiles for `architecture-design`; UML uses `validate --plugin generic-graph --profile uml`, view kinds `uml-class` / `uml-data` / `uml-activity`, optional `uml-xmi` export, and `properties.uml` for attributes, operations, multiplicities, guards, partitions, and optional architecture context.
- The bundled `tools/dediren-linux/docs/agent-usage.md` guide is the runtime-local fast contract for source JSON authoring, command handoff, and repair loops.
- Cross-notation support is optional upward UML context to ArchiMate through `properties.uml.architecture_context` and `relationship: "elaborates"`; validate referenced ids at the skill level because schema validation alone permits open properties.
- The standards review notes are local, ignored working notes; the agent-friendly extracted ArchiMate 3.2 reference checked conformance, viewpoints, customization, grouping, connectors, Interface/Service semantics.
- Source-weighting distills standards/practitioner/research/artifact/platform sources into a source evidence evaluator; no local corpus paths ship.
- `validate --plugin generic-graph --profile archimate` is the semantic gate; layout-only groups are not semantic-boundary groups; semantic Grouping needs `semantic_source_id`; relationship connectors and junctions remain unsupported.
- `tools/dediren-linux/**` is an imported upstream artifact; tool defects go upstream and issue-filing mechanics are agent-local.
- The implementation-readiness review notes are local, ignored working notes; shipped guidance paraphrases the outcome into `implementation-readiness-review.md` plus a synthetic implementation-readiness eval.
- Source-weighting was refreshed from standards/method sources for semantic and viewpoint defaults, practitioner sources for app-layer and relationship defaults, enterprise-practice sources for business-claim evidence gates, and portfolio/cloud sources for overlay-only guidance; local extracted corpora remain authoring aids and do not ship as cited paths.
