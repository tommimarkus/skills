# Dediren Self-Check

<!-- lean-audit:sync-intentional -->
Before runtime claims, prefer the plugin's Dediren MCP adapter: call its tools —
`dediren_validate`, `dediren_build`, `dediren_guide` — with an absolute
`workspaceRoot` on every operation. The adapter is bundled and provisions
Dediren: it discovers the resolved executable's live tools, whether that came
from `DEDIREN_COMMAND`, the plugin's own managed install, a floor-meeting
`dediren` on `PATH`, the former verified release cache, or a first-use install
of the pinned release.
The server contract and the `${CLAUDE_SKILL_DIR}` semantics are canonical in
`architecture.md` §9 Runtime Evidence; `${CLAUDE_SKILL_DIR}` locates this skill's
own helper scripts (`build-gallery.py`, `svg-accessible-name.py`), not Dediren.
Claude Code expands that token in the loaded SKILL.md. In Codex, reuse the
absolute `<skill-dir>` resolved from the loaded skill source anywhere this raw
procedure shows `${CLAUDE_SKILL_DIR}`.

## Server availability

Dediren must be executable in the MCP process sandbox, and the launcher gets it
there itself: it resolves `DEDIREN_COMMAND`, its managed install under the
plugin data directory, a `dediren` on `PATH` reporting at or above the floor, or
the former verified release cache — and otherwise installs the pinned
`2026.08.5` release, verified against `SHA256SUMS` before unpacking, on the first
`tools/list`. It never installs Java, never downgrades, and never patches the
runtime. When provisioning fails or must be overridden — no Java 21+, no plugin
data directory (exit 78), a download or checksum failure, an air-gapped host, or
a resolved runtime below the floor — read
`references/procedures/dediren-install.md` and hand the user its steps, instead
of improvising an install or working around the gap. Claude Code launches
the adapter from its manifest; Codex and Copilot both use the Agent Plugins root
`plugin.json` plus its `mcp.json`, with `mcp/codex.mcp.json` and
`mcp/copilot.mcp.json` retained as their legacy lanes. The router handles both the legacy
`initialize` / `initialized` exchange and MCP 2026-07-28 stateless
`server/discover`, obtains `tools/list` from the installed Dediren, and keeps one
upstream process per explicit workspace root. Startup and catalog waits default
to 120 seconds (`DEDIREN_MCP_STARTUP_TIMEOUT_SEC`); tool-call waits default to
360 seconds (`DEDIREN_MCP_REQUEST_TIMEOUT_SEC`). Each override must be a positive
number of seconds. A known-dead process is replaced for the next call, an
uncertain tool call is never
auto-retried, and EOF or router termination closes every child. A host sandbox
therefore works when it permits this local stdio MCP process, the external
executable, and the selected workspace; the adapter does not bypass host
filesystem or network policy.

The host configuration is intentionally specific: Claude Code interpolates
`${CLAUDE_PLUGIN_ROOT}` in its inline command and explicitly sets `DEDIREN_HOME`
from `${CLAUDE_PLUGIN_DATA}`. Codex Agent Plugins and the root Copilot lane
export plugin-data variables read by the resolver; root `mcp.json` deliberately
declares no `env` or `cwd`. The retained legacy `.codex-plugin` lane stays
literal with `cwd: "."` and gets no plugin data root at all; the legacy Copilot
lane explicitly sets `DEDIREN_HOME` from `${COPILOT_PLUGIN_DATA}`. Regardless of
that configuration, the shared launcher/router has no harness detection and
sets each upstream child cwd from the absolute per-call `workspaceRoot`. The
three `DEDIREN_COMMAND`, `DEDIREN_MCP_STARTUP_TIMEOUT_SEC`, and
`DEDIREN_MCP_REQUEST_TIMEOUT_SEC` overrides apply uniformly, as do
`DEDIREN_HOME`, `DEDIREN_VERSION`, and `DEDIREN_AUTO_INSTALL`. Router values and
the legacy Codex `startup_timeout_sec` are seconds; Copilot `timeout` is
milliseconds; the Agent Plugins lane has no MCP startup-timeout field, so Codex's
30s default applies — safe, because the router answers `initialize` itself and
provisioning waits for the first `tools/list`.
The maintained adapters are Claude Code, Codex, and Copilot CLI.

