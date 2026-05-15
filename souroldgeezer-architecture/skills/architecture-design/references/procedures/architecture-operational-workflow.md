# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Pre-Flight

Determine package, diagram kind, quality target, export need, and runtime.
Default to `view-readable` for Build/Extract and `review-ready` for Review.
Preserve ids, labels, policies, and source evidence unless invalid/stale.

Treat the packaged Dediren bundle as upstream-owned runtime evidence. Do not
patch files under `souroldgeezer-architecture/tools/dediren-linux/` or future
platform bundle directories to fix tool behavior. When Dediren itself appears
wrong, report it under `Dediren tool issues` with repro evidence; issue-filing
mechanics belong in agent-local configuration.

## Build

Create/update source and policies from architect intent. Add actual views only;
validate, project layout requests, project render metadata, run ELK layout
commands serially, layout-validate, and render changed views.

## Package JSON Generation

For clean-slate packages, copy the basic fixture shape and then edit source
content. Keep `model.json`, `project.json`, `render-policy.json`, package-level
`render-metadata.json` when deliberately maintained, and optional
`export-policy.json` as checked-in source/policy files. Treat projections,
per-view render metadata, layout results, SVG, and optional OEF intermediates
under `generated/` as reproducible output.

Each view in `project.json` should declare:

- `projection` for `generic-graph` `layout-request`;
- `metadata` for `generic-graph` `render-metadata` with a
  `generated/render-metadata/<view>.json` output;
- `layout` for `elk-layout` output;
- `render` for `svg-render` policy, metadata, and SVG output.

Render with the generated per-view metadata when it is declared. Use the
checked-in package-level `render-metadata.json` only when the package owner
intentionally keeps one synchronized shared metadata file.

## Semantic Modeling Guard

Before readiness, check APIs and GUIs are Application Interfaces, Application
Services model the functionality exposed through an interface, Use Triggering
when the architectural claim is process sequencing, and define the view concern,
allowed element types, and relationship types. Do not override semantic
validation with local endpoint bans; if it accepts Application Component to
Application Interface Realization, do not report it as endpoint-illegal. Prefer
Composition or Aggregation for component-interface ownership. If dediren accepts
a suspect model, keep the `ARCH-*` finding and list the gap under `Dediren tool
issues`.

Relationship connectors and junctions are unsupported in dediren package source.
Report that limitation instead of inventing ordinary-element stand-ins.

The bundled dediren 0.8.3 runtime enforces ArchiMate® 3.2 relationship endpoint
legality during ArchiMate® metadata/export paths. Use `Node`, not
`TechnologyNode`, for technology nodes in ArchiMate® packages.

## Extract

Read source/IaC/workflows/APIs/UI routes. Lift extractable facts only: Business
Process/Event/Interaction candidates need evidence; Business-other, Motivation,
Strategy, and Physical claims stay architect-owned.

Create source-backed groups for ownership, hosting, trust, environment,
dependency, responsibility, or orchestration boundaries. Put them in
`model.json` under `plugins.generic-graph.views[].groups`, not `project.json`,
with stable ids/labels/member ids. Use `role: "layout-only"` for visual groups;
use `semantic_source_id` to a `Grouping` node for ArchiMate semantic Grouping.
No decorative groups.

Layout-only groups are not ArchiMate Grouping elements. Semantic-boundary groups
only claim ArchiMate Grouping when they are backed by a `Grouping` source node.

## Grouped Layout Guard

Run per-view `layout --plugin elk-layout` commands serially. Current packaged
dediren can return invalid JSON envelopes when multiple ELK layout invocations
start concurrently. A parallel-only layout failure must be rerun serially
before it becomes an `ARCH-L-1` finding, and repeated parallel-only failures
must be reported as upstream Dediren tool defects rather than patched in this
repo's bundle.

If grouped layout validation still reports connector-through-node, invalid
route, or group-boundary warnings, rerun the same view without groups. If
cleaner, keep source-backed groups, use the cleaner layout as evidence and
report the grouped-layout regression plus both validation counts.

Also inspect dediren 0.8.3 layout warnings for route detours and close parallel
route channels before claiming render-readiness. Layout-valid is not visually
clean: inspect density, fanout, long routes, group balance, labels, and
viewpoint focus before claiming a view is clean enough for the audience.

## Review

Review without mutation by default. Check schema, ArchiMate semantic validation
with `validate --plugin generic-graph --profile archimate`, `project.json`,
projection, layout, SVG, optional export, and requested drift. Lead with
findings and cap quality at proven evidence. Plain `dediren validate` is not
ArchiMate semantic validity.

## Lookup

Answer the narrow notation/package/source-mapping/reverse-lookup question
without edits. Cite package path and source ids used.

## Generated Output

Treat `generated/` as reproducible output. Recreate it through dediren commands
when evidence is needed, but do not make it the canonical source.
