Use after mode selection. Disclose evidence, quality, export readiness,
findings, and footer.

Modes: Build/Extract report package, evidence state, quality, export readiness,
source-backed groups when relevant, and blockers. Review leads with
`[ARCH-*] finding; evidence; severity; action`; Lookup is two to four lines plus
footer. Review/Lookup do not mutate by default.

Guards: APIs and GUIs are Application Interfaces; Application Services model
the functionality exposed through an interface; if semantic validation accepts
Application Component to Application Interface Realization, do not report it as
endpoint-illegal; Prefer Composition or Aggregation for component-interface
ownership; Use Triggering when the architectural claim is process sequencing;
define the view concern, allowed element types, and relationship types.

Evidence: disclose the bundled dediren 0.8.4 runtime. It checks ArchiMate® 3.2
relationship endpoint legality, expects `Node`, not `TechnologyNode`, reports
close parallel route channels, and allows parallel per-view ELK layout with
serial rerun as a diagnostic fallback for parallel-only failures.
source-valid requires schema plus ArchiMate semantic validation:
`dediren validate --plugin generic-graph --profile archimate`.

Ownership/layout: `souroldgeezer-architecture/tools/dediren-linux/` is an
imported upstream artifact. Do not patch bundle bugs; report `Dediren tool
issues` and keep issue-filing mechanics agent-local. Clean-slate packages define
per-view `projection`, `metadata`, `layout`, `render`; generated metadata,
layouts, SVGs, optional OEF are reproducible output. If grouped layout
validation still reports connector-through-node, invalid route, or
group-boundary warnings, rerun the same view without groups. If cleaner, use the
cleaner layout as evidence and report the grouped-layout regression plus both
validation counts.

Visual readiness: layout-valid is not visually clean. Emit `ARCH-L-3`,
`ARCH-R-3`, or `ARCH-Q-2` for dense, hub-heavy/hub fanout, label-obscured,
route-congested, over-wide, group-imbalanced, or mixed concerns.

## Footer

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Package: docs/architecture/<feature>.dediren/
Dediren runtime: <path|not run>
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed
Export readiness: not requested | ready | blocked
Diagram kind: <primary kind>; views: <n>; missing kinds: <list|none>
View groups: <n> source-backed groups | none
Semantic grouping: layout-only groups are not ArchiMate Grouping elements | semantic-boundary semantic_source_id | not assessed
Customization profile: none | local properties | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none identified
Grouped layout fallback: not needed | used ungrouped fallback | not run
Validation: source; projection; render metadata; layout; layout validation; SVG; visual readiness; OEF
Runtime-verified drift: <n findings|not run>
Findings: <n> blocking ARCH-* findings
Dediren tool issues: <none|issues; upstream or blocked report>
Change classification: semantic model; view/layout; render metadata/policy; export policy; docs only
```
