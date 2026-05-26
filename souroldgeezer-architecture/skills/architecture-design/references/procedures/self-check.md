# Dediren Self-Check

Before runtime claims, resolve the pinned Dediren GitHub™ release:

```bash
DEDIREN="$(
  souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh --ensure
)"
```

The resolver caches release bundles under `.cache/dediren/releases/`; do not
commit that cache. If the resolver cannot download or select a supported
platform, disclose `not run (missing dediren release bundle)` and cap at
`source-valid` unless Lookup only.

The selected release bundle is an imported upstream Dediren artifact. Do not
patch cached release files or future packaged bundles. For defects, report
`Dediren tool issues` with version, command, input summary, envelope/error,
expected behavior, and repro evidence.

For JSON authoring, repair, and command handoff details, read the selected
release bundle guide before loading schemas:
`souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh --agent-guide`.
It is the fast contract for Minimal Source JSON, Artifact Authoring Map, Command
Handoff Rules, and Repair Map.

Use `generic-graph`, `elk-layout`, `svg-render`. For generated notation SVG
metadata, set `plugins.generic-graph.semantic_profile` to `archimate` or `uml`;
add `archimate-oef` only when OEF export is requested and `uml-xmi` only when
UML/XMI export is requested. Plain `validate` proves schema only; `source-valid`
requires `validate` plus `validate --plugin generic-graph --profile archimate`
for ArchiMate or `validate --plugin generic-graph --profile uml` for UML.
When running OEF or XMI export, follow the selected release guide's schema-cache
instructions such as setting `DEDIREN_SCHEMA_CACHE_DIR` or providing the
offline schema path required by that export plugin.
Command order: `validate`; semantic validate; `project`; `layout`;
`validate-layout`; `render`; optional export. The release-resolved Dediren runtime allows
parallel per-view layout; rerun parallel-only failures serially before
`ARCH-L-1`.

## Command templates

Run from the target repository root and replace `<pkg>` with
`docs/architecture/<feature>.dediren`. Render metadata uses
`dediren project --target render-metadata` with the selected model file and
view id. The CLI emits JSON envelopes to stdout; when materializing
`generated/`, write each envelope `data` payload to the matching path declared
by `project.json`.

```bash
"$DEDIREN" validate --input <pkg>/model.json
"$DEDIREN" validate --plugin generic-graph --profile archimate --input <pkg>/model.json
"$DEDIREN" validate --plugin generic-graph --profile uml --input <pkg>/model.json
"$DEDIREN" project --target layout-request --plugin generic-graph --view <view-id> --input <pkg>/model.json
"$DEDIREN" project --target render-metadata --plugin generic-graph --view <view-id> --input <pkg>/model.json
"$DEDIREN" layout --plugin elk-layout --input <layout-request.json>
"$DEDIREN" validate-layout --input <layout-result.json>
"$DEDIREN" render --plugin svg-render --policy <pkg>/render-policy.json --metadata <render-metadata.json> --input <layout-result.json>
"$DEDIREN" export --plugin archimate-oef --policy <pkg>/export-policy.json --source <pkg>/model.json --layout <layout-result.json>
"$DEDIREN" export --plugin uml-xmi --policy <pkg>/export-policy.json --source <pkg>/model.json --layout <layout-result.json>
```

Omit export unless OEF or XMI was requested.