Generic local-client compatibility is limited to local stdio process launch with
Bash, Python, and Java 21+, and an absolute `workspaceRoot` per tool call. Such a
client must also give the launcher somewhere to install: `DEDIREN_HOME` set to an
absolute path when it exposes none of `CLAUDE_PLUGIN_DATA` /
`COPILOT_PLUGIN_DATA` / `PLUGIN_DATA`, or `DEDIREN_COMMAND` pointing at an
executable it manages itself. It does not establish another maintained harness.
Preserve the legacy verified-release-cache fallback. Streamable HTTP is future
work only for an explicit remote/shared multi-client service requirement; first
design authentication, origin validation, port/service lifecycle, session
isolation, and workspace authorization.
Require `dediren --version` (or `$DEDIREN_COMMAND --version`) to report
`2026.07.28` or newer before rendering; that floor is the resolve gate for a
host-supplied executable, while the plugin's own install is pinned above it.

`dediren_validate` / `dediren_guide` plus the four read-only tools (`dediren_diff` /
`dediren_query` / `dediren_verify` / `dediren_status`) are the read-only subset that
a `dediren mcp --read-only` server keeps — only `dediren_build` is withheld — so
Extract, Review, and Lookup work against a read-only server. The plugin adapter
runs full because Build needs `dediren_build`; the launcher never passes
`--read-only` (architecture §9).

When the MCP tools are absent, use the **internal CLI lane** only if the same
resolved executable is available as `${DEDIREN_COMMAND:-dediren}`. This is
internal machinery; the user never has to retype the model command. Do not
hand-fetch or substitute a runtime outside the launcher's own provisioning. If
neither MCP nor CLI can execute, disclose
`not run (dediren runtime unavailable)` and report `Quality level: not assessed` — a
capability cap, not a hard stop. Disclose which lane ran in the footer
(`Dediren: MCP server | CLI fallback | not run`) and identify the missing external
prerequisite rather than fabricating a pass.

Every tool call passes the same absolute project directory as `workspaceRoot`;
every other tool path is relative to it and must remain inside that root,
and so must every `fragments[]` path inside a source you pass. A path that escapes
it returns a `DEDIREN_MCP_PATH_OUTSIDE_ROOT` error envelope — keep packages and
their fragments under the project root.

## Validate

`source-valid` requires semantic validation, not schema alone. Call
`dediren_validate` with the source path **and** `profile` set to the model's
notation:

- `dediren_validate {workspaceRoot: "/abs/project", source: "<pkg>/model.json", profile: "archimate"}` for ArchiMate.
- `dediren_validate {workspaceRoot: "/abs/project", source: "<pkg>/model.json", profile: "uml"}` for UML.

The tool runs schema validation plus semantic-profile validation and returns the
validation envelope; `dediren_validate` without a `profile` proves schema only. Use
`generic-graph`, `elk-layout`, `render`; set `plugins.generic-graph.semantic_profile`
to `archimate` or `uml` in the source, and add `archimate-oef` only when OEF export
is requested, `uml-xmi` only when XMI export is requested.

When the MCP server is unavailable, run the same validation through the internal CLI
lane (§ Server availability): set `DEDIREN="${DEDIREN_COMMAND:-dediren}"`, require
that command to exist, then run `"$DEDIREN" validate --input <pkg>/model.json` for schema and
`"$DEDIREN" validate --plugin generic-graph --profile archimate` (or `uml`) for the
semantic gate. This is the same evidence, obtained without the server.

## Migrating an outdated input

When validation (or a build) rejects an input with
`DEDIREN_SCHEMA_VERSION_OUTDATED`, the diagnostic carries a machine-readable
`migration` object `{from, to, operations: [{op, pointer?, to?, value?}]}`
(architecture §9). Dediren never rewrites the file — the skill upgrades it. Apply
the `operations` in order to the outdated source or policy: `rename_field`,
`remove_key`, or `set_version` at the diagnostic's JSON `pointer` (using its `to` /
`value`), or `regenerate` to rebuild the named artifact. Then re-run
`dediren_validate` to confirm the input now passes. Only migrate an input the task
already edits or owns; for a package you were asked only to review, report the
version-outdated state as a finding rather than silently upgrading it.

## Format guide

Resolving evidence does not require the guide. Defer it until authoring, repairing,
or handing off source JSON is imminent; a resolve-and-validate or review-only check
never needs it. When that point is reached, read the guide through the tool:

```
dediren_guide {workspaceRoot: "/abs/project"}                       # index
dediren_guide {workspaceRoot: "/abs/project", topic: "source-json"} # start here
```

Its topic scope (Minimal Source JSON, Artifact Map, Semantic Profiles, Command
Handoff, Repair Rules) is stated in `architecture.md` §9. When running OEF or
XMI export, follow the installed Dediren guide's schema-cache instructions. The
export engines inherit the resolved Dediren process environment. If export fails with
`DEDIREN_*_SCHEMA_UNAVAILABLE` (offline host), read the diagnostic's
`message`: it names whether to make that cache writable or to pre-fetch the XSDs and
pass absolute offline paths via `DEDIREN_OEF_SCHEMA_DIR` / `DEDIREN_XMI_SCHEMA_PATH`.
`DEDIREN_XMI_SCHEMA_PATH` at the bare `XMI.xsd` validates only the XMI envelope; full
UML-content schema validation needs the driver schema in
[external-validation-handoff](external-validation-handoff.md) required disclosure 4.

