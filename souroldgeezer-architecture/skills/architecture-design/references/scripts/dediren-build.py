#!/usr/bin/env python3
"""Build a dediren architecture package with the one-shot `dediren build` command.

Replaces the decomposed per-view chain (project x2 -> layout -> validate-layout ->
render/export) with one runtime call per (model, render-policy) group, then
materializes the results into the canonical paths `project.json` declares.

Dediren >= 2026.07.14 runs its five engines in-process behind a single launcher, so
one `build` call can walk a view through every stage the decomposed commands run
separately. The win is process count: one JVM start per group, rather than 13-15
across a package. Flag and result contracts are specified in the bundle's own agent
guide (`dediren-release.sh --agent-guide`, section Build).

Two shape rules this script exists to enforce (getting either backwards writes an
empty or wrong-shaped package file, with every stage still reporting success):

  * What `build` prints is already the build-result document. Nothing wraps it, so
    there is no `.data` to reach into -- unlike the per-stage commands.
  * The stage artifacts it writes under `--emit` are the opposite: those are
    ordinary envelopes, and the package stores their unwrapped `.data` payload at
    the path `project.json` declares.

Rendered SVG is written raw. Completing its accessible name (and visible title) is
the caller's next step -- `svg-accessible-name.sh` per rendered view, per
architecture.md section 9 -- exactly as with the decomposed flow.

An export policy's identity fields apply to a whole invocation rather than to each
view within it, so every export declared by `project.json` is run on its own with a
single view selected.

Usage:
    dediren-build.py <package-dir>              build every view, plus declared exports
    dediren-build.py <package-dir> --views a,b  build only these views
    dediren-build.py <package-dir> --no-export  skip the OEF/XMI export lanes
    dediren-build.py <package-dir> --json       machine-readable summary on stdout
    dediren-build.py --help

Exit codes: 0 all views ok (warnings allowed, and reported); 1 a view or export
failed, or a declared artifact was missing/empty; 2 usage or package-input error;
3 the dediren runtime could not be resolved.

Stdlib-only; Python >= 3.9.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# project.json export plugin -> (build lane flag, artifact filename build writes)
EXPORT_LANES = {
    "archimate-oef": ("--oef-policy", "oef.xml"),
    "uml-xmi": ("--xmi-policy", "xmi.xml"),
}
# Stage envelopes to persist. layout-request is not declared by project.json, so it
# is not emitted; render-metadata and layout-result are.
EMIT_KINDS = ("render-metadata", "layout-result")


class PackageError(Exception):
    """The package's project.json cannot be interpreted."""


class RuntimeUnavailable(Exception):
    """The pinned dediren release bundle could not be resolved."""


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
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeUnavailable(
            "dediren-release.sh --ensure failed; disclose "
            "'not run (missing dediren release bundle)' and cap at source-valid.\n"
            + proc.stderr.strip()
        )
    return proc.stdout.strip()


def normalize(project):
    """Fold project.json v1 and v2 into one shape.

    Returns (models, views, exports):
      models  {model_id: model_file}
      views   [{id, model_id, render_policy, render_out, metadata_out, layout_out}]
      exports [{view_id, model_id, plugin, policy, output}]
    """
    schema = project.get("schema", "")
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


