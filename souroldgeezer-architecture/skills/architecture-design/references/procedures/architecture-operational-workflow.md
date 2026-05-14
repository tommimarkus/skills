# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Pre-Flight

Determine package, diagram kind, quality target, export need, and runtime.
Default to `view-readable` for Build/Extract and `review-ready` for Review.
Preserve ids, labels, policies, and source evidence unless invalid or stale.

## Build

Create/update source and policies from architect intent. Add actual views only.
Validate, project, layout, layout-validate, and render changed views.

## Semantic Modeling Guard

Before readiness, check APIs/GUIs as Application Interfaces, services as exposed
functionality, Application Component to Application Interface Realization is
ArchiMate 3.2-legal but less expressive than whole/part interface ownership,
process sequence as Triggering, and one concern/vocabulary per view. Prefer
Composition or Aggregation for component-interface ownership when that is the
model claim. If dediren accepts a suspect model, keep the `ARCH-*` finding and
list the gap under `Dediren tool issues`.

Relationship connectors and junctions are unsupported in dediren package
source. If the requested model needs them, report the limitation and the
nearest explicit repair path instead of inventing ordinary elements as
stand-ins.

The bundled dediren 0.5.0 runtime enforces ArchiMate® 3.2 relationship endpoint
legality during ArchiMate® metadata/export paths. Use `Node`, not
`TechnologyNode`, for technology nodes in ArchiMate® packages.

## Extract

Read in-scope source/IaC/workflows/APIs/UI routes. Lift only extractable facts:
Business Process/Event/Interaction candidates need source evidence; Business-
other, Motivation, Strategy, and Physical claims stay architect-owned.

Create source-backed groups for ownership, hosting, trust, environment,
dependency, system responsibility, or orchestration boundaries. Put them in
`model.json` under `plugins.generic-graph.views[].groups`, not `project.json`,
with stable ids/labels/member ids. No decorative groups.

These layout/source groups are not ArchiMate Grouping elements. If the
architecture claim is a real ArchiMate Grouping concept, model or report the
semantic grouping explicitly rather than encoding it only as a layout group.

## Grouped Layout Guard

If grouped layout validation reports connector-through-node, invalid route, or
group-boundary warnings, rerun the same view without groups. If cleaner, keep
source-backed groups in source, use the cleaner layout as evidence and report
the grouped-layout regression with validation counts.

Also inspect dediren 0.5.0 layout warnings for route detours and close parallel
route channels before claiming render-readiness.

## Review

Review without mutation by default. Check schema, ArchiMate semantic validation
with `validate --plugin generic-graph --profile archimate`, `project.json`,
projection, layout, SVG, optional export when requested/supplied, and drift when
requested. Lead with findings and cap quality at proven evidence. Do not present
plain `dediren validate` alone as ArchiMate semantic validity.

## Lookup

Answer the narrow notation/package/source-mapping/reverse-lookup question
without edits. Cite package path and source ids used.

## Generated Output

Treat `generated/` as reproducible output. Recreate it through dediren commands
when evidence is needed, but do not make it the canonical source.
