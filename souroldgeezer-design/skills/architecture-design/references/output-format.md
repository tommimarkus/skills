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
  Per-view readiness:
    | View id                       | Viewpoint                       | Readiness        | Authority                  | Top blockers          |
    |---|---|---|---|---|
    | <id>                          | <reference §9 kind>             | model-valid | diagram-readable | review-ready | lifted-from-source | forward-only-or-inferred | architect-approved | stakeholder-validated | <comma-separated AD-* codes, or "none"> |
  Artifact quality:      model-valid | diagram-readable | review-ready  (worst-view minimum; model-level blockers: <none | comma-separated AD-* codes>)
  Runtime correspondence: <n>/<n> [runtime verified — or source-aligned, IaC verification required]
  Layout backend report:
    | View id | Viewpoint | Intent | Geometry path | Request validation | Result validation | OEF materialization | PNG validation | Provenance artifact | Notes |
    |---|---|---|---|---|---|---|---|---|---|
    | view-application-cooperation | Application Cooperation | generated-layout-recreate | layout-elk | passed | passed | materialized | not requested | layout-provenance emitted | eligible generated view |

Deviations from defaults (if any): <list with reason>
```

The per-view readiness matrix is required when the artifact contains more than one materialized view. Per-view classification rules and the worst-view rollup are defined in [procedures/professional-readiness.md](procedures/professional-readiness.md) §Quality verdict. Authority defaults to `lifted-from-source` when every element resolves to a current source and no `LIFT-CANDIDATE` is unconfirmed; otherwise `forward-only-or-inferred`. Architect overrides via the view-level `propid-authority` property (reference §6.4b).

### Extract mode

```
<OEF XML document with FORWARD-ONLY comment blocks around fully-stubbed element sections, and LIFT-CANDIDATE XML comments preceding each Business Process / Event / Interaction emitted from backend workflow sources>

Extraction summary:
  Layers lifted:          Application (<n>), Technology (<n>), Implementation & Migration (<n>), Business-Process (<n_lift_candidates>)
  Layers stubbed (forward-only): Motivation, Strategy; Business-other (Actor / Role / Collaboration / Object / Contract / Product / Service / Function)
  Sources read:           <list of files, including Durable Functions orchestrators and Logic Apps workflows when present>
  LIFT-CANDIDATE confidence: <n_high> high / <n_medium> medium / <n_low> low
  Elements preserved from existing diagram: <n>/<n>
  Per-view readiness:
    | View id                       | Viewpoint                       | Readiness        | Authority                  | Top blockers          |
    |---|---|---|---|---|
    | <id>                          | <reference §9 kind>             | model-valid | diagram-readable | review-ready | lifted-from-source | forward-only-or-inferred | architect-approved | stakeholder-validated | <comma-separated AD-* codes, or "none"> |
  Artifact quality:       model-valid | diagram-readable | review-ready  (worst-view minimum; model-level blockers: <none | comma-separated AD-* codes>)
  Drift vs existing diagram: <added / removed / changed counts, or n/a if greenfield>
  Layout backend report:
    | View id | Viewpoint | Intent | Geometry path | Request validation | Result validation | OEF materialization | PNG validation | Provenance artifact | Notes |
    |---|---|---|---|---|---|---|---|---|---|
    | view-technology-usage | Technology Usage | generated-layout-recreate | layout-elk | passed | passed | materialized | validate-png passed | layout-provenance emitted | eligible generated view; PNG validation followed render only |
```

### Review mode

Lead with the per-view readiness matrix (required for multi-view artifacts; single-row matrix is acceptable for single-view files), then the artifact rollup, then change classification:

```
Per-view readiness:
  | View id                       | Viewpoint                       | Readiness        | Top blockers          |
  |---|---|---|---|
  | <id>                          | <reference §9 kind>             | model-valid | diagram-readable | review-ready | <comma-separated AD-* codes, or "none"> |