def run_build(dediren, pkg, model_file, out_dir, view_ids, lanes, emit=()):
    """One `dediren build` call. Returns the parsed build-result document.

    Build's stdout is the build-result document itself, not an envelope.
    """
    cmd = [
        dediren,
        "build",
        "--input",
        str(pkg / model_file),
        "--out",
        str(out_dir),
        "--views",
        ",".join(view_ids),
    ]
    for flag, policy in lanes:
        cmd += [flag, str(pkg / policy)]
    if emit:
        cmd += ["--emit", ",".join(emit)]

    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        document = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise PackageError(
            f"dediren build emitted no JSON (exit {proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        ) from None
    if "build_result_schema_version" not in document:
        # A build-level input/IO failure arrives as a plain error envelope instead.
        diagnostics = document.get("diagnostics", [])
        codes = ", ".join(d.get("code", "?") for d in diagnostics) or "unknown"
        raise PackageError(f"dediren build rejected the request ({codes}): {json.dumps(diagnostics)}")
    return document


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


def materialize_view(build_dir, pkg, view):
    """Move one view's build output to the paths project.json declares."""
    view_dir = build_dir / view["id"]
    written = []

    copy_artifact(view_dir / "diagram.svg", pkg / view["render_out"])
    written.append(view["render_out"])

    for kind, declared in (("render-metadata", "metadata_out"), ("layout-result", "layout_out")):
        envelope = view_dir / f"{kind}.json"
        if not envelope.is_file():
            raise PackageError(f"dediren build did not emit {kind} for view {view['id']!r}")
        write_json(pkg / view[declared], payload_of(envelope))
        written.append(view[declared])
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dediren-build.py",
        description="One-shot dediren build for an architecture package.",
    )
    parser.add_argument("package", help="path to docs/architecture/<feature>.dediren")
    parser.add_argument("--views", help="comma-separated view ids (default: every view)")
    parser.add_argument("--no-export", action="store_true", help="skip OEF/XMI export lanes")
    parser.add_argument("--json", action="store_true", help="machine-readable summary on stdout")
    args = parser.parse_args(argv)

    pkg = Path(args.package)
    script_dir = Path(__file__).resolve().parent
    summary = {"package": str(pkg), "views": [], "exports": [], "status": "ok"}

    try:
        project_path = pkg / "project.json"
        if not project_path.is_file():
            raise PackageError(f"no project.json in {pkg}")
        models, views, exports = normalize(json.loads(project_path.read_text(encoding="utf-8")))

        if args.views:
            wanted = [v.strip() for v in args.views.split(",") if v.strip()]
            known = {view["id"] for view in views}
            unknown = [v for v in wanted if v not in known]
            if unknown:
                raise PackageError(f"unknown view ids: {', '.join(unknown)}")
            views = [view for view in views if view["id"] in wanted]
            exports = [e for e in exports if e["view_id"] in wanted]
        if args.no_export:
            exports = []

        dediren = resolve_dediren(script_dir)

        with tempfile.TemporaryDirectory(prefix="dediren-build-") as tmp:
            tmp_dir = Path(tmp)

            # Render lane: one call per (model, render-policy) group. Views sharing both
            # are built together; a differing policy or model needs its own invocation.
            groups = {}
            for view in views:
                groups.setdefault((view["model_id"], view["render_policy"]), []).append(view)

            for index, ((model_id, policy), group) in enumerate(sorted(groups.items())):
                out_dir = tmp_dir / f"render-{index}"
                result = run_build(
                    dediren,
                    pkg,
                    models[model_id],
                    out_dir,
                    [view["id"] for view in group],
                    [("--render-policy", policy)],
                    emit=EMIT_KINDS,
                )
                by_id = {view["view_id"]: view for view in result.get("views", [])}
                for view in group:
                    outcome = by_id.get(view["id"], {})
                    status = outcome.get("status", "error")
                    entry = {
                        "view": view["id"],
                        "status": status,
                        "diagnostics": outcome.get("diagnostics", []),
                        "artifacts": [],
                    }
                    # A stage failure is scoped to its own view; record it, keep the rest.
                    if status != "error":
                        entry["artifacts"] = materialize_view(out_dir, pkg, view)
                    summary["views"].append(entry)

            # Export lanes: one single-view call each, because an export policy's
            # identity fields apply to the whole invocation rather than per view.
            for index, export in enumerate(exports):
                out_dir = tmp_dir / f"export-{index}"
                flag, artifact = EXPORT_LANES[export["plugin"]]
                result = run_build(
                    dediren,
                    pkg,
                    models[export["model_id"]],
                    out_dir,
                    [export["view_id"]],
                    [(flag, export["policy"])],
                )
                outcome = next(
                    (v for v in result.get("views", []) if v["view_id"] == export["view_id"]), {}
                )
                status = outcome.get("status", "error")
                entry = {
                    "export": export["plugin"],
                    "view": export["view_id"],
                    "status": status,
                    "diagnostics": outcome.get("diagnostics", []),
                    "output": export["output"],
                }
                if status != "error":
                    copy_artifact(out_dir / export["view_id"] / artifact, pkg / export["output"])
                summary["exports"].append(entry)

    except PackageError as exc:
        print(f"dediren-build: {exc}", file=sys.stderr)
        return 2
    except RuntimeUnavailable as exc:
        print(f"dediren-build: {exc}", file=sys.stderr)
        return 3

    outcomes = [entry["status"] for entry in summary["views"] + summary["exports"]]
    if "error" in outcomes:
        summary["status"] = "error"
    elif "warning" in outcomes:
        summary["status"] = "warning"

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for entry in summary["views"]:
            print(f"view {entry['view']}: {entry['status']}")
            for path in entry["artifacts"]:
                print(f"  wrote {path}")
            for diagnostic in entry["diagnostics"]:
                print(f"  {diagnostic.get('severity', '?')}: {diagnostic.get('code', '?')}")
        for entry in summary["exports"]:
            print(f"export {entry['export']} ({entry['view']}): {entry['status']}")
            if entry["status"] != "error":
                print(f"  wrote {entry['output']}")
        print(f"build: {summary['status']}")
        if summary["status"] != "error":
            print("next: complete each rendered SVG's accessible name (svg-accessible-name.sh),")
            print("      then rebuild the package gallery (build-gallery.py).")

    return 1 if summary["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
