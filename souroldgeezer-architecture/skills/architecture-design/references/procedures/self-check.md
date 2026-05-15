# Dediren Self-Check

Before runtime claims, select the first existing executable:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

If neither exists, disclose `not run (missing dediren bundle)` and cap quality at
`source-valid` unless Lookup only. Record version and bundle JSON.

The selected bundle is an imported upstream Dediren artifact. Do not patch files
under `tools/dediren-linux/` or future bundles for tool behavior. For
runtime/schema/plugin/helper/render/layout/export defects, report `Dediren tool
issues` with version, command, input summary, envelope/error, expected behavior,
and repro evidence. Keep issue-filing mechanics agent-local.

Required render-path plugins: `generic-graph`, `elk-layout`, `svg-render`.
For ArchiMate SVG policy with generated per-view render metadata, also keep
`archimate-oef` in `model.json.required_plugins` with the bundled dediren 0.8.4
runtime, even when export is not requested. Without it, generated metadata can
use `semantic_profile: "generic-graph"` and render can fail with
`DEDIREN_RENDER_METADATA_PROFILE_MISMATCH`; tracked upstream as
`tommimarkus/dediren#1`. Plain `validate` proves schema only.
`source-valid` requires `validate` plus
`validate --plugin generic-graph --profile archimate`. Projection, render,
layout, and export evidence remain separate gates.

When `project.json` declares `metadata`, generate render metadata per view
before rendering. With bundled dediren 0.8.4, per-view
`layout --plugin elk-layout` commands may run in parallel. If a parallel batch
returns an error envelope or invalid output, rerun the exact failing input
serially before reporting `ARCH-L-1`.

Command order: `validate`; semantic validate; `project` projection/render
metadata; `layout`; `validate-layout`; `render --plugin svg-render`;
optional `export --plugin archimate-oef`. Error envelopes block that quality
level.
