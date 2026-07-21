#!/usr/bin/env python3
"""Plan and materialize a dediren architecture package built through the MCP server.

The architecture-design skill drives dediren through the plugin's bundled MCP server
(`dediren_build` / `dediren_validate` tools), not the CLI. The `dediren_build` tool
writes each view's artifacts under `<out>/<view-id>/` — `diagram.svg`, and the
`--emit` stage envelopes — exactly as the CLI `build` did, which is *not* where
`project.json` declares them. This script owns the two deterministic halves the tool
does not: deciding which `dediren_build` calls a package needs, and moving the built
output into the canonical `project.json` paths.

The MCP server is the primary path; `plan` + `map` bracket the tool calls. When the
server is not available, `run` is the internal fallback that drives the same builds
through the dediren CLI (resolving the pinned bundle on demand) — invisible to the
user, who never types a dediren command. Three subcommands:

    dediren-build.py plan <package-dir> [--views a,b] [--no-export]
        Print the JSON list of `dediren_build` MCP tool calls to make for the
        package (one per (model, render-policy) render group, one per export view),
        all writing into a shared staging dir under the package. Make each call with
        the bundled dediren MCP server, then run `map`.

    dediren-build.py map <package-dir> [--views a,b] [--no-export] [--json]
        After the tool calls have written into the staging dir, move every declared
        artifact to the path `project.json` declares, unwrapping the `--emit` stage
        envelopes to their `.data` payload, and remove the staging dir. Verifies each
        declared artifact is present and non-empty.

    dediren-build.py run <package-dir> [--views a,b] [--no-export] [--json]
        Internal fallback when the MCP server is not running: resolve the pinned
        dediren bundle (downloading on demand into the shared cache) and execute each
        planned build through the CLI into the staging dir, then materialize exactly
        as `map` does. Same output as `map`. Honours a preset $DEDIREN.

Two shape rules this script exists to enforce (getting either backwards writes an
empty or wrong-shaped package file):

  * A rendered `diagram.svg` is a raw artifact copied verbatim to `render_out`.
  * A `--emit`ted stage file (`render-metadata.json`, `layout-result.json`) is an
    ordinary envelope; the package stores its unwrapped `.data` payload.

Rendered SVG is written raw. Completing its accessible name (and visible title) is
the caller's next step — `svg-accessible-name.sh` per rendered view, per
architecture.md section 9 — then the gallery (`build-gallery.py`).

An export policy's identity fields apply to a whole `dediren_build` invocation rather
than to each view within it, so `plan` scopes every export to a single view.

Exit codes: 0 ok; 1 a declared artifact was missing or empty; 2 usage or
package-input error; 3 the dediren runtime could not be resolved (run).

Stdlib-only; Python >= 3.9.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# project.json export plugin -> (dediren_build MCP arg, artifact filename build writes)
EXPORT_LANES = {
    "archimate-oef": ("oef_policy", "oef.xml"),
    "uml-xmi": ("xmi_policy", "xmi.xml"),
}
# Stage envelopes to persist. layout-request is not declared by project.json, so it
# is not emitted; render-metadata and layout-result are.
EMIT_KINDS = ("render-metadata", "layout-result")
# Staging directory (under the package, inside the MCP server --root) that the
# `dediren_build` calls write into and `map` drains.
STAGING_DIR = ".dediren-build"


class PackageError(Exception):
    """The package's project.json cannot be interpreted."""


def normalize(project):
    """Fold project.json v1 and v2 into one shape.

    Returns (models, views, exports):
      models  {model_id: model_file}
      views   [{id, model_id, render_policy, render_out, metadata_out, layout_out}]
      exports [{view_id, model_id, plugin, policy, output}]
    """
    raw_views = project.get("views") or []
    if not raw_views:
        raise PackageError("project.json declares no views")

    if project.get("models"):  # v2: several single-notation models
        models = {entry["id"]: entry["file"] for entry in project["models"]}
        default_model = None
    else:  # v1: one model for the whole package
        model_file = project.get("model")
        if not model_file:
            raise PackageError("project.json declares neither 'models' nor 'model'")
        default_model = "__default__"
        models = {default_model: model_file}

    views = []
    for view in raw_views:
        model_id = view.get("model", default_model)
        if model_id not in models:
            raise PackageError(f"view {view.get('id')!r} names unknown model {model_id!r}")
        try:
            render = view["render"]
            views.append(
                {
                    "id": view["id"],
                    "model_id": model_id,
                    "render_policy": render["policy"],
                    "render_out": render["output"],
                    "metadata_out": view["metadata"]["output"],
                    "layout_out": view["layout"]["output"],
                }
            )
        except KeyError as exc:
            raise PackageError(f"view {view.get('id')!r} is missing {exc}") from exc

    raw_exports = project.get("exports")
    if raw_exports is None:
        single = project.get("export")
        raw_exports = [single] if single else []
    exports = []
    for export in raw_exports:
        view_id = export.get("view")
        if view_id is None:
            # v1 names no view. Unambiguous only for a single-view package; guessing
            # which view an export belongs to would silently export the wrong one.
            if len(views) != 1:
                raise PackageError(
                    "project.json 'export' names no 'view' and the package has "
                    f"{len(views)} views; add \"view\": \"<view-id>\" to the export"
                )
            view_id = views[0]["id"]
        known = {view["id"]: view for view in views}
        if view_id not in known:
            raise PackageError(f"export names unknown view {view_id!r}")
        plugin = export.get("plugin")
        if plugin not in EXPORT_LANES:
            raise PackageError(f"export names unsupported plugin {plugin!r}")
        exports.append(
            {
                "view_id": view_id,
                "model_id": known[view_id]["model_id"],
                "plugin": plugin,
                "policy": export["policy"],
                "output": export["output"],
            }
        )
    return models, views, exports