Professional readiness: model-valid | diagram-readable | review-ready  (worst-view minimum; model-level blockers: <none | comma-separated AD-* codes>)
Top artifact blockers: <none | concise list of AD-Q / AD-L / AD-B / AD-* codes>
Change classification: semantic model change yes|no; view geometry change yes|no; documentation/render inventory change yes|no
```

Then emit one per-finding block for each failure, followed by the rollup. All findings cite `AD-*` / `AD-Q*` code + reference §n + ArchiMate® 3.2 §/Appendix when applicable. Each finding includes a `layer:` field so the reader knows how to confirm: `static` (diagram-source inspection), `visual` (render inspection), `runtime` (vs current code/IaC). Only `static` and completed `visual` findings are definitively pass / fail from their evidence; `runtime` findings are "source-aligned, confirmation requires re-running drift detection on current code." The rollup states whether architecture semantics changed.

Cross-view smells (`AD-B-8`, `AD-B-9`, `AD-B-13`, `AD-B-14`, `AD-DR-*`) are listed in the `Top blockers` cell of *every* view they cap, so the architect can pick a single view and see every reason it isn't yet `review-ready` without scanning the per-finding list.

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
Layout intent: preserve-authored | route-repair-only | generated-layout-recreate | global-reflow
Layout backend report: present <n>/<n> views; layout-elk used <n>; route-repair used <n>; global-polish used <n>; deterministic fallback used <n>; viewpoint-policy only <n>; preserved-authored <n>; unavailable/skipped <n>; provenance emitted <n>/<n>
Layout generation vs PNG validation: `layout-elk` / `route-repair` / `global-polish` generate or repair OEF geometry; `validate-png` validates rendered PNGs only
Layers in scope: <comma-separated>
Per-view readiness: <comma-separated `<view-id>=<readiness>:<authority>` triples, or "single-view artifact: see Artifact quality below">
Artifact quality: model-valid | diagram-readable | review-ready | not assessed (worst-view minimum)
Authority distribution: <comma-separated `<authority-level>=<count>` pairs across all views>
AD-Q11 findings: <none | comma-separated view ids with override-vs-content contradictions>
Change classification:
  Semantic model change: yes | no
  View geometry change: yes | no
  Documentation/render inventory change: yes | no
  Notes: <relationship ids hidden from specific views, committed render/docs artifacts updated, or "none">
Self-check (skill tooling):
  Reference files:        present <n>/<n> | degraded (<missing path list>)
  Procedures:             present <n>/<n> | degraded (<missing path list>)
  Scripts:                present <n>/<n>, executable <m>/<n> | degraded (<missing or non-executable path list>)
  Weak dependencies:      archi-render.sh: runnable | not run (<blocker>)
Self-check (run): pass | <n failures> | n/a
Visual render inspection: not run | passed <n>/<n> views | failed <n>/<n> views
Render gate: not applicable (visual quality not requested) | passed (render ran on changed views) | engaged (visual quality requested but render not run; <n> changed views capped at model-valid)
Render artifacts: not requested | not run (<blocker>) | <output directory and PNG count>
Source geometry gate: not run | passed | failed <n> findings
Project assimilation:
  <block per the Project assimilation section above; canonical example below>
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

### Project assimilation block — canonical example

```
Project assimilation:
  Existing model: docs/architecture/checkout.oef.xml (last modified 2026-04-12)
    elements preserved: 11/11, identifiers preserved: 11/11, view layouts preserved: 3/3
  Layers extracted (Extract mode):
    Application:  from Orders.Api.csproj, Orders.Core.csproj, Blazor.Client.csproj — 3 components
    Technology:   from infra/main.bicep — 1 Function App + 1 Cosmos account + 1 Storage account + 1 Key Vault + 1 Managed Identity
    Impl & Migr:  from .github/workflows/deploy.yml — 1 Work Package, 3 Plateaus (dev/staging/prod)
  Forward-only layers: Business, Motivation, Strategy — typed stubs emitted; architect fills in
  Render contracts detected:
    committed renders: docs/architecture/checkout.png (last modified 2026-04-12), docs/architecture/checkout-tech.png (last modified 2026-04-12)
    gallery sections: docs/architecture/README.md §Checkout (line 14) — table row referencing checkout.oef.xml
    render commands:  Makefile target `render-architecture` invokes archi-render.sh
    note: OEF changed in this run; 2 committed renders / 1 gallery section may need refresh — architect decides whether to update them in this run
  Drift vs existing diagram: 1 element added (Cosmos account), 1 removed (Table Storage account)
```
