# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Pre-Flight

1. Determine `docs/architecture/<feature>.dediren/`, diagram kind, and quality
   target. Default to `view-readable` for Build/Extract and `review-ready` for
   Review.
2. If optional OEF export is requested, require `export-policy.json`.
3. Run the dediren self-check before claiming runtime evidence.
4. Preserve ids, labels, policies, and source evidence unless invalid or stale.

## Build

Create or update `model.json`, `project.json`, render policy, and render
metadata from architect intent. Add actual views only. Validate, project,
layout, layout-validate, and render changed views.

## Extract

Read source, IaC, workflows, APIs, and UI routes that are in scope. Lift only
extractable facts into package source. Mark Business Process, Event, and
Interaction candidates with source evidence. Leave Business-other, Motivation,
Strategy, and Physical claims as architect-owned intent.

Create source-backed groups when source structure exposes ownership, hosting,
trust, environment, dependency, system responsibility, or orchestration
boundaries. Put them in `model.json` under
`plugins.generic-graph.views[].groups`, not `project.json`, with stable ids,
labels, and member ids that also appear in that view. Do not add decorative
groups without source evidence or architect intent.

## Review

Review without mutation by default. Check source validity, `project.json`
references, per-view projection/layout, SVG quality, optional export only when
requested or supplied, and drift when requested. Lead with findings and cap
quality at the strongest evidence-backed level.

## Lookup

Answer the narrow notation, package, source mapping, or reverse-lookup question
without editing files. Cite the package path and any source ids used.

## Generated Output

Treat `generated/` as reproducible output. Recreate it through dediren commands
when evidence is needed, but do not make it the canonical source.
