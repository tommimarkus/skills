# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Core Pass

- Pre-flight: identify package, diagram kind, quality target, export need, and
  runtime. Default to `view-readable` for Build/Extract and `review-ready` for
  Review. Preserve ids, labels, policies, evidence unless invalid/stale.
- Runtime boundary: the packaged bundle is imported upstream evidence. Do not
  patch files under `souroldgeezer-architecture/tools/dediren-linux/` or future
  bundles. Report `Dediren tool issues` with version, command, input summary,
  envelope/error, expected behavior, repro evidence; issue-filing mechanics
  stay agent-local.
- Build: create/update source and policies from architect intent; add actual
  views only. Validate, project layout requests and render metadata, run layout
  commands serially, validate layout, render changed views.
- Clean-slate package: start from the basic fixture, then replace content.
  Hand-authored source/policy files are `model.json`, `project.json`,
  `render-policy.json`, maintained `render-metadata.json`, optional
  `export-policy.json`. Generated projections, per-view render metadata,
  layouts, SVG, and optional OEF under `generated/` are reproducible output.
- `project.json` view recipe: `projection` for `generic-graph`
  `layout-request`; `metadata` for `generic-graph` `render-metadata` at
  `generated/render-metadata/<view>.json`; `layout` for `elk-layout`; `render`
  for `svg-render`. Render with generated per-view metadata when declared.
- Semantic guard: APIs and GUIs are Application Interfaces; Application
  Services model the functionality exposed through an interface; Use Triggering
  when the architectural claim is process sequencing; define the view concern,
  allowed element types, and relationship types. If validation accepts
  Application Component to Application Interface Realization, do not report it
  as endpoint-illegal. Prefer Composition or Aggregation for
  component-interface ownership. If dediren accepts a suspect model, keep an
  `ARCH-*` finding and list the gap under `Dediren tool issues`.
- Runtime semantics: the bundled dediren 0.8.3 runtime enforces ArchiMate® 3.2
  relationship endpoint legality, expects `Node`, not `TechnologyNode`, reports
  close parallel route channels, and needs
  `validate --plugin generic-graph --profile archimate` for `source-valid`.
- Unsupported source: relationship connectors and junctions are unsupported in
  dediren package source; report the limitation.
- Extract: lift source/IaC/workflow/API/UI facts only when evidenced.
  Business-other, Motivation, Strategy, and Physical claims stay architect-owned.
- Groups: create source-backed groups for ownership, hosting, trust,
  environment, dependency, responsibility, or orchestration boundaries. Put them
  in `model.json` under `plugins.generic-graph.views[].groups`, not
  `project.json`, with stable ids/labels/members. `role: "layout-only"` is only
  visual; semantic-boundary Grouping needs `semantic_source_id` to a `Grouping`
  source node. Layout-only groups are not ArchiMate Grouping elements.
- Grouped layout: run `layout --plugin elk-layout` serially. Rerun
  parallel-only failures serially before `ARCH-L-1`. If grouped layout
  validation still reports connector-through-node, invalid route, or
  group-boundary warnings, rerun the same view without groups. If cleaner, keep
  source-backed groups, use the cleaner layout as evidence and report the
  grouped-layout regression plus both validation counts.
- Visual readiness: layout-valid is not visually clean. Inspect density, fanout,
  long routes, group balance, labels, congestion, and viewpoint focus.
- Review/Lookup: Review does not mutate by default and leads with findings.
  Lookup answers only the narrow question and cites package path/source ids.
