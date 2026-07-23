Return evidence, notation, cross-notation links, quality, export readiness,
findings, executive summary, footer. Build/Extract: package state, groups,
blockers. Build also
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

Evidence: disclose which Dediren lane ran — the bundled MCP server or the internal
CLI fallback — and its runtime version. Runtime semantics and the notation-specific
`source-valid` validation tools (`dediren_validate` with `profile`) are defined in
`architecture.md` §9. When the read-only evidence tools were run, disclose only
what actually ran: `dediren_verify` stale results as `ARCH-R-2` / `ARCH-E-4` on the
relevant finding, its freshness on the `Gallery:` line alongside `dediren_status`
and `build-gallery.py --check`, and `dediren_diff` / `dediren_query` facts inline
where they support a finding or answer (`architecture.md` §9).

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
`.diagnostics[]` — a partial export is still partial evidence. A whole-model
interchange document (`model.oef.xml` / `model.uml.xml`, `architecture.md` §10) is
a separate artifact, complete across the built views with no omission diagnostic;
disclose it distinctly from the per-view coverage qualifier. Its `model.uml.xml`
UMLDI diagram content is provisional (classifier-diagram views only), so it does
not upgrade a per-view `XMI ready (classes only)` claim.

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

Cross-package: when the `architecture.md` §15 consistency leg runs, report
identity conflicts (`ARCH-X-5`) and fragmentation candidates or rollup gaps
(`ARCH-X-6`) with the package set and shared identity or id; the footer
`Cross-package identity` line carries the rollup.

Visual readiness: layout-valid is not visually clean. Emit `ARCH-L-3`,
`ARCH-R-3`, or `ARCH-Q-2` for dense, hub fanout, label-obscured,
label-dissociated (`architecture.md` §7 label-to-own-edge check),
route-congested, group-imbalanced, or mixed concerns. Tune `layout_preferences`
(`architecture.md` §9) for placement problems and re-validate before reporting
or splitting. Missing `architecture.md` §9 accessible-name markup or visible
title on rendered evidence is `ARCH-R-2`.

Render mode: renders are static SVG. The footer `Layout/render options` line
reports the mode verified from the emitted artifact (`architecture.md` §9
render-mode check), never the render-policy intent. A `<script>` in the
artifact, or a footer that misreports the artifact, is `ARCH-R-5`; a script
also adds a `Dediren tool issues` entry (the runtime retired interactive SVG,
so a script is an upstream defect).

Gallery: when a run (re)generates SVG output, the package-level shareable
`gallery.html` is rebuilt (`references/gallery.md`) and its state reported on the
footer `Gallery:` line. It is an outer viewer over the static SVGs and never
bears on the per-view render-mode check. A committed gallery that has drifted
from its SVGs (detected via `build-gallery.py --check`) is an `ARCH-R-2`
render-evidence finding.

Source-weighted choices: `<n>`; low-confidence: `<n>`; architect-owned: `<n>`.
Use `Notable choices` only for non-obvious or challenged decisions:

```text
Notable choices:
- <source fact> -> <chosen concept/relation/view>; rejected <alternative>; evidence <source-backed|candidate-from-source|architect-owned|weak-evidence|overlay-only>
```

## Executive Summary

Build, Extract, and Review output carries a required executive summary
immediately above the Footer; Lookup (bounded brief/footer answers) is exempt.
Write it for a non-technical sponsor deciding what to approve, fund, or
escalate: plain words only — no `ARCH-*` codes, quality-level tokens, file
paths, or notation/dediren jargon. Those stay in the Footer.

```text
Executive summary:
- Subject: <the architecture/feature and what this run did, in plain words>
- Verdict: <one plain-words sentence: is the architecture sound, and can the reader rely on these diagrams?>
- Diagrams: <plain-language gloss of the reached quality level, per the table below>
- Top risks / asks: <up to 3, each naming the decision needed - approve, fund, or escalate | none>
```

The `Diagrams` gloss must match the Footer `Quality level` — never overstate:

| Quality level | Plain-language gloss |
|---|---|
| source-valid | the model's facts are consistent, but the diagrams themselves have not been checked — do not rely on the pictures yet |
| view-readable | diagrams are structurally valid but not yet confirmed legible — treat them as drafts |
| render-ready | diagrams are rendered and checked for legibility — readable, subject to the listed risks |
| review-ready | no blocking issues remain — the diagrams can be relied on for the stated scope and audience |
| not assessed | quality was not evaluated in this run — do not act on the diagrams from this report alone |

Partial export or render coverage, blocking findings, and layout-fallback
regressions that change what the reader may rely on must also surface here as
plain-words risks/asks, not only as footer fields.

## Footer

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Package: docs/architecture/<feature>.dediren/
Notation: archimate | uml | mixed | unsupported
Dediren: MCP server (<version>) | CLI fallback (<version>) | not run (dediren runtime unavailable); Validation: source; semantic; projection; metadata; layout; layout validation; SVG; accessible name; visual; OEF; XMI
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed; Export readiness: not requested | OEF ready (<coverage>) | XMI ready (<coverage>) | blocked
Cross-notation links: none | UML elaborates ArchiMate <ids> | broken <ids> | not assessed
Cross-package identity: single package | consistent | conflicts <n>, candidates <n> | not assessed
Handoff boundary: architecture/design model | companion material required | delegated to <skill>
Diagram kind: <primary>; views: <n>; missing kinds: <list|none>; View groups: <n> source-backed groups | none
Semantic grouping: layout-only groups are not ArchiMate Grouping elements | semantic-boundary semantic_source_id | not assessed
Customization profile: none | local properties | profile/attribute/specialization documented
Unsupported ArchiMate concepts: relationship connectors and junctions unsupported in dediren package source | none
Grouped layout fallback: not needed | used ungrouped fallback | not run
Layout/render options: layout_preferences none | <view: knobs>; render static SVG (verified script-free)
Gallery: built (<n> views) <path> | refreshed | stale (run build-gallery) | not built (<reason>) | not applicable (no render this run)
Implementation readiness: sufficient | partial | insufficient | not assessed
Build readiness disclosure: <n> of 7 concern classes present; absent <list|none> | not build mode
Finding split: <n> architecture-documentation findings; <n> other source material findings
ArchiMate equivalence: direct | partial | metadata/companion | none | not assessed
Findings: <n> blocking ARCH-*
Dediren tool issues: <none|issues; upstream or blocked report>
```
