# Dediren Self-Check

Before runtime claims, use the first executable found:
`souroldgeezer-architecture/tools/dediren-linux/bin/dediren`, then
`souroldgeezer-architecture/tools/dediren-macos/bin/dediren`. If missing,
disclose `not run (missing dediren bundle)` and cap at `source-valid` unless Lookup only.

The selected bundle is an imported upstream Dediren artifact. Do not patch
`tools/dediren-linux/` or future bundles. For defects, report
`Dediren tool issues` with version, command, input summary, envelope/error,
expected behavior, and repro evidence.

Use `generic-graph`, `elk-layout`, `svg-render`. For generated ArchiMate SVG
metadata, set `plugins.generic-graph.semantic_profile` to `archimate`; add
`archimate-oef` only when OEF export is requested. Plain `validate` proves
schema only; `source-valid` requires `validate` plus
`validate --plugin generic-graph --profile archimate`. Command order:
`validate`; semantic validate; `project`; `layout`; `validate-layout`; `render`;
optional export. Dediren 0.9.0 allows parallel per-view layout; rerun
parallel-only failures serially before `ARCH-L-1`.
