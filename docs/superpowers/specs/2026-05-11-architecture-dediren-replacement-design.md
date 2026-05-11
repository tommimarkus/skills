# architecture-design dediren replacement design

Date: 2026-05-11

## Summary

Replace the `architecture-design` `arch-layout` and Architecture IR runtime
with a dediren-native architecture package model. This is a backwards-
incompatible `souroldgeezer-architecture` release and should ship as version
`1.0.0`.

The new canonical architecture artifact is a dediren package directory:

```text
docs/architecture/<feature>.dediren/
  model.json
  project.json
  render-policy.json
  export-policy.json
  render-metadata.json
  generated/
```

`generated/` is ignored by default. It may contain layout JSON, SVG renders,
optional OEF exports, and run reports. Package source and package-owned
policies are committed.

## Decisions

### Canonical Source

Use dediren source as the canonical agent-editable architecture model. Do not
keep Architecture IR YAML as a first-class authoring layer.

OEF becomes an optional compatibility export, not the source of truth. Existing
OEF files can be removed and recreated after the dediren replacement is in
place.

### Package Shape

Each feature architecture model lives in `docs/architecture/<feature>.dediren/`.

`project.json` is owned by `architecture-design`, not by dediren core. It is a
thin orchestration manifest that lists only actual views and points to the
model, policies, plugin choices, and generated output paths.

Example shape:

```json
{
  "schema": "souroldgeezer.architecture.dediren.project.v1",
  "feature": "orders",
  "model": "model.json",
  "views": [
    {
      "id": "view-application-cooperation",
      "title": "Orders - Application Cooperation",
      "projection": {
        "plugin": "generic-graph",
        "target": "layout-request"
      },
      "layout": {
        "plugin": "elk-layout",
        "output": "generated/layout/view-application-cooperation.json"
      },
      "render": {
        "plugin": "svg-render",
        "policy": "render-policy.json",
        "metadata": "render-metadata.json",
        "output": "generated/svg/view-application-cooperation.svg"
      }
    }
  ],
  "export": {
    "plugin": "archimate-oef",
    "policy": "export-policy.json",
    "output": "generated/export/orders.oef.xml"
  }
}
```

`project.json.views[]` contains only views that exist. Missing diagram kinds
are reported by the skill when relevant; they are not represented as empty
placeholder views.

Policies are package-owned. Real architecture packages do not depend on
runtime fixture defaults from `tools/dediren-<platform>/fixtures/`.

### Runtime Layout

Use the bundled dediren tool directly. Do not add a wrapper unless repeated
path mistakes or platform detection problems prove that one is needed.

Initial runtime:

```text
souroldgeezer-architecture/tools/dediren-linux/bin/dediren
```

Expected later runtime:

```text
souroldgeezer-architecture/tools/dediren-macos/bin/dediren
```

The skill chooses the platform bundle from the host platform. Missing platform
bundles produce degraded-mode output with the exact missing path. There is no
fallback to `arch-layout`.

### Workflow Modes

Keep the existing four modes and change their artifact contract.

- Build: architect intent to `docs/architecture/<feature>.dediren/`; validate
  source, project views, layout, render SVG by default, and export OEF only when
  requested.
- Extract: code, IaC, and workflows to a dediren package; preserve
  source-grounded lift evidence in the model; validate, layout, render SVG by
  default, and export OEF only when requested.
- Review: inspect dediren package source, view coverage, layout diagnostics,
  SVG render, modeling quality, and source drift. Existing OEF output is
  derived export evidence only.
- Lookup: answer notation, model, process, and reverse-lookup questions from
  the dediren package plus repo source context.

The old `arch-layout` flow is removed: no Architecture IR lifecycle, no
`arch-layout.sh`, no Java layout runtime, no OEF materialization path, and no
PNG gate as a primary requirement.

### Validation And Readiness

Dediren is the quality authority. The main validation path is:

```text
model/project package -> dediren validate/project/layout/validate-layout/render -> semantic SVG checks
```

Readiness levels:

- `source-valid`: dediren package source validates and package files are
  coherent.
- `view-readable`: intended views project/layout successfully and pass dediren
  layout validation.