def select(views, exports, views_filter, no_export):
    """Apply the --views / --no-export filters, refusing unknown view ids."""
    if views_filter:
        wanted = [v.strip() for v in views_filter.split(",") if v.strip()]
        known = {view["id"] for view in views}
        unknown = [v for v in wanted if v not in known]
        if unknown:
            raise PackageError(f"unknown view ids: {', '.join(unknown)}")
        views = [view for view in views if view["id"] in wanted]
        exports = [e for e in exports if e["view_id"] in wanted]
    if no_export:
        exports = []
    return views, exports


def plan(pkg, models, views, exports):
    """The `dediren_build` MCP tool calls needed to build the package.

    All calls write into one staging dir under the package (inside the server root);
    each view's artifacts land under `<staging>/<view-id>/` with fixed filenames, so
    render groups and single-view exports never collide. Paths are relative to the
    package so they resolve inside any MCP `--root` at or above it.
    """
    staging = f"{STAGING_DIR}"
    calls = []

    # Render lane: one call per (model, render-policy) group. Views sharing both are
    # built together; a differing policy or model needs its own invocation.
    groups = {}
    for view in views:
        groups.setdefault((view["model_id"], view["render_policy"]), []).append(view)
    for (model_id, policy), group in sorted(groups.items()):
        calls.append(
            {
                "tool": "dediren_build",
                "arguments": {
                    "source": _rel(pkg, models[model_id]),
                    "out": _rel(pkg, staging),
                    "views": [view["id"] for view in group],
                    "render_policy": _rel(pkg, policy),
                    "emit": list(EMIT_KINDS),
                },
            }
        )

    # Export lanes: one single-view call each, because an export policy's identity
    # fields apply to the whole invocation rather than per view.
    for export in exports:
        arg, _artifact = EXPORT_LANES[export["plugin"]]
        calls.append(
            {
                "tool": "dediren_build",
                "arguments": {
                    "source": _rel(pkg, models[export["model_id"]]),
                    "out": _rel(pkg, staging),
                    "views": [export["view_id"]],
                    arg: _rel(pkg, export["policy"]),
                },
            }
        )
    return {"package": str(pkg), "staging": str(pkg / staging), "calls": calls}


def _rel(pkg, member):
    """Package member path relative to the package dir (server-root friendly)."""
    return str((pkg / member))