## Building a package (default path)

One `dediren_build` call with a `package` argument builds the whole package — every
view across every model, each through projection, layout, layout validation and its
own render policy, plus the view- or model-scoped export lanes — and writes each
artifact **directly to the path `package.json` declares**. No staging dir, no path
arithmetic, no per-view fan-out: the runtime owns the build graph.

1. Call `dediren_build` with absolute `workspaceRoot` and `package` set to the
   package's relative `package.json` path; add
   `no_export: true` to suppress the export lanes. `package` is mutually exclusive
   with the single-model arguments (`source` / `out` / `render_policy` /
   `oef_policy` / `xmi_policy` / `emit`).
2. Read the result. Unlike a single-model build, a package build **is** wrapped in
   the standard envelope — read `.data` for the `package-build-result`. Roll up its
   `.status` together with every `.views[]` and `.exports[]` entry: each carries its
   own `status` and `diagnostics`, so reading only the rollup hides a failed lane.
   Manifest-level rejections — an id that resolves to nothing, two entries claiming
   one output path — surface as `DEDIREN_PACKAGE_*` and are raised up front, so a
   package the runtime refuses leaves no half-written artifacts behind.

When the MCP server is unavailable, build through the internal CLI lane:

```bash
DEDIREN="${DEDIREN_COMMAND:-dediren}"
command -v "$DEDIREN" >/dev/null 2>&1 || { printf 'Dediren unavailable\n' >&2; exit 127; }
"$DEDIREN" build --package <pkg>/package.json      # or: "$DEDIREN" build <pkg>
```

Same `package-build-result` on stdout. Prefer the MCP tool when the server is up;
use the CLI only as the fallback.

Semantic `dediren_validate` (above) still gates `source-valid` — run it first. Each
view's `presentation.title` / `question` reaches the render lane as that view's SVG
accessible name (`<title>` / `<desc>`), per view even under a shared render policy —
but the *visible* title band is still the skill's own, so the post-render band
step below remains required, and a re-render still means a stale gallery
(`SKILL.md` step 7).

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
- A package build's declared `render_metadata` / `layout` outputs are the
  unwrapped stage payloads, not `--emit` envelopes — the runtime writes them that
  way, so never hand-write a whole envelope into a package file.
- `dediren_diff`, `dediren_query`, `dediren_verify`, and `dediren_status` carry
  their result document (`diff-result` / `query-result` / `verify-result` /
  `status-result` schema; architecture §9) in the tool result — check `isError` and
  the envelope `status` first, as for `dediren_validate`. `dediren_verify` is an
  error (`isError`, `DEDIREN_ARTIFACT_STALE`) when any artifact is `stale` — the
  drift gate: a stale SVG or gallery → `ARCH-R-2`, a stale export → `ARCH-E-4`; an
  `unstamped` artifact is the non-error `DEDIREN_ARTIFACT_UNSTAMPED` warning,
  disclosable and not a finding on its own (committed pre-stamping evidence reads
  `unstamped`). `dediren_query` returns `DEDIREN_COMMAND_INPUT_INVALID` on an
  unknown `kind` or a `dependents` query with no `id`. `dediren_status` is a
  non-gating index; `dediren_diff` is report-only.

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
status or any nonzero non-informational count as a `warn`-class `ARCH-L-3` finding —
resolve or disclose it before claiming render-ready, but it is not a hard block (a
layout *validation error* — connector-through-node, invalid route, group-boundary —
is the blocking case, `ARCH-L-2`). An `overlap_count` that superimposes two nodes in
the rendered SVG is a render defect (`ARCH-R-3`), not merely hard to scan.

### Rendered SVG

After the build materializes a rendered SVG, add the visible title band — the
step's job. The runtime already emits `role="img"` + `<title>` / `<desc>`
natively from the view's `presentation`, and the step requires that name rather
than synthesising one: an artifact without it exits 4, and the remedy is a
re-render on a supported runtime (`architecture.md` §9):

```bash
${CLAUDE_SKILL_DIR}/references/scripts/svg-accessible-name.py --title "<view label>" --desc "<view architecture question>" <pkg>/generated/svg/<view-id>.svg
# Codex: replace ${CLAUDE_SKILL_DIR} with the resolved absolute <skill-dir>.
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

The selected Dediren executable is an upstream runtime, whether the launcher
provisioned it or the host supplied it. Do not patch, hand-download, or downgrade
it from this workflow; report
defects under `Dediren tool issues` per `architecture.md` §9.
