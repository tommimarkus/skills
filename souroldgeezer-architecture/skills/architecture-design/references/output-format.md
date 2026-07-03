Return evidence, notation, cross-notation links, quality, export readiness,
findings, footer. Build/Extract: package state, groups, blockers. Review:
`[ARCH-*] finding; evidence; severity; action`. Lookup: brief/footer.

Implementation-readiness review fields: implementation-readiness verdict, evidence
inventory, architecture-documentation findings, other source material findings,
skill/package issue classification, ArchiMate equivalence, Implementation impact;
do not duplicate API, UI, auth, IaC, test, or code internals.

Guards: apply `architecture.md` §5 (interface/service semantics,
component-interface ownership, Triggering for process sequencing); define the
view concern, allowed element types, and relationship types.

Evidence: disclose the selected release-resolved Dediren runtime version.
Runtime semantics and the notation-specific `source-valid` validation commands
are defined in `architecture.md` §9.

Ownership/layout: imported release bundles are upstream artifacts; report
`Dediren tool issues`. Packages define per-view `projection`, `metadata`,
`layout`, `render`; generated metadata, layouts, SVGs, optional OEF/XMI are
reproducible output.
When the `architecture.md` §9 grouped-layout fallback was used, report the
regression plus both validation counts.

Export readiness never claims bare "ready": qualify with coverage — views
exported vs. total actual views, and content kinds exported vs. authored (per
[external-validation-handoff](procedures/external-validation-handoff.md)
required disclosures) — e.g. `OEF ready (1 of 2 views)`, `XMI ready (classes
only)`. A lossy export with an `ok` envelope is still lossy evidence.

Cross-notation: report UML to ArchiMate `properties.uml.architecture_context`
links as handoff evidence. Broken targets, missing source evidence, or UML detail
that contradicts linked ArchiMate intent cap cross-notation readiness.

Visual readiness: layout-valid is not visually clean. Emit `ARCH-L-3`,
`ARCH-R-3`, or `ARCH-Q-2` for dense, hub fanout, label-obscured, route-congested,
group-imbalanced, or mixed concerns. Tune `layout_preferences` (`architecture.md`
§9) for placement problems and re-validate before reporting or splitting.

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
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed; Export readiness: not requested | OEF ready (<coverage>) | XMI ready (<coverage>) | blocked
Cross-notation links: none | UML elaborates ArchiMate <ids> | broken <ids> | not assessed
Handoff boundary: architecture/design model | companion material required | delegated to <skill>
Diagram kind: <primary>; views: <n>; missing kinds: <list|none>; View groups: <n> source-backed groups | none
Semantic grouping: layout-only groups are not ArchiMate Grouping elements | semantic-boundary semantic_source_id | not assessed
Customization profile: none | local properties | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none
Grouped layout fallback: not needed | used ungrouped fallback | not run
Layout/render options: layout_preferences none | <view: knobs>; render static SVG | interactive <svg|html|both>; raster png no | yes
Implementation readiness: sufficient | partial | insufficient | not assessed
Finding split: <n> architecture-documentation findings; <n> other source material findings
ArchiMate equivalence: direct | partial | metadata/companion | none | not assessed
Findings: <n> blocking ARCH-*
Dediren tool issues: <none|issues; upstream or blocked report>
```
