Return evidence, notation, cross-notation links, quality, export readiness,
findings, footer. Build/Extract: package state, groups, blockers. Build also
ends with the build readiness disclosure — architecture-owned concern classes
present vs. absent per
[implementation-readiness-review](procedures/implementation-readiness-review.md)
§ Build Readiness Disclosure. Review: `[ARCH-*] finding; evidence; severity;
action`. Lookup: brief/footer.

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
only)`. A single-view or classes-only export keeps an `ok` envelope but carries
`info` omission diagnostics (`DEDIREN_OEF_VIEWS_OMITTED`,
`DEDIREN_XMI_ELEMENTS_OMITTED` / `DEDIREN_XMI_RELATIONSHIPS_OMITTED`); read
`.diagnostics[]` — a partial export is still partial evidence.

Render readiness for a UML view that authors association end adornments
qualifies the same way: count rendered vs. authored end-adornment labels per
the `architecture.md` §9 end-adornment coverage check and carry the count in
the quality level — e.g. `render-ready (end adornments 4 of 4)`. A gap is
`ARCH-R-2` plus a `Dediren tool issues` entry, never an unqualified
`render-ready` — the pipeline reports `ok` envelopes while the diagram is
lossier than the model.

Cross-notation: report UML to ArchiMate `properties.uml.architecture_context`
links as handoff evidence. Broken targets, missing source evidence, or UML detail
that contradicts linked ArchiMate intent cap cross-notation readiness.

Visual readiness: layout-valid is not visually clean. Emit `ARCH-L-3`,
`ARCH-R-3`, or `ARCH-Q-2` for dense, hub fanout, label-obscured,
label-dissociated (`architecture.md` §7 label-to-own-edge check),
route-congested, group-imbalanced, or mixed concerns. Tune `layout_preferences`
(`architecture.md` §9) for placement problems and re-validate before reporting
or splitting. Missing `architecture.md` §9 accessible-name markup or visible
title on rendered evidence is `ARCH-R-2`.

Render mode: the footer `Layout/render options` line reports the mode
verified from the emitted artifact (`architecture.md` §9 render-mode check),
never the render-policy intent. A policy/artifact/footer mismatch is
`ARCH-R-5`; a script despite a static policy adds a `Dediren tool issues`
entry. When interactive output ships, disclose the `architecture.md` §3
mouse-only and embedding limits to the audience.

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
Dediren runtime: <path|not run>; Validation: source; semantic; projection; metadata; layout; layout validation; SVG; accessible name; visual; OEF; XMI
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed; Export readiness: not requested | OEF ready (<coverage>) | XMI ready (<coverage>) | blocked
Cross-notation links: none | UML elaborates ArchiMate <ids> | broken <ids> | not assessed
Handoff boundary: architecture/design model | companion material required | delegated to <skill>
Diagram kind: <primary>; views: <n>; missing kinds: <list|none>; View groups: <n> source-backed groups | none
Semantic grouping: layout-only groups are not ArchiMate Grouping elements | semantic-boundary semantic_source_id | not assessed
Customization profile: none | local properties | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none
Grouped layout fallback: not needed | used ungrouped fallback | not run
Layout/render options: layout_preferences none | <view: knobs>; render static SVG (verified script-free) | interactive <svg|html|both> (verified; mouse-only limits disclosed); raster png no | yes
Implementation readiness: sufficient | partial | insufficient | not assessed
Build readiness disclosure: <n> of 7 concern classes present; absent <list|none> | not build mode
Finding split: <n> architecture-documentation findings; <n> other source material findings
ArchiMate equivalence: direct | partial | metadata/companion | none | not assessed
Findings: <n> blocking ARCH-*
Dediren tool issues: <none|issues; upstream or blocked report>
```