- `render-ready`: intended views render to SVG; SVG is nonblank, has expected
  nodes/edges, sane bounds/viewBox, and passes semantic SVG checks.
- `review-ready`: render-ready plus source drift/extraction checks,
  professional modeling checks, and no blocking `ARCH-*` findings.
- `export-ready`: optional badge when OEF or another export was requested,
  generated, and passed export/interop checks.

`export-ready` is orthogonal. A package can be `review-ready` without OEF
export.

### Finding Codes

Retire the old `AD-*`, `AD-Q*`, `AD-L*`, `AD-B-*`, and `AD-DR-*` output codes
from new `architecture-design` outputs.

Use a cleaner `ARCH-*` taxonomy:

- `ARCH-M-*`: model semantics
- `ARCH-V-*`: view/projection coverage and readability
- `ARCH-L-*`: dediren layout diagnostics
- `ARCH-R-*`: SVG/render quality
- `ARCH-X-*`: extraction/drift
- `ARCH-E-*`: export/interop
- `ARCH-Q-*`: overall readiness/professional quality

### Generated Output Policy

Commit canonical source and package-owned policies. Ignore routine generated
outputs by default with a repo-level ignore rule for:

```text
docs/architecture/*.dediren/generated/
```

Representative fixture or golden outputs may be committed when they are
intentional test evidence. Routine per-project generated layout, SVG, OEF, and
report files are regenerated on demand.

### Deletion Scope

Delete the old `arch-layout` implementation and support surface:

- `tools/architecture-layout-java/`
- `references/bin/arch-layout.jar`
- `references/scripts/arch-layout.sh`
- `references/scripts/package-arch-layout.sh`
- old layout request, result, and provenance schemas
- Architecture IR YAML fixtures
- old `layout-contract`, `layout-elk`, `route-repair`, `global-polish`,
  `materialize-oef`, `rendered-png`, and render-quality-gate fixture families
- procedure text that only exists to explain the retired runtime

Replace the old fixture strategy with dediren-native examples only. Do not
preserve old arch-layout parity fixtures.

Keep and refactor the architecture reference, mode workflow, lifting rules,
source grounding, professional-quality guidance, and cross-skill drift concepts.

### Cross-Skill Coupling

Change the cross-skill architecture pairing path from:

```text
docs/architecture/<feature>.oef.xml
```

to:

```text
docs/architecture/<feature>.dediren/
```

Sibling skills (`app-design`, `api-design`, and `infra-design`) treat directory
existence as the architecture-pairing signal. They can report validity or
staleness separately, but they do not require successful dediren validation just
to recognize that architecture evidence exists.

### Versioning

Bump `souroldgeezer-architecture` from `0.2.0` to `1.0.0` in the same commit as
the refactor.

Update all synchronized public surfaces:

- `souroldgeezer-architecture/.claude-plugin/plugin.json`
- `souroldgeezer-architecture/.codex-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `README.md`
- `CLAUDE.md`
- matching Claude agent and Codex metadata/descriptions

Descriptions must remove Architecture IR, Java `arch-layout`, route repair,
global polish, and PNG validation as primary shipped features. Replace them
with dediren package, SVG-first render, optional OEF export, platform-aware
bundled runtime, and the new readiness/output contract.

## Non-goals

- No compatibility wrapper for `arch-layout`.
- No migration adapter from Architecture IR YAML to dediren source.
- No requirement to preserve current OEF files.
- No PNG renderer requirement for the initial replacement. PNG may be produced
  later by ImageMagick conversion or by future native dediren rendering.
- No placeholder project entries for missing diagram kinds.

## Implementation Notes

The implementation should be treated as a big-bang v1 refactor. Keeping old
`arch-layout` files in place during the transition would leave stale authority
signals in the repo and make future agents choose the wrong toolchain.

After implementation, verification should include at minimum:

- dediren platform-bundle self-check on the current host
- package schema/path checks for representative dediren fixtures
- dediren validate/project/layout/validate-layout/render smoke tests
- semantic SVG checks against fixture output
- optional OEF export smoke test when export behavior is in scope
- plugin metadata and marketplace synchronization checks
- `scripts/skill-architecture-report.sh` if available
- git diff whitespace checks
