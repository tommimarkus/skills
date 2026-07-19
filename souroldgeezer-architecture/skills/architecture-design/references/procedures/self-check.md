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

The bundled server needs the pinned Java™-backed runtime on the host (Java™ 21 or
newer) — exactly as a Node- or Python-based plugin MCP server needs its runtime
installed. The launcher **resolves the pinned bundle on demand** at session start
when the cache is cold, then starts the server. The resolve is bounded (the resolver
caps curl with `--connect-timeout`/`--max-time` and the install lock with `flock -w`)
so it can never hang session start, and it caches per-user under
`${CLAUDE_PLUGIN_DATA}` — at most one download per pinned version per user, not per
repo. The fast path, when the bundle is already resolved, does no network I/O. The
`dediren_*` tools are absent only when the resolve cannot complete (host offline) or
Java™ 21+ is missing.

When the tools are absent — resolve failed, Java™ 21+ missing, or the freshly-resolved
server not yet reconnected this session — fall back to the **internal CLI lane**:
`dediren-build.py run` (below) resolves the bundle on demand and drives the same
runtime through the CLI, and the resolver provides the binary for the validate
fallback. This is internal machinery; the user never types a dediren command. Both
lanes share the same `${CLAUDE_PLUGIN_DATA}` cache, so once the bundle is present the
server starts on its own at the next session start — a pin bump no longer strands the
server, because the launcher resolves the newly-pinned bundle itself. Only when the
fallback itself cannot resolve a Java™ 21+ runtime do you disclose `not run (dediren
runtime unavailable)` and cap at `source-valid` — a capability cap, not a hard stop. Disclose which lane ran in the
footer (`Dediren: MCP server | CLI fallback | not run`). Do not ask the user to
install or launch Dediren; the plugin owns that.

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

When the MCP server is unavailable, run the same validation through the internal CLI
lane (§ Server availability): resolve the binary with
`DEDIREN="$("$SKILL_DIR"/references/scripts/dediren-release.sh --ensure)"`, then
`"$DEDIREN" validate --input <pkg>/model.json` for schema and
`"$DEDIREN" validate --plugin generic-graph --profile archimate` (or `uml`) for the
semantic gate. This is the same evidence, obtained without the server.

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

When the MCP server is unavailable, build through the internal CLI lane in one call —
`"$SKILL_DIR"/references/scripts/dediren-build.py run <pkg>` — which resolves the
bundle on demand, drives the same builds through the CLI, and materializes exactly as
`map`. Same output; exit `3` if the runtime cannot be resolved. Prefer the MCP tools
when the server is up; use `run` only as the fallback.

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

`dediren_build` runs `validate-layout` inside the build; its verdict lands on the
build-result document, not in the mapped layout file. Read the `dediren_build`
view entry as the authoritative source: `.views[].status` (`ok` / `warning` /
`error`) and the gate counts carried by its `.views[].diagnostics[]`. A layout
quality problem surfaces as a `warning` on the view entry with a
`DEDIREN_LAYOUT_QUALITY_WARNING` diagnostic that names the offending count (for
example `overlap_count`, `route_detour_count`, or `edge_label_dissociation_count`;
take the field names from the diagnostic itself — the runtime's gate-count set has
drifted — and `edge_crossing_count` is informational). The mapped
`generated/layout/<view-id>.json` (`layout-result.schema.v2`) carries layout
*geometry* — `nodes` / `edges` / `groups` and a `warnings[]` array — not the
quality verdict, so do not read `data.status` or `data.*_count` from it; the
runtime stopped emitting them there (see source grounding). Treat a `warning` view
status or any nonzero non-informational count as a blocking layout finding
(`ARCH-L-*`) to resolve or disclose before claiming render evidence; an overlap can
superimpose two nodes in the rendered SVG.

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
then rebuild. Renders are static SVG (the runtime retired the interactive render
policy, §3). After every render, verify the artifact is static before disclosing
it — `grep -c '<script' <svg>` must be `0` — and report that verified static
mode, never the policy intent, in the footer `Layout/render options` line. A
`≥ 1` script count, or a footer that misreports the artifact, is `ARCH-R-5`; a
script additionally goes upstream under `Dediren tool issues`
(`architecture.md` §9 render-mode check).

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
