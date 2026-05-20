Return evidence, notation, cross-notation links, quality, export readiness,
findings, footer. Build/Extract: package state, groups, blockers. Review:
`[ARCH-*] finding; evidence; severity; action`. Lookup: brief/footer.

Implementation-readiness review fields: implementation-readiness verdict, evidence
inventory, architecture-documentation findings, other source material findings,
skill/package issue classification, ArchiMate equivalence, Implementation impact;
do not duplicate API, UI, auth, IaC, test, or code internals.

Guards: APIs and GUIs are Application Interfaces; Application Services model the
functionality exposed through an interface; if semantic validation accepts
Application Component to Application Interface Realization, do not report it as
endpoint-illegal; Prefer Composition or Aggregation for component-interface
ownership; Use Triggering when the architectural claim is process sequencing;
define the view concern, allowed element types, and relationship types.

Evidence: disclose the selected bundled Dediren runtime version; it checks
ArchiMate® 3.2 relationship endpoint legality, expects `Node`, not
`TechnologyNode`, reports close parallel route channels, allows parallel
per-view ELK layout with serial rerun. source-valid requires schema plus ArchiMate semantic validation:
`dediren validate --plugin generic-graph --profile archimate`. UML source-valid requires schema plus
`dediren validate --plugin generic-graph --profile uml`.

Ownership/layout: imported bundles are upstream artifacts; report `Dediren tool
issues`. Packages define per-view `projection`, `metadata`, `layout`, `render`;
generated metadata, layouts, SVGs, optional OEF/XMI are reproducible output.
If grouped layout validation still reports connector-through-node, invalid route,
or group-boundary warnings, rerun the same view without groups. If cleaner, use
the cleaner layout as evidence and report the grouped-layout regression plus both
validation counts.

Cross-notation: report UML to ArchiMate `properties.uml.architecture_context`
links as handoff evidence. Broken targets, missing source evidence, or UML detail
that contradicts linked ArchiMate intent cap cross-notation readiness.

Visual readiness: layout-valid is not visually clean. Emit `ARCH-L-3`,
`ARCH-R-3`, or `ARCH-Q-2` for dense, hub fanout, label-obscured, route-congested,
group-imbalanced, or mixed concerns.

Source-weighted choices: `<n>`; low-confidence: `<n>`; architect-owned: `<n>`.
Use `Notable choices` only for non-obvious or challenged decisions:

```text
Notable choices:
- <source fact> -> <chosen concept/relation/view>; rejected <alternative>; evidence <source-backed|candidate-from-source|architect-owned|weak-evidence|overlay-only>
```

## Footer

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Package: docs/architecture/<feature>.dediren/
Notation: archimate | uml | mixed | unsupported
Dediren runtime: <path|not run>; Validation: source; semantic; projection; metadata; layout; layout validation; SVG; visual; OEF; XMI
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed; Export readiness: not requested | OEF ready | XMI ready | blocked
Cross-notation links: none | UML elaborates ArchiMate <ids> | broken <ids> | not assessed
Handoff boundary: architecture/design model | companion material required | delegated to <skill>
Diagram kind: <primary>; views: <n>; missing kinds: <list|none>; View groups: <n> source-backed groups | none
Semantic grouping: layout-only groups are not ArchiMate Grouping elements | semantic-boundary semantic_source_id | not assessed
Customization profile: none | local properties | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none
Grouped layout fallback: not needed | used ungrouped fallback | not run
Implementation readiness: sufficient | partial | insufficient | not assessed
Finding split: <n> architecture-documentation findings; <n> other source material findings
ArchiMate equivalence: direct | partial | metadata/companion | none | not assessed
Findings: <n> blocking ARCH-*
Dediren tool issues: <none|issues; upstream or blocked report>
```
