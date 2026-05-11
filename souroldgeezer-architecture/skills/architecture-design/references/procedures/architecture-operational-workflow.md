# Architecture Operational Workflow

Use after `SKILL.md` selects Build, Extract, Review, or Lookup.

## Pre-Flight

1. Determine the feature slug and package path
   `docs/architecture/<feature>.dediren/`.
2. Determine the requested diagram kind and quality target. Default to
   `view-readable` for Build/Extract and `review-ready` for Review.
3. Check whether optional OEF export is requested. If yes, require
   `export-policy.json`.
4. Run the dediren runtime self-check before claiming runtime evidence.
5. Preserve existing ids and source evidence unless they are invalid or stale.

## Build

Create or update `model.json`, `project.json`, render policy, and render
metadata from architect intent. Add only actual views. Run source validation,
projection, layout, layout validation, and SVG render for changed views.

## Extract

Read source, IaC, workflows, APIs, and UI routes that are in scope. Lift only
extractable facts into package source. Mark Business Process, Event, and
Interaction candidates with source evidence. Leave Business-other, Motivation,
Strategy, and Physical claims as architect-owned intent.

## Review

Review the package without mutating it by default. Check:

- source validity and relationship correctness;
- `project.json` view/plugin/policy references;
- per-view projection and layout evidence;
- SVG render quality for requested or changed views;
- optional OEF export only when requested or supplied;
- drift against current source when requested.

Lead with findings. Cap quality at the strongest level supported by evidence.

## Lookup

Answer the narrow notation, package, source mapping, or reverse-lookup question
without editing files. Cite the package path and any source ids used.

## Generated Output

Treat `generated/` as reproducible output. Recreate it through dediren commands
when evidence is needed, but do not make it the canonical source.
