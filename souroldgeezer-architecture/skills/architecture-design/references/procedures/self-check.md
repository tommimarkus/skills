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

## Command templates

Run from the target repository root and replace `<pkg>` with
`docs/architecture/<feature>.dediren`. Render metadata uses
`dediren project --target render-metadata` with the selected project file and
view id.

```bash
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate --plugin generic-graph --profile archimate <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren project <pkg>/project.json --view <view-id>
souroldgeezer-architecture/tools/dediren-linux/bin/dediren project <pkg>/project.json --view <view-id> --target render-metadata
souroldgeezer-architecture/tools/dediren-linux/bin/dediren layout <pkg>/project.json --view <view-id> --plugin elk-layout
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate-layout <pkg>/generated/layout/<view-id>.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren render <pkg>/project.json --view <view-id>
souroldgeezer-architecture/tools/dediren-linux/bin/dediren export <pkg>/project.json
```

Use the macOS bundle path when `tools/dediren-macos/` is the selected bundle.
Omit export unless OEF was requested.
