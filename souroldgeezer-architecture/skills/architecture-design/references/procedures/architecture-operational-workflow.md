# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Pre-Flight

Determine package, diagram kind, quality target, export need, and runtime.
Default to `view-readable` for Build/Extract and `review-ready` for Review.
Preserve ids, labels, policies, and source evidence unless invalid/stale.

## Build

Create/update source and policies from architect intent. Add actual views only;
validate, project, layout, layout-validate, and render changed views.

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

The bundled dediren 0.6.0 runtime enforces ArchiMate® 3.2 relationship endpoint
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

If grouped layout validation still reports connector-through-node, invalid
route, or group-boundary warnings, rerun the same view without groups. If
cleaner, keep source-backed groups, use the cleaner layout as evidence and
report the grouped-layout regression plus both validation counts.

Also inspect dediren 0.6.0 layout warnings for route detours and close parallel
route channels before claiming render-readiness.

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
