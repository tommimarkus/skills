# Dediren Self-Check

Before runtime claims, resolve the pinned Dediren GitHub™ release. Set
`SKILL_DIR` to the architecture-design skill directory — the directory that
contains this skill's `SKILL.md`. In this marketplace repo that is
`souroldgeezer-architecture/skills/architecture-design`; in an installed
plugin it is the `skills/architecture-design/` directory inside the plugin
cache.

```bash
DEDIREN="$("$SKILL_DIR"/references/scripts/dediren-release.sh --ensure)"
```

The resolver caches release bundles under `.cache/dediren/releases/`; do not
commit that cache. The pinned release bundle is Java™-backed; commands that
return or execute the runnable Dediren CLI require Java™ 21 or newer through
`JAVA_HOME`, `JAVACMD`, or `java` on `PATH`. If the resolver cannot download or
select a supported platform, disclose `not run (missing dediren release
bundle)` and cap at `source-valid` unless Lookup only. If Java™ 21+ is missing,
disclose `not run (missing Java 21+ runtime)` for runtime steps.

The selected release bundle is an imported upstream Dediren artifact. Do not
patch cached release files or future packaged bundles; report defects under
`Dediren tool issues` per `architecture.md` §9.

For JSON authoring, repair, and command handoff details, read the selected
release bundle guide before loading schemas:

```bash
"$SKILL_DIR"/references/scripts/dediren-release.sh --agent-guide
```

It is the fast contract for Minimal Source JSON, Artifact Map, Semantic
Profiles, Command Handoff, and Repair Rules.

Use `generic-graph`, `elk-layout`, `render`. For generated notation SVG
metadata, set `plugins.generic-graph.semantic_profile` to `archimate` or `uml`;
add `archimate-oef` only when OEF export is requested and `uml-xmi` only when
UML/XMI export is requested. Plain `validate` proves schema only; `source-valid`
requires `validate` plus `validate --plugin generic-graph --profile archimate`
for ArchiMate or `validate --plugin generic-graph --profile uml` for UML.
When running OEF or XMI export, follow the selected release guide's schema-cache
instructions. Export plugins download validation schemas from a child process
that receives only manifest-listed environment variables, so proxied or
sandboxed environments fail with `DEDIREN_*_SCHEMA_UNAVAILABLE` even when the
agent's own shell has network access: pre-fetch the XSDs and pass absolute
offline paths via `DEDIREN_OEF_SCHEMA_DIR` / `DEDIREN_XMI_SCHEMA_PATH`
(`DEDIREN_SCHEMA_CACHE_DIR` helps only when the child itself can download).
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
"$DEDIREN" render --plugin render --policy <pkg>/render-policy.json --metadata <render-metadata.json> --input <layout-result.json>
"$DEDIREN" export --plugin archimate-oef --policy <pkg>/export-policy.json --source <pkg>/model.json --layout <layout-result.json>
"$DEDIREN" export --plugin uml-xmi --policy <pkg>/export-policy.json --source <pkg>/model.json --layout <layout-result.json>
```

Omit export unless OEF or XMI was requested.

To steer placement, set `layout_preferences` (`mode` / `direction` / `density` /
`wrapping` / `routing`; enums and guidance in `architecture.md` §9) in the
layout-request before `layout`, then re-run `validate-layout`. For navigable
output, set the render policy `interactive` field (§3); static SVG is the
default.

## Envelope handling

Every command emits a JSON envelope on stdout. Check the envelope `status`
before feeding output to the next command — a downstream stage fed an error
envelope fails one stage late with `DEDIREN_COMMAND_INPUT_INVALID`, pointing
diagnosis at the wrong command.

Envelope `status: ok` with empty `diagnostics` is **not** a quality verdict.
`validate-layout` reports its verdict inside the payload: read `data.status`
and the `data.*_count` quality fields. Treat `data.status: "warning"` or any
nonzero non-informational count (`overlap_count`,
`connector_through_node_count`, `invalid_route_count`, and the other §9 gate
counts; `edge_crossing_count` is informational) as a blocking layout finding
(`ARCH-L-*`) to resolve or disclose before claiming render evidence — an
overlap can superimpose two nodes in the rendered SVG while every envelope in
the pipeline says `ok`.

Artifact extraction differs by command and yields silent empty files when
mixed up: `render` returns artifacts in `.data.artifacts[]` (select the entry
whose `artifact_kind` is `svg` and write its `.content`), while `export`
returns a single artifact directly as `.data.content` (with `.data.artifact_kind`
naming the format). After materializing any artifact, verify it is non-empty
before claiming render or export evidence.