def payload_of(envelope_path):
    """The `.data` payload of an emitted stage envelope."""
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    if "data" not in envelope:
        raise PackageError(f"{envelope_path.name} is not a stage envelope (no .data)")
    return envelope["data"]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def copy_artifact(src, dest):
    if not src.is_file() or src.stat().st_size == 0:
        raise PackageError(f"dediren build did not write {src.name}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def materialize_view(staging, pkg, view):
    """Move one view's staged output to the paths project.json declares."""
    view_dir = staging / view["id"]
    written = []

    copy_artifact(view_dir / "diagram.svg", pkg / view["render_out"])
    written.append(view["render_out"])

    for kind, declared in (("render-metadata", "metadata_out"), ("layout-result", "layout_out")):
        envelope = view_dir / f"{kind}.json"
        if not envelope.is_file():
            raise PackageError(f"staging is missing {kind} for view {view['id']!r}")
        write_json(pkg / view[declared], payload_of(envelope))
        written.append(view[declared])
    return written


def run_map(pkg, models, views, exports):
    """Drain the staging dir into the package's canonical project.json paths."""
    staging = pkg / STAGING_DIR
    if not staging.is_dir():
        raise PackageError(
            f"no staging dir {staging}; run the planned dediren_build MCP calls first"
        )
    summary = {"package": str(pkg), "views": [], "exports": [], "status": "ok"}

    for view in views:
        entry = {"view": view["id"], "status": "ok", "artifacts": []}
        try:
            entry["artifacts"] = materialize_view(staging, pkg, view)
        except PackageError as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
        summary["views"].append(entry)

    for export in exports:
        _arg, artifact = EXPORT_LANES[export["plugin"]]
        entry = {"export": export["plugin"], "view": export["view_id"], "status": "ok"}
        try:
            copy_artifact(staging / export["view_id"] / artifact, pkg / export["output"])
            entry["output"] = export["output"]
        except PackageError as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
        summary["exports"].append(entry)

    shutil.rmtree(staging, ignore_errors=True)

    if any(e["status"] == "error" for e in summary["views"] + summary["exports"]):
        summary["status"] = "error"
    return summary


class RuntimeUnavailable(Exception):
    """The pinned dediren release bundle could not be resolved (fallback lane)."""


def resolve_dediren(script_dir):
    """Absolute path to the pinned dediren CLI (honours a preset $DEDIREN)."""
    preset = os.environ.get("DEDIREN")
    if preset:
        return preset
    resolver = script_dir / "dediren-release.sh"
    if not resolver.is_file():
        raise RuntimeUnavailable(f"release resolver not found: {resolver}")
    proc = subprocess.run(
        ["bash", str(resolver), "--ensure"],
        check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeUnavailable(
            "dediren-release.sh --ensure failed; disclose "
            "'not run (dediren runtime unavailable)' and cap at source-valid.\n"
            + proc.stderr.strip()
        )
    return proc.stdout.strip()


# dediren_build MCP argument name -> dediren CLI flag, for the fallback lane.
_CLI_FLAGS = {"render_policy": "--render-policy", "oef_policy": "--oef-policy", "xmi_policy": "--xmi-policy"}


def run_cli(pkg, models, views, exports, script_dir):
    """Internal fallback: execute each planned build through the dediren CLI, then map.

    Mirrors the MCP path — same staging dir, same per-(model, render-policy) render
    groups and single-view exports the plan emits — but drives the runtime via the
    CLI when the MCP server is not warm. The user never sees a dediren command.
    """
    dediren = resolve_dediren(script_dir)
    for call in plan(pkg, models, views, exports)["calls"]:
        arguments = call["arguments"]
        cmd = [dediren, "build", "--input", arguments["source"], "--out", arguments["out"],
               "--views", ",".join(arguments["views"])]
        for arg, flag in _CLI_FLAGS.items():
            if arg in arguments:
                cmd += [flag, arguments[arg]]
        if "emit" in arguments:
            cmd += ["--emit", ",".join(arguments["emit"])]
        proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            document = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise PackageError(
                f"dediren build emitted no JSON (exit {proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            ) from None
        if "build_result_schema_version" not in document:
            diagnostics = document.get("diagnostics", [])
            codes = ", ".join(d.get("code", "?") for d in diagnostics) or "unknown"
            raise PackageError(f"dediren build rejected the request ({codes})")
    return run_map(pkg, models, views, exports)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dediren-build.py",
        description="Plan and materialize a dediren package built via the MCP server.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("plan", "print the dediren_build MCP calls to make"),
        ("map", "materialize staged build output into project.json paths"),
        ("run", "internal fallback: build via the dediren CLI, then materialize"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("package", help="path to docs/architecture/<feature>.dediren")
        p.add_argument("--views", help="comma-separated view ids (default: every view)")
        p.add_argument("--no-export", action="store_true", help="skip OEF/XMI export lanes")
        if name in ("map", "run"):
            p.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args(argv)

    pkg = Path(args.package)
    try:
        project_path = pkg / "project.json"
        if not project_path.is_file():
            raise PackageError(f"no project.json in {pkg}")
        models, views, exports = normalize(json.loads(project_path.read_text(encoding="utf-8")))
        views, exports = select(views, exports, args.views, args.no_export)

        if args.command == "plan":
            print(json.dumps(plan(pkg, models, views, exports), indent=2))
            return 0

        if args.command == "run":
            summary = run_cli(pkg, models, views, exports, Path(__file__).resolve().parent)
        else:
            summary = run_map(pkg, models, views, exports)
    except PackageError as exc:
        print(f"dediren-build: {exc}", file=sys.stderr)
        return 2
    except RuntimeUnavailable as exc:
        print(f"dediren-build: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for entry in summary["views"]:
            print(f"view {entry['view']}: {entry['status']}")
            for path in entry["artifacts"]:
                print(f"  wrote {path}")
            if entry.get("error"):
                print(f"  {entry['error']}")
        for entry in summary["exports"]:
            print(f"export {entry['export']} ({entry['view']}): {entry['status']}")
            if entry["status"] == "ok":
                print(f"  wrote {entry['output']}")
            elif entry.get("error"):
                print(f"  {entry['error']}")
        print(f"{args.command}: {summary['status']}")
        if summary["status"] != "error":
            print("next: complete each rendered SVG's accessible name (svg-accessible-name.sh),")
            print("      then rebuild the package gallery (build-gallery.py).")

    return 1 if summary["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
