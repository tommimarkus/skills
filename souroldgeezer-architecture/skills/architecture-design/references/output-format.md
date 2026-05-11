Use this reference after `SKILL.md` selects the mode. Copy only the relevant
skeleton and keep runtime evidence, quality level, export readiness, and footer
disclosures explicit.

## Output Format

### Build Mode

```
Architecture package: docs/architecture/orders.dediren/
Mode: build
Quality level: source-valid | view-readable | render-ready | review-ready
Export readiness: not requested | export-ready | export blocked (missing export-policy.json)

Created or updated:
  Source:        model.json, project.json
  Render policy: render-policy.json, render-metadata.json
  Generated:     generated/ ignored; recreated by dediren

Views:
  1 actual view; missing diagram kinds: Capability Map, Migration, Motivation,
  Business Process Cooperation, Service Realization, Technology Usage

Evidence:
  Dediren runtime: souroldgeezer-architecture/tools/dediren-linux/bin/dediren
  Source validation: passed | failed | not run (missing dediren bundle)
  SVG render: passed | failed | not run (dediren render returned error envelope)
  Optional OEF export: not requested | passed | failed | blocked
  Findings: 0 blocking ARCH-* findings
```

### Extract Mode

```
Architecture package: docs/architecture/<feature>.dediren/
Mode: extract
Quality level: source-valid | view-readable | render-ready | review-ready
Export readiness: not requested | export-ready | export blocked (missing export-policy.json)

Extraction summary:
  Sources read: <files>
  Layers lifted: Application <n>, Technology <n>, Implementation & Migration <n>,
    Business Process candidates <n>
  Architect-owned layers: Business-other, Motivation, Strategy, Physical
  Source evidence: <source refs preserved in model.json, or "none">

Evidence:
  Dediren runtime: <path> | not run (missing dediren-linux bundle)
  Source validation: passed | failed | not run
  Views: <n> actual views; missing diagram kinds: <list or "none">
  SVG render: passed | failed | not run
  Drift against existing package: <added / removed / changed counts, or n/a>
  Findings: <n> blocking ARCH-* findings
```

### Review Mode

Lead with findings, then the rollup:

```
Findings:
  [ARCH-M-1] <one-line finding>
    evidence: <file, node id, edge id, command, or render artifact>
    severity: block | warn | info
    action: <specific correction>

Readiness:
  Quality level: source-valid | view-readable | render-ready | review-ready
  Export readiness: not requested | export-ready | export blocked (missing export-policy.json)
  Change classification: semantic model yes|no; view membership or layout policy yes|no; render policy or metadata yes|no; export policy yes|no

Evidence:
  Architecture package: docs/architecture/<feature>.dediren/
  Dediren runtime: <path> | not run (missing dediren bundle)
  Source validation: passed | failed | not run
  Layout validation: passed | failed | not run
  SVG render: passed | failed | not run
  Optional OEF export: not requested | passed | failed | blocked
```

Every finding cites an `ARCH-*` code from `smell-catalog.md`. Use one severity
per finding. Do not claim `review-ready` while any blocking finding remains.

### Lookup Mode

Two to four lines of prose plus the footer. Do not mutate the package.

### Footer (All Modes)

```
Mode: build | extract | review | lookup
Reference: souroldgeezer-architecture/docs/architecture-reference/architecture.md
Architecture package: docs/architecture/<feature>.dediren/
Dediren runtime: souroldgeezer-architecture/tools/dediren-linux/bin/dediren | souroldgeezer-architecture/tools/dediren-macos/bin/dediren | not run (missing dediren bundle)
Quality level: source-valid | view-readable | render-ready | review-ready | not assessed
Export readiness: not requested | export-ready | export blocked (missing export-policy.json)
Diagram kind: <primary kind>
Views: <n> actual views; missing diagram kinds: <comma-separated supported kinds, or "none">
Source validation: passed | failed <n> diagnostics | not run
Projection: passed | failed | not run
Layout: passed | failed | not run
Layout validation: passed | failed | not run
SVG render: passed | failed | not run
Optional OEF export: not requested | passed | failed | blocked
Runtime-verified drift: <n findings, or "drift detection not run">
Findings: <n> blocking ARCH-* findings
Change classification:
  Semantic model change: yes | no
  View membership or layout policy change: yes | no
  Render policy or metadata change: yes | no
  Export policy change: yes | no
  Documentation only: yes | no
```

### Quality Levels

- `source-valid`: package source validates and relationships are coherent.
- `view-readable`: each listed view can be projected and has validated layout.
- `render-ready`: SVG render ran for changed views and the output is
  nonblank, framed, and carries dediren node/edge markers.
- `review-ready`: render-ready plus no blocking `ARCH-*` findings for the
  audience and diagram kind.

The artifact rollup is the weakest applicable level across actual views.
