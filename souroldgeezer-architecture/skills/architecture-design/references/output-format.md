Use after mode selection. Every answer discloses evidence, quality, export
readiness, findings, and the footer.

## Build

Report package path, `build`, quality, export readiness, runtime path or
missing-bundle disclosure, views/missing kinds, validation/render/export state,
and blocking finding count.

## Extract

Report package, `extract`, sources read, lifted layer counts, source-backed
groups, unsupported grouping candidates, grouped layout fallback, architect-owned
layers, validation/render/drift state, and findings.

## Review

Lead with findings in this shape: `[ARCH-*] finding; evidence; severity; action`.
Then report quality, export readiness, change classification, package, runtime,
validation/layout/SVG/OEF state. One code per finding; no `review-ready` with a
block.

Semantic checks: APIs and GUIs are Application Interfaces; Application Services
model the functionality exposed through an interface; Application Components
must not realize Application Interfaces; compose today and aggregate for
ArchiMate 4. "Use Triggering when the architectural claim is process
sequencing"; define the view concern, allowed element types, and relationship
types.

Runtime checks: disclose the bundled dediren 0.3.0 runtime when used; it checks
ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
`TechnologyNode`, for technology nodes, and can report close parallel route
channels during layout validation.

Evidence checks: source-valid requires schema plus ArchiMate semantic validation.
Do not report source-valid from plain `dediren validate` alone; run `dediren
validate --plugin generic-graph --profile archimate`.

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
Grouped layout fallback: not needed | used ungrouped fallback after grouped route warnings | not run
Validation: source <state>; projection <state>; layout <state>; layout validation <state>; SVG <state>; OEF <state>
Runtime-verified drift: <n findings|not run>
Findings: <n> blocking ARCH-* findings
Dediren tool issues: <none|semantic validation, layout, render, or export gaps to raise upstream>
Change classification: semantic model <yes|no>; view/layout <yes|no>; render metadata/policy <yes|no>; export policy <yes|no>; docs only <yes|no>
```
