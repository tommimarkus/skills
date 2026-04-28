Use this reference after `SKILL.md` selects the mode. Copy only the relevant
skeleton and keep evidence, quality level, change classification, verification
state, and footer disclosures explicit.

## Output format

### Build mode

```
<OEF XML document>

Self-check:
  Well-formedness:       <n>/<n>  [static verified]
  Layer discipline:      <n>/<n>  [static verified]
  Appendix B relations:  <n>/<n>  [static verified]
  Artifact quality:      model-valid | diagram-readable | review-ready
  Runtime correspondence: <n>/<n> [runtime verified — or source-aligned, IaC verification required]

Deviations from defaults (if any): <list with reason>
```

### Extract mode

```
<OEF XML document with FORWARD-ONLY comment blocks around fully-stubbed element sections, and LIFT-CANDIDATE XML comments preceding each Business Process / Event / Interaction emitted from backend workflow sources>

Extraction summary:
  Layers lifted:          Application (<n>), Technology (<n>), Implementation & Migration (<n>), Business-Process (<n_lift_candidates>)
  Layers stubbed (forward-only): Motivation, Strategy; Business-other (Actor / Role / Collaboration / Object / Contract / Product / Service / Function)
  Sources read:           <list of files, including Durable Functions orchestrators and Logic Apps workflows when present>
  LIFT-CANDIDATE confidence: <n_high> high / <n_medium> medium / <n_low> low
  Elements preserved from existing diagram: <n>/<n>
  Artifact quality:       model-valid | diagram-readable | review-ready
  Drift vs existing diagram: <added / removed / changed counts, or n/a if greenfield>
```

### Review mode

Lead with:

```
Professional readiness: model-valid | diagram-readable | review-ready
Top artifact blockers: <none | concise list of AD-Q / AD-L / AD-B / AD-* codes>
Change classification: semantic model change yes|no; view geometry change yes|no; documentation/render inventory change yes|no
```

Then emit one per-finding block for each failure, followed by the rollup. All findings cite `AD-*` / `AD-Q*` code + reference §n + ArchiMate® 3.2 §/Appendix when applicable. Each finding includes a `layer:` field so the reader knows how to confirm: `static` (diagram-source inspection), `visual` (render inspection), `runtime` (vs current code/IaC). Only `static` and completed `visual` findings are definitively pass / fail from their evidence; `runtime` findings are "source-aligned, confirmation requires re-running drift detection on current code." The rollup states whether architecture semantics changed.

### Lookup mode

Two to four lines of prose + one footer line.

### Footer (all modes)

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-design/docs/architecture-reference/architecture.md
Canonical path: docs/architecture/<feature>.oef.xml
Diagram kind: <reference §9 kind name — primary kind in scope this run>
Diagram kinds present: <M> of 7 (<comma-separated canonical viewpoint names>)
Diagram kinds missing: <comma-separated canonical viewpoint names, or "none">
Layout engine: Sugiyama-v1 [+ <viewpoint> specialisation, when applicable]
Layers in scope: <comma-separated>
Artifact quality: model-valid | diagram-readable | review-ready | not assessed
Change classification:
  Semantic model change: yes | no
  View geometry change: yes | no
  Documentation/render inventory change: yes | no
  Notes: <relationship ids hidden from specific views, committed render/docs artifacts updated, or "none">
Self-check: pass | <n failures> | n/a
Visual render inspection: not run | passed <n>/<n> views | failed <n>/<n> views
Render artifacts: not requested | not run (<blocker>) | <output directory and PNG count>
Source geometry gate: not run | passed | failed <n> findings
Project assimilation:
  <block per the Project assimilation section above>
Forward-only layers stubbed: <list, or "none">
Process-view emission:
  Top-level Business Processes:    <n>
  Sub-processes (Composition):     <m>
  §9.7 cooperation views emitted:  <0 or 1>
  §9.3 service-realization views:  <distinct story views emitted> (<processes covered> processes; <same-story consolidations> consolidations)
  Suppressed by propid-coop-view-exclude:    <comma-separated identifiers, or "none">
  Suppressed by propid-drilldown-exclude:    <comma-separated identifiers, or "none">
  Over-budget views (AD-L4):       <comma-separated view identifiers, or "none">
Runtime-verified drift: <n findings, or "drift detection not run">
```
