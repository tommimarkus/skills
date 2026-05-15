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

Required plugins: `generic-graph`, `elk-layout`, `svg-render`; add
`archimate-oef` only for export. Plain `validate` proves schema only.
`source-valid` requires `validate` plus
`validate --plugin generic-graph --profile archimate`. Projection, render,
layout, and export evidence remain separate gates.

When `project.json` declares `metadata`, generate render metadata per view
before rendering. Run `layout --plugin elk-layout` serially; parallel ELK layout
can produce invalid JSON envelopes even when the same inputs pass serially.

Command order: `validate`; semantic validate; `project` projection/render
metadata; serial `layout`; `validate-layout`; `render --plugin svg-render`;
optional `export --plugin archimate-oef`. Error envelopes block that quality
level.
