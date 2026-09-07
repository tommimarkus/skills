#!/usr/bin/env python3
"""Prepare an isolated, byte-accounted Dediren package copy for Review.

The helper deliberately has no build, promotion, or cleanup command: the caller
owns the persistent destination and the original package remains the evidence of
record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

SCHEMA = "architecture-review-copy-v1"
MANIFEST = ".architecture-review-copy.json"
PATH_KEYS = {"source", "policy", "render_policy", "export_policy", "theme", "gallery"}
OUTPUT_KEYS = {"output", "diagram", "layout", "render_metadata", "gallery"}


class CopyError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def emit(value: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(value, sort_keys=True))
    return code


def relative_path(root: Path, raw: str, label: str, base: Path | None = None) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise CopyError(f"{label} must be workspace-relative: {raw}")
    candidate = Path(os.path.normpath(str((base or root) / path)))
    # Check lexical containment before resolving so an in-root symlink cannot
    # disappear into its target before the caller checks every ancestor.
    try:
        return candidate.relative_to(root)
    except ValueError as exc:
        raise CopyError(f"{label} escapes workspace: {raw}") from exc


def ensure_regular(root: Path, rel: Path, required: bool = True) -> Path | None:
    path = root / rel
    # A symlink at any point is forbidden, even when it resolves inside the root.
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise CopyError(f"symlink is not permitted: {rel.as_posix()}")
    if not path.exists():
        if required:
            raise CopyError(f"missing required input: {rel.as_posix()}")
        return None
    if not path.is_file():
        raise CopyError(f"nonregular input: {rel.as_posix()}")
    return path


def package_files(root: Path, package_rel: Path, package_data: dict[str, Any]) -> tuple[set[Path], set[Path], set[Path]]:
    package_dir = package_rel.parent
    copied: set[Path] = set()
    inputs: set[Path] = set()
    outputs: set[Path] = set()
    # The complete package tree is copied so local gallery/theme assets and
    # declared generated evidence retain their original byte state.
    directory = root / package_dir
    for entry in directory.rglob("*"):
        rel = entry.relative_to(root)
        if entry.is_symlink():
            raise CopyError(f"symlink is not permitted: {rel.as_posix()}")
        if entry.is_file():
            copied.add(rel)
        elif not entry.is_dir():
            raise CopyError(f"nonregular input: {rel.as_posix()}")
    copied.add(package_rel)
    inputs.add(package_rel)
    # package.schema.v1 paths are relative to package.json, except a permitted
    # ../ reference still resolves within workspace root.
    if not isinstance(package_data.get("models"), list):
        raise CopyError("package models must be a list")
    for model in package_data["models"]:
        if not isinstance(model, dict) or not isinstance(model.get("source"), str):
            raise CopyError("package model lacks source")
        inputs.add(relative_path(root, model["source"], "source", root / package_dir))
    if not isinstance(package_data.get("views"), list):
        raise CopyError("package views must be a list")
    for view in package_data["views"]:
        if not isinstance(view, dict):
            raise CopyError("invalid package view")
        if isinstance(view.get("render_policy"), str):
            inputs.add(relative_path(root, view["render_policy"], "render_policy", root / package_dir))
        declared = view.get("outputs", {})
        if not isinstance(declared, dict):
            raise CopyError("invalid view outputs")
        for key in ("diagram", "layout", "render_metadata"):
            if isinstance(declared.get(key), str):
                outputs.add(relative_path(root, declared[key], key, root / package_dir))
    if not isinstance(package_data.get("exports", []), list):
        raise CopyError("package exports must be a list")
    for export in package_data.get("exports", []):
        if not isinstance(export, dict):
            raise CopyError("invalid package export")
        if isinstance(export.get("policy"), str):
            inputs.add(relative_path(root, export["policy"], "policy", root / package_dir))
        if isinstance(export.get("output"), str):
            outputs.add(relative_path(root, export["output"], "output", root / package_dir))
    # Fragments are source inputs, not a recursive package mechanism. Reject a
    # fragment object that itself declares fragments: that shape cannot be
    # snapshot safely without widening the reviewed package graph.
    for model in package_data["models"]:
        source = model.get("source") if isinstance(model, dict) else None
        if isinstance(source, str):
            rel = relative_path(root, source, "source", root / package_dir)
            source_path = ensure_regular(root, rel)
            try:
                model_data = json.loads(source_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise CopyError(f"invalid model JSON: {rel.as_posix()}") from exc
            fragments = model_data.get("fragments", [])
            if not isinstance(fragments, list):
                raise CopyError(f"invalid fragments list: {rel.as_posix()}")
            for fragment in fragments:
                if not isinstance(fragment, str):
                    raise CopyError(f"invalid fragment path: {rel.as_posix()}")
                fragment_rel = relative_path(root, fragment, "fragment", source_path.parent)
                fragment_path = ensure_regular(root, fragment_rel)
                try:
                    fragment_data = json.loads(fragment_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    raise CopyError(f"invalid fragment JSON: {fragment_rel.as_posix()}") from exc
                if "fragments" in fragment_data:
                    raise CopyError(f"nested fragments are not supported: {fragment_rel.as_posix()}")
                inputs.add(fragment_rel)
    # A gallery is a declared review surface even when the package has not yet
    # generated it; preserve its absence in the snapshot.
    outputs.add(package_dir / "gallery.html")
    for output in outputs:
        existing = root / output
        if existing.exists() or existing.is_symlink():
            ensure_regular(root, output)
            copied.add(output)
    copied.update(inputs)
    return copied, inputs, outputs


def prepare(workspace_root: Path, package: str, destination: Path) -> dict[str, Any]:
    root = workspace_root.resolve(strict=True)
    package_rel = relative_path(root, package, "package")
    package_path = ensure_regular(root, package_rel)
    if package_path.name != "package.json":
        raise CopyError("package must name package.json")
    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CopyError(f"invalid package JSON: {package_rel.as_posix()}") from exc
    if not isinstance(package_data, dict):
        raise CopyError("package JSON must be an object")
    raw_destination = destination.absolute()
    for ancestor in (raw_destination, *raw_destination.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise CopyError(f"destination has a symlink ancestor: {ancestor}")
    destination = raw_destination.resolve(strict=False)
    if destination.exists():
        raise CopyError(f"destination already exists: {destination}")
    if destination == root or root in destination.parents or destination in root.parents:
        raise CopyError("destination overlaps workspace root")
    paths, inputs, outputs = package_files(root, package_rel, package_data)
    reserved = Path(MANIFEST)
    if reserved in paths or reserved in outputs:
        raise CopyError(f"reserved manifest path collision: {MANIFEST}")
    for rel in paths:
        ensure_regular(root, rel)
    for output in outputs:
        for input_path in inputs:
            if output == input_path or output in input_path.parents or input_path in output.parents:
                raise CopyError(
                    f"input/output path collision: {input_path.as_posix()} and {output.as_posix()}"
                )
    # Destination root acts as the copied workspace root, preserving every
    # workspace-relative path used by package.json, including ../ references.
    preflight_hashes = {rel: sha256(root / rel) for rel in paths}
    destination.mkdir(parents=True)
    mapping: dict[str, str | None] = {}
    for rel in sorted(paths):
        source = root / rel
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256(source) != preflight_hashes[rel] or sha256(target) != preflight_hashes[rel]:
            raise CopyError(f"original changed during copy: {rel.as_posix()}")
        mapping[rel.as_posix()] = preflight_hashes[rel]
    for rel in sorted(outputs):
        mapping.setdefault(rel.as_posix(), sha256(root / rel) if (root / rel).is_file() else None)
    manifest = {
        "schema": SCHEMA,
        "original_workspace_root": str(root),
        "workspace_root": str(destination),
        "package": package_rel.as_posix(),
        "files": mapping,
    }
    (destination / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "ok", "manifest": str(destination / MANIFEST), "workspace_root": str(destination), "package": package_rel.as_posix()}


def verify_original(manifest_path: Path) -> tuple[dict[str, Any], int]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise CopyError("unsupported manifest schema")
    required = {"original_workspace_root", "workspace_root", "package", "files"}
    if not required <= set(data) or not isinstance(data["files"], dict):
        raise CopyError("invalid manifest")
    root = Path(data["original_workspace_root"])
    changes = []
    for raw, expected in data.get("files", {}).items():
        rel = relative_path(root.resolve(strict=True), raw, "manifest file")
        path = root / rel
        actual = sha256(path) if path.is_file() and not path.is_symlink() else None
        if actual != expected:
            changes.append(raw)
    package_rel = relative_path(root.resolve(strict=True), data["package"], "package")
    package_path = ensure_regular(root, package_rel)
    package_data = json.loads(package_path.read_text(encoding="utf-8"))
    inventory, _, _ = package_files(root, package_rel, package_data)
    recorded = set(data["files"])
    for path in sorted(inventory, key=lambda item: item.as_posix()):
        if path.as_posix() not in recorded:
            changes.append(path.as_posix())
    return {"status": "unchanged" if not changes else "changed", "changed_count": len(changes), "changed_paths": changes[:20]}, 0 if not changes else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--workspace-root", required=True)
    prepare_parser.add_argument("--package", required=True)
    prepare_parser.add_argument("--destination", required=True)
    verify_parser = sub.add_parser("verify-original")
    verify_parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            if not Path(args.workspace_root).is_absolute() or not Path(args.destination).is_absolute():
                raise CopyError("workspace-root and destination must be absolute")
            return emit(prepare(Path(args.workspace_root), args.package, Path(args.destination)))
        value, code = verify_original(Path(args.manifest))
        return emit(value, code)
    except (CopyError, OSError, json.JSONDecodeError) as exc:
        print(f"review-copy: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
