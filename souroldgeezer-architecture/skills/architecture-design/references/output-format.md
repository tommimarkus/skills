Use after mode selection. Disclose evidence, quality, export readiness,
findings, and the footer.

## Build

Report package path, quality, export readiness, runtime, views/missing kinds,
validation/render/export state, and blocking finding count.

## Extract

Report package, sources read, lifted counts, source-backed groups, unsupported
grouping candidates, grouped layout fallback, architect-owned layers,
validation/render/drift state, and findings.

## Review

Lead with findings: `[ARCH-*] finding; evidence; severity; action`. Then
report quality, export readiness, change classification, package, runtime, and
validation/layout/SVG/OEF state. One code per finding; no `review-ready` with a
block.

Semantic checks: APIs and GUIs are Application Interfaces; Application Services
model the functionality exposed through an interface; Application Component to
Application Interface Realization is ArchiMate 3.2-legal, not
endpoint-illegal; Prefer Composition or Aggregation for component-interface
ownership when that is the claim; Use Triggering when the architectural claim is
process sequencing; define the view concern, allowed element types, and
relationship types.

Runtime checks: disclose the bundled dediren 0.5.0 runtime when used; it checks
ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
`TechnologyNode`, for technology nodes, and reports close parallel route
channels during layout validation.

Evidence checks: source-valid requires schema plus ArchiMate semantic validation.
Plain `dediren validate` is not enough; run `dediren validate --plugin
generic-graph --profile archimate`.

If grouped layout validation reports connector-through-node, invalid route, or
group-boundary warnings, rerun the same view without groups. If the ungrouped
layout validates cleaner, use the cleaner layout as evidence and report the
grouped-layout regression with both validation counts.

## Lookup

Answer in two to four lines plus footer. Do not mutate the package.

## Footer

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Package: docs/architecture/<feature>.dediren/
Dediren runtime: <linux path> | <macos path> | not run (missing dediren bundle)
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed
Export readiness: not requested | export-ready | blocked (missing export-policy.json)
Diagram kind: <primary kind>; views: <n>; missing kinds: <list|none>
View groups: <n> source-backed groups | none | not assessed
Semantic grouping: layout/source groups are not ArchiMate Grouping elements | semantic Grouping modeled | not assessed
Customization profile: none | local properties only | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none identified
Grouped layout fallback: not needed | used ungrouped fallback after grouped route warnings | not run
Validation: source <state>; projection <state>; layout <state>; layout validation <state>; SVG <state>; OEF <state>
Runtime-verified drift: <n findings|not run>
Findings: <n> blocking ARCH-* findings
Dediren tool issues: <none|semantic validation, layout, render, or export gaps to raise upstream>
Change classification: semantic model <yes|no>; view/layout <yes|no>; render metadata/policy <yes|no>; export policy <yes|no>; docs only <yes|no>
```
