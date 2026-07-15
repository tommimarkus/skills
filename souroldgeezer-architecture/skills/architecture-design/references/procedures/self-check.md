# Dediren Self-Check

Before runtime claims, drive Dediren through the plugin's **bundled MCP server**.
Dediren is an internal engine: the plugin declares it in `plugin.json`
(`mcpServers.dediren`) and Claude Code auto-starts it when the plugin is enabled,
so the user never has to find, install, or version it. Call its tools —
`dediren_validate`, `dediren_build`, `dediren_guide` — never a CLI. `$SKILL_DIR`
is this skill's absolute directory, established in `SKILL.md` from the
`${CLAUDE_SKILL_DIR}` substitution; it locates this skill's own helper scripts
(`dediren-build.py`, `build-gallery.py`, `svg-accessible-name.sh`), not Dediren.

## Server availability

The bundled server downloads the pinned Java™-backed runtime on first use (into
`${CLAUDE_PLUGIN_DATA}`) and needs Java™ 21 or newer on the host — exactly as a
Node- or Python-based plugin MCP server needs its runtime installed. If the
`dediren_*` tools are not present (the server failed to start: no Java™ 21+, or the
bundle could not be downloaded), disclose `not run (dediren MCP server
unavailable)` and cap at `source-valid` — authoring and hand-written source
validation remain available; this is a capability cap, not a hard stop. Do not ask
the user to install or launch Dediren; the plugin owns that.

Every tool path must resolve inside the server's `--root` (the project directory),
and so must every `fragments[]` path inside a source you pass. A path that escapes
it returns a `DEDIREN_MCP_PATH_OUTSIDE_ROOT` error envelope — keep packages and
their fragments under the project root.

## Validate

`source-valid` requires semantic validation, not schema alone. Call
`dediren_validate` with the source path **and** `profile` set to the model's
notation:

- `dediren_validate {source: "<pkg>/model.json", profile: "archimate"}` for ArchiMate.
- `dediren_validate {source: "<pkg>/model.json", profile: "uml"}` for UML.

The tool runs schema validation plus semantic-profile validation and returns the
validation envelope; `dediren_validate` without a `profile` proves schema only. Use
`generic-graph`, `elk-layout`, `render`; set `plugins.generic-graph.semantic_profile`
to `archimate` or `uml` in the source, and add `archimate-oef` only when OEF export
is requested, `uml-xmi` only when XMI export is requested.

## Format guide

Resolving evidence does not require the guide. Defer it until authoring, repairing,
or handing off source JSON is imminent; a resolve-and-validate or review-only check
never needs it. When that point is reached, read the guide through the tool:

```
dediren_guide {}                       # index of topics
dediren_guide {topic: "source-json"}   # start here
```

It is the fast contract for Minimal Source JSON, Artifact Map, Semantic Profiles,
Command Handoff, and Repair Rules. When running OEF or XMI export, follow the
guide's schema-cache instructions. The export engines run in-process and inherit
the server's environment; the plugin points `DEDIREN_SCHEMA_CACHE_DIR` at a writable
`${CLAUDE_PLUGIN_DATA}` directory so the XSD download succeeds. If export still
fails with `DEDIREN_*_SCHEMA_UNAVAILABLE` (offline host), read the diagnostic's
`message`: it names whether to make that cache writable or to pre-fetch the XSDs and
pass absolute offline paths via `DEDIREN_OEF_SCHEMA_DIR` / `DEDIREN_XMI_SCHEMA_PATH`.
`DEDIREN_XMI_SCHEMA_PATH` at the bare `XMI.xsd` validates only the XMI envelope; full
UML-content schema validation needs the driver schema in
[external-validation-handoff](external-validation-handoff.md) required disclosure 4.

## Building a package (default path)

A `dediren_build` call takes a view through every stage — projection, layout, layout
validation, then whichever of the render, OEF, and XMI lanes are enabled — inside
the server, and writes each view's artifacts under its `out` directory as
`<out>/<view-id>/diagram.svg` (plus `oef.xml` / `xmi.xml`), which is *not* where
`project.json` declares them. The skill's bundled helper owns both the planning and
the remapping so you never do path arithmetic by hand:

```bash
"$SKILL_DIR"/references/scripts/dediren-build.py plan <pkg>            # emits the dediren_build calls
"$SKILL_DIR"/references/scripts/dediren-build.py plan <pkg> --views <view-id>
"$SKILL_DIR"/references/scripts/dediren-build.py map  <pkg>            # materialize + summary
"$SKILL_DIR"/references/scripts/dediren-build.py map  <pkg> --json
```

1. Run `plan <pkg>`. It reads `project.json` and prints the JSON list of
   `dediren_build` tool calls the package needs — one per (model, render-policy)
   render group, and one **single-view** call per export (an OEF/XMI policy's
   identity fields apply per invocation, so each export runs one view at a time).
   Every call writes into one staging dir, `<pkg>/.dediren-build`, so views never
   collide.
