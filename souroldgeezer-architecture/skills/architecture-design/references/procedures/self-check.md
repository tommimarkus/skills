# Dediren Self-Check

Before runtime claims, use the first executable found:
`souroldgeezer-architecture/tools/dediren-linux/bin/dediren`, then
`souroldgeezer-architecture/tools/dediren-macos/bin/dediren`. If missing,
disclose `not run (missing dediren bundle)` and cap at `source-valid` unless Lookup only.

The selected bundle is an imported upstream Dediren artifact. Do not patch
`tools/dediren-linux/` or future bundles. For defects, report
`Dediren tool issues` with version, command, input summary, envelope/error,
expected behavior, and repro evidence.

For JSON authoring, repair, and command handoff details, read the selected
bundle guide before loading schemas:
`souroldgeezer-architecture/tools/dediren-linux/docs/agent-usage.md`. It is the
fast contract for Minimal Source JSON, Artifact Authoring Map, Command Handoff
Rules, and Repair Map.

Use `generic-graph`, `elk-layout`, `svg-render`. For generated ArchiMate SVG
metadata, set `plugins.generic-graph.semantic_profile` to `archimate`; add
`archimate-oef` only when OEF export is requested. Plain `validate` proves
schema only; `source-valid` requires `validate` plus
`validate --plugin generic-graph --profile archimate`. Command order:
`validate`; semantic validate; `project`; `layout`; `validate-layout`; `render`;
optional export. The bundled Dediren runtime allows parallel per-view layout; rerun
parallel-only failures serially before `ARCH-L-1`.

## Command templates

Run from the target repository root and replace `<pkg>` with
`docs/architecture/<feature>.dediren`. Render metadata uses
`dediren project --target render-metadata` with the selected model file and
view id. The CLI emits JSON envelopes to stdout; when materializing
`generated/`, write each envelope `data` payload to the matching path declared
by `project.json`.

```bash
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate --input <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate --plugin generic-graph --profile archimate --input <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren project --target layout-request --plugin generic-graph --view <view-id> --input <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren project --target render-metadata --plugin generic-graph --view <view-id> --input <pkg>/model.json
souroldgeezer-architecture/tools/dediren-linux/bin/dediren layout --plugin elk-layout --input <layout-request.json>
souroldgeezer-architecture/tools/dediren-linux/bin/dediren validate-layout --input <layout-result.json>
souroldgeezer-architecture/tools/dediren-linux/bin/dediren render --plugin svg-render --policy <pkg>/render-policy.json --metadata <render-metadata.json> --input <layout-result.json>
souroldgeezer-architecture/tools/dediren-linux/bin/dediren export --plugin archimate-oef --policy <pkg>/export-policy.json --source <pkg>/model.json --layout <layout-result.json>
```

Use the macOS bundle path when `tools/dediren-macos/` is the selected bundle.
Omit export unless OEF was requested.
