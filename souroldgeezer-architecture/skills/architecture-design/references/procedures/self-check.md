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

Runtime commands use `generic-graph`, `elk-layout`, and `svg-render`. For
ArchiMate SVG policy with generated per-view render metadata, set
`plugins.generic-graph.semantic_profile` to `archimate`; the bundled dediren
0.9.0 runtime no longer requires `archimate-oef` for render metadata. Add
`archimate-oef` only when OEF export is requested. Plain `validate` proves
schema only.
`source-valid` requires `validate` plus
`validate --plugin generic-graph --profile archimate`. Projection, render,
layout, and export evidence remain separate gates.

When `project.json` declares `metadata`, generate render metadata per view
before rendering. With bundled dediren 0.9.0, per-view
`layout --plugin elk-layout` commands may run in parallel. If a parallel batch
returns an error envelope or invalid output, rerun the exact failing input
serially before reporting `ARCH-L-1`.

Command order: `validate`; semantic validate; `project` projection/render
metadata; `layout`; `validate-layout`; `render --plugin svg-render`;
optional `export --plugin archimate-oef`. Error envelopes block that quality
level.