2. Make each planned `dediren_build` call with the bundled MCP tool, passing its
   `arguments` verbatim (`source`, `out`, `views`, and the `render_policy` /
   `oef_policy` / `xmi_policy` / `emit` keys the plan set).
3. Run `map <pkg>`. It moves each declared artifact from staging to the
   `project.json` path, unwraps the `--emit`ted stage envelopes to their `.data`
   payload, verifies every declared artifact is present and non-empty, and removes
   the staging dir. Exit `0` all declared artifacts materialized; `1` one was
   missing or empty; `2` a package/usage error. Read the per-view/-export lines it
   prints.

Semantic `dediren_validate` (above) still gates `source-valid` — run it first.
Rendered SVGs land raw, so the accessible-name step below is still required, and a
re-render still means a stale gallery (`SKILL.md` step 7).

## Reading tool results

MCP tool results carry the same envelope JSON the CLI printed, so the guide's
Command Handoff rules apply unchanged. Check `isError` on the tool result and the
envelope `status` before trusting output.

- `dediren_validate` returns a generic envelope: read `.status` and `.diagnostics[]`.
- `dediren_build` is the exception — what it returns **is** the build-result
  document (`build-result.schema` family), not wrapped in a `.data`. Roll up its
  top-level `.status` together with every entry in `.views[]`: a stage failure is
  scoped to the view it happened in, so the remaining views still run and still
  report, and reading only the first entry hides them. `.views[].artifacts[]` names
  each written file (`{artifact_kind, path}`) relative to `out`. A build-level
  failure (no lane selected, or the source itself fails `validate`) leaves `.views`
  empty with the failure on the top-level `.diagnostics[]`.
- The `--emit`ted stage files under `<out>/<view-id>/` invert this: they *are*
  ordinary envelopes, and the package stores their unwrapped `.data` payload —
  `dediren-build.py map` does that, so never write a whole envelope into a package
  file.

### Layout quality

`dediren_build` runs `validate-layout` inside the build and emits the
`layout-result` stage (mapped to `generated/layout/<view-id>.json`). Read the
mapped payload as the authoritative source: `data.status` and the `data.*_count`
quality fields (`overlap_count`, `connector_through_node_count`,
`invalid_route_count`, and the other §9 gate counts; `edge_crossing_count` is
informational). A layout quality problem surfaces as a `warning` status on the
view entry with a `DEDIREN_LAYOUT_QUALITY_WARNING` diagnostic naming the offending
count. Treat `data.status: "warning"` or any nonzero non-informational count as a
blocking layout finding (`ARCH-L-*`) to resolve or disclose before claiming render
evidence; an overlap can superimpose two nodes in the rendered SVG.

### Rendered SVG

After `map` materializes a rendered SVG, complete its accessible name (the runtime
emits `role="img"` + `<title>` natively; the render-policy `accessibility` block or
the view-id fallback) and add the visible title:

```bash
"$SKILL_DIR"/references/scripts/svg-accessible-name.sh --title "<view label>" --desc "<view architecture question>" <pkg>/generated/svg/<view-id>.svg
```

To steer placement, set `layout_preferences` (`mode` / `direction` / `density` /
`wrapping` / `routing`, plus the ELK Layered tuning knobs and per-node placement
hints; enums and guidance in `architecture.md` §9) on the view in the source model,
then rebuild. For navigable output, set the render policy `interactive` field (§3);
static SVG is the default. After every render, verify the mode from the artifact
before disclosing it — `grep -c '<script' <svg>` is `0` for a static policy and
`≥ 1` when `interactive` scripts the SVG — and report that verified mode, never the
policy intent, in the footer `Layout/render options` line. A mismatch is `ARCH-R-5`;
a script despite a static policy additionally goes upstream under `Dediren tool
issues` (`architecture.md` §9 render-mode check).

For a UML view whose render metadata authors association end adornments (edge
`properties.source_role` / `target_role` / `source_multiplicity` /
`target_multiplicity`), also verify end-adornment coverage after materializing the
SVG: collect the nonempty adornment values from the mapped render metadata
(`generated/render-metadata/<view-id>.json`, e.g. `jq` over `.edges[].properties`)
and confirm each appears as an SVG `<text>` label. Report the count in the footer
quality qualifier (`render-ready (end adornments <rendered> of <authored>)`); a
missing adornment is `ARCH-R-2` plus a `Dediren tool issues` entry per
`architecture.md` §9 — this content has dropped with every stage reporting
`status: ok`, so envelope checks never prove it.

The bundled release is an imported upstream Dediren artifact. Do not patch cached
release files or future packaged bundles; report defects under `Dediren tool issues`
per `architecture.md` §9.
