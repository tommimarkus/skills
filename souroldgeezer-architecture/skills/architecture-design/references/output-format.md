Use after mode selection. Always disclose runtime evidence, quality, export
readiness, findings, and the footer.

## Build

```
Package: docs/architecture/<feature>.dediren/
Mode: build
Quality level: <quality>
Export readiness: <export-readiness>
Evidence:
  Dediren runtime: <path> | not run (missing dediren bundle)
  Views: <n> actual; missing diagram kinds: <list|none>
  Source validation: passed | failed | not run
  SVG render: passed | failed | not run
  OEF export: not requested | passed | failed | blocked
  Findings: <n> blocking ARCH-* findings
```

## Extract

```
Package: docs/architecture/<feature>.dediren/
Mode: extract
Quality level: <quality>
Export readiness: <export-readiness>
Sources read: <files>
Layers lifted: Application <n>, Technology <n>, Implementation & Migration <n>, Business Process candidates <n>
View groups: <n> source-backed groups; unsupported grouping candidates <n>|none
Architect-owned layers: Business-other, Motivation, Strategy, Physical
Evidence: runtime <path|missing>; validation <state>; views <n>; render <state>; drift <summary>; findings <n>
```

## Review

Lead with findings:

```
[ARCH-M-1] <one-line finding>
  evidence: <file, id, command, render artifact, or supplied downstream evidence>
  severity: block | warn | info
  action: <specific correction>
```

Then report quality, export readiness, change classification, package path,
runtime, validation, layout validation, SVG render, and optional OEF export.
Each finding uses one `ARCH-*` code; do not claim `review-ready` with a block.

## Lookup

Answer in two to four lines and include the footer. Do not mutate the package.

## Footer

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Package: docs/architecture/<feature>.dediren/
Dediren runtime: <linux path> | <macos path> | not run (missing dediren bundle)
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed
Export readiness: not requested | export-ready | blocked (missing export-policy.json)
Diagram kind: <primary kind>
Views: <n> actual; missing diagram kinds: <list|none>
View groups: <n> source-backed groups | none | not assessed
Validation: source <state>; projection <state>; layout <state>; layout validation <state>; SVG <state>; OEF <state>
Runtime-verified drift: <n findings|not run>
Findings: <n> blocking ARCH-* findings
Change classification: semantic model <yes|no>; view/layout <yes|no>; render metadata/policy <yes|no>; export policy <yes|no>; docs only <yes|no>
```
