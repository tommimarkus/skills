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
import re
import shutil
import sys
from pathlib import Path
from typing import Any

SCHEMA = "architecture-review-copy-v1"
MANIFEST = ".architecture-review-copy.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CopyError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def read_json_snapshot(path: Path, rel: Path, label: str) -> tuple[Any, str]:
    try:
        content = path.read_bytes()
        return json.loads(content), sha256_bytes(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CopyError(f"invalid {label} JSON: {rel.as_posix()}") from exc


def emit(value: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(value, sort_keys=True))
    return code


def relative_path(
    root: Path,
    raw: str,
    label: str,
    base: Path | None = None,
    *,
    reject_symlinks: bool = True,
) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise CopyError(f"{label} must be workspace-relative: {raw}")
    cursor = base or root
    for part in path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            parent = cursor.parent
            if parent != root and root not in parent.parents:
                raise CopyError(f"{label} escapes workspace: {raw}")
            cursor = parent
            continue
        cursor /= part
        if reject_symlinks and cursor.is_symlink():
            raise CopyError(f"{label} traverses a symlink: {raw}")
    candidate = Path(os.path.normpath(str((base or root) / path)))
    # Check lexical containment before resolving so an in-root symlink cannot
    # disappear into its target before the caller checks every ancestor.
    try:
        return candidate.relative_to(root)
    except ValueError as exc:
        raise CopyError(f"{label} escapes workspace: {raw}") from exc


def absolute_path(raw: Path, label: str, *, require_directory: bool = False) -> Path:
    """Validate an absolute path without following a symlinked identity."""
    if not raw.is_absolute():
        raise CopyError(f"{label} must be absolute")
    lexical = Path(os.path.abspath(raw))
    cursor = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        cursor /= part
        if cursor.is_symlink():
            raise CopyError(f"{label} has a symlink component: {cursor}")
        if not cursor.exists():
            break
    if require_directory:
        if not lexical.exists():
            raise CopyError(f"{label} does not exist: {lexical}")
        if not lexical.is_dir():
            raise CopyError(f"{label} is not a directory: {lexical}")
    return lexical


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


def current_path_state(root: Path, rel: Path) -> tuple[str, str | None]:
    """Return a verification state without following symlinked ancestors."""
    cursor = root
    for part in rel.parts:
        cursor /= part
        if cursor.is_symlink():
            return "unsafe", None
        if not cursor.exists():
            return "missing", None
        if cursor != root / rel and not cursor.is_dir():
            return "unsafe", None
    if cursor.is_file():
        return "regular", sha256(cursor)
    return "unsafe", None


def require_path_field(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CopyError(f"{label} must be a non-empty path string")
    return value


def package_tree_files(root: Path, package_dir: Path) -> set[Path]:
    directory = ensure_regular_directory(root, package_dir)
    files: set[Path] = set()
    for entry in directory.rglob("*"):
        rel = entry.relative_to(root)
        if entry.is_symlink():
            raise CopyError(f"symlink is not permitted: {rel.as_posix()}")
        if entry.is_file():
            files.add(rel)
        elif not entry.is_dir():
            raise CopyError(f"nonregular input: {rel.as_posix()}")
    return files


def ensure_regular_directory(root: Path, rel: Path) -> Path:
    path = root / rel
    cursor = root
    for part in rel.parts:
        cursor /= part
        if cursor.is_symlink():
            raise CopyError(f"symlink is not permitted: {rel.as_posix()}")
    if not path.exists() or not path.is_dir():
        raise CopyError(f"missing package directory: {rel.as_posix()}")
    return path


def package_files(
    root: Path,
    package_rel: Path,
    package_data: dict[str, Any],
    parsed_hashes: dict[Path, str],
) -> tuple[set[Path], set[Path], set[Path]]:
    package_dir = package_rel.parent
    copied: set[Path] = set()
    inputs: set[Path] = set()
    outputs: set[Path] = set()

    def declare_output(rel: Path) -> None:
        for existing in outputs:
            if rel == existing or rel in existing.parents or existing in rel.parents:
                raise CopyError(
                    f"declared output path collision: {existing.as_posix()} and {rel.as_posix()}"
                )
        outputs.add(rel)

    # The complete package tree is copied so local gallery/theme assets and
    # declared generated evidence retain their original byte state.
    copied.update(package_tree_files(root, package_dir))
    copied.add(package_rel)
    inputs.add(package_rel)
    # package.schema.v1 paths are relative to package.json, except a permitted
    # ../ reference still resolves within workspace root.
    if not isinstance(package_data.get("models"), list):
        raise CopyError("package models must be a list")
    for model in package_data["models"]:
        if not isinstance(model, dict):
            raise CopyError("package model lacks source")
        source = require_path_field(model.get("source"), "package model source")
        inputs.add(relative_path(root, source, "source", root / package_dir))
    if not isinstance(package_data.get("views"), list):
        raise CopyError("package views must be a list")
    for view in package_data["views"]:
        if not isinstance(view, dict):
            raise CopyError("invalid package view")
        render_policy = require_path_field(view.get("render_policy"), "view render_policy")
        inputs.add(relative_path(root, render_policy, "render_policy", root / package_dir))
        declared = view.get("outputs", {})
        if not isinstance(declared, dict):
            raise CopyError("invalid view outputs")
        for key in ("diagram", "layout", "render_metadata"):
            if key == "diagram" or key in declared:
                raw_output = require_path_field(declared.get(key), f"view output {key}")
                declare_output(relative_path(root, raw_output, key, root / package_dir))
    if not isinstance(package_data.get("exports", []), list):
        raise CopyError("package exports must be a list")
    for export in package_data.get("exports", []):
        if not isinstance(export, dict):
            raise CopyError("invalid package export")
        policy = require_path_field(export.get("policy"), "export policy")
        output = require_path_field(export.get("output"), "export output")
        inputs.add(relative_path(root, policy, "policy", root / package_dir))
        declare_output(relative_path(root, output, "output", root / package_dir))
    # Fragments are source inputs, not a recursive package mechanism. Reject a
    # fragment object that itself declares fragments: that shape cannot be
    # snapshot safely without widening the reviewed package graph.
    for model in package_data["models"]:
        source = model.get("source") if isinstance(model, dict) else None
        if isinstance(source, str):
            rel = relative_path(root, source, "source", root / package_dir)
            source_path = ensure_regular(root, rel)
            model_data, parsed_hashes[rel] = read_json_snapshot(source_path, rel, "model")
            if not isinstance(model_data, dict):
                raise CopyError(f"model JSON must be an object: {rel.as_posix()}")
            fragments = model_data.get("fragments", [])
            if not isinstance(fragments, list):
                raise CopyError(f"invalid fragments list: {rel.as_posix()}")
            for fragment in fragments:
                if not isinstance(fragment, str):
                    raise CopyError(f"invalid fragment path: {rel.as_posix()}")
                fragment_rel = relative_path(root, fragment, "fragment", source_path.parent)
                fragment_path = ensure_regular(root, fragment_rel)
                fragment_data, parsed_hashes[fragment_rel] = read_json_snapshot(
                    fragment_path, fragment_rel, "fragment"
                )
                if not isinstance(fragment_data, dict):
                    raise CopyError(f"fragment JSON must be an object: {fragment_rel.as_posix()}")
                if "fragments" in fragment_data:
                    raise CopyError(f"nested fragments are not supported: {fragment_rel.as_posix()}")
                inputs.add(fragment_rel)
    # A gallery is a declared review surface even when the package has not yet
    # generated it; preserve its absence in the snapshot.
    declare_output(package_dir / "gallery.html")
    for output in outputs:
        existing = root / output
        if existing.exists() or existing.is_symlink():
            ensure_regular(root, output)
            copied.add(output)
    copied.update(inputs)
    return copied, inputs, outputs


def prepare(workspace_root: Path, package: str, destination: Path) -> dict[str, Any]:
    root = absolute_path(workspace_root, "workspace-root", require_directory=True)
    package_rel = relative_path(root, package, "package")
    package_path = ensure_regular(root, package_rel)
    if package_path.name != "package.json":
        raise CopyError("package must name package.json")
    package_data, package_hash = read_json_snapshot(package_path, package_rel, "package")
    if not isinstance(package_data, dict):
        raise CopyError("package JSON must be an object")
    destination = absolute_path(destination, "destination")
    if destination.exists() or destination.is_symlink():
        raise CopyError(f"destination already exists: {destination}")
    if destination == root or root in destination.parents or destination in root.parents:
        raise CopyError("destination overlaps workspace root")
    parsed_hashes = {package_rel: package_hash}
    paths, inputs, outputs = package_files(root, package_rel, package_data, parsed_hashes)
    reserved = Path(MANIFEST)
    for rel in paths | outputs:
        if rel == reserved or reserved in rel.parents or rel in reserved.parents:
            raise CopyError(f"reserved manifest path collision: {rel.as_posix()}")
    for rel in paths:
        ensure_regular(root, rel)
    for output in outputs:
        for input_path in inputs:
            if output == input_path or output in input_path.parents or input_path in output.parents:
                raise CopyError(
                    f"input/output path collision: {input_path.as_posix()} and {output.as_posix()}"
                )
        for copied_path in paths:
            if copied_path != output and (
                copied_path in output.parents or output in copied_path.parents
            ):
                raise CopyError(
                    f"copied file/output path collision: {copied_path.as_posix()} and {output.as_posix()}"
                )
    # Destination root acts as the copied workspace root, preserving every
    # workspace-relative path used by package.json, including ../ references.
    package_inventory = package_tree_files(root, package_rel.parent)
    planned_package_inventory = {
        rel for rel in paths
        if package_rel.parent == Path(".") or package_rel.parent in rel.parents
    }
    if package_inventory != planned_package_inventory:
        raise CopyError("package file inventory changed before copy")
    preflight_hashes = {rel: sha256(root / rel) for rel in paths}
    for rel, parsed_hash in parsed_hashes.items():
        if preflight_hashes.get(rel) != parsed_hash:
            raise CopyError(f"parsed input changed before copy: {rel.as_posix()}")
    output_states: dict[Path, str | None] = {}
    for rel in outputs:
        state, actual = current_path_state(root, rel)
        if state == "unsafe":
            raise CopyError(f"nonregular input: {rel.as_posix()}")
        expected = preflight_hashes.get(rel) if rel in paths else None
        if (state == "regular" and actual != expected) or (
            state == "missing" and expected is not None
        ):
            raise CopyError(f"original changed before copy: {rel.as_posix()}")
        output_states[rel] = actual
    destination.mkdir(parents=True, exist_ok=False)
    mapping: dict[str, str | None] = {}
    for rel in sorted(paths):
        source = root / rel
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        ensure_regular(root, rel)
        if sha256(source) != preflight_hashes[rel] or sha256(target) != preflight_hashes[rel]:
            raise CopyError(f"original changed during copy: {rel.as_posix()}")
        mapping[rel.as_posix()] = preflight_hashes[rel]
    if package_tree_files(root, package_rel.parent) != package_inventory:
        raise CopyError("package file inventory changed during copy")
    for rel, expected in preflight_hashes.items():
        state, actual = current_path_state(root, rel)
        if state != "regular" or actual != expected:
            raise CopyError(f"original changed during copy: {rel.as_posix()}")
    for rel, expected in output_states.items():
        state, actual = current_path_state(root, rel)
        if (expected is None and state != "missing") or (
            expected is not None and (state != "regular" or actual != expected)
        ):
            raise CopyError(f"original changed during copy: {rel.as_posix()}")
        mapping.setdefault(rel.as_posix(), expected)
    manifest = {
        "schema": SCHEMA,
        "original_workspace_root": str(root),
        "workspace_root": str(destination),
        "package": package_rel.as_posix(),
        "files": mapping,
    }
    (destination / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "ok", "manifest": str(destination / MANIFEST), "workspace_root": str(destination), "package": package_rel.as_posix()}


def changed_result(changes: set[str]) -> tuple[dict[str, Any], int]:
    ordered = sorted(changes)
    return {
        "status": "unchanged" if not ordered else "changed",
        "changed_count": len(ordered),
        "changed_paths": ordered[:20],
    }, 0 if not ordered else 1


def verify_original(manifest_path: Path) -> tuple[dict[str, Any], int]:
    manifest_path = absolute_path(manifest_path, "manifest")
    if not manifest_path.exists() or not manifest_path.is_file():
        raise CopyError(f"manifest is not a regular file: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CopyError("manifest JSON must be an object")
    if data.get("schema") != SCHEMA:
        raise CopyError("unsupported manifest schema")
    required = {"original_workspace_root", "workspace_root", "package", "files"}
    if not required <= set(data) or not isinstance(data["files"], dict):
        raise CopyError("invalid manifest")
    for field in ("original_workspace_root", "workspace_root", "package"):
        if not isinstance(data[field], str) or not data[field]:
            raise CopyError(f"invalid manifest {field}")
    root = Path(data["original_workspace_root"])
    copied_root = Path(data["workspace_root"])
    if not root.is_absolute() or not copied_root.is_absolute():
        raise CopyError("manifest workspace roots must be absolute")
    if manifest_path != copied_root / MANIFEST:
        raise CopyError("manifest path does not match its copied workspace root")
    changes: set[str] = set()
    root_safe = True
    try:
        root = absolute_path(root, "original workspace root", require_directory=True)
    except CopyError:
        root_safe = False
    validated_files: dict[Path, str | None] = {}
    for raw, expected in data["files"].items():
        if not isinstance(raw, str) or not raw or (expected is not None and (
            not isinstance(expected, str) or not SHA256_RE.fullmatch(expected)
        )):
            raise CopyError("invalid manifest files mapping")
        lexical_root = Path(os.path.abspath(root))
        rel = relative_path(lexical_root, raw, "manifest file", reject_symlinks=False)
        if rel.as_posix() != raw:
            raise CopyError(f"manifest file is not canonical: {raw}")
        validated_files[rel] = expected
    package_rel = relative_path(
        Path(os.path.abspath(root)), data["package"], "package", reject_symlinks=False
    )
    if package_rel.as_posix() != data["package"] or package_rel.name != "package.json":
        raise CopyError("invalid manifest package")
    if not root_safe:
        changes.update(path.as_posix() for path in validated_files)
        changes.add(package_rel.as_posix())
        return changed_result(changes)
    for rel, expected in validated_files.items():
        state, actual = current_path_state(root, rel)
        if (expected is None and state != "missing") or (
            expected is not None and (state != "regular" or actual != expected)
        ):
            changes.add(rel.as_posix())
    package_expected = validated_files.get(package_rel)
    package_state, package_actual = current_path_state(root, package_rel)
    if package_expected is None or package_state != "regular" or package_actual != package_expected:
        changes.add(package_rel.as_posix())
        return changed_result(changes)
    package_dir = package_rel.parent
    recorded_package_files = {
        rel for rel, expected in validated_files.items()
        if expected is not None and (package_dir == Path(".") or package_dir in rel.parents)
    }
    try:
        current_package_files = package_tree_files(root, package_dir)
    except CopyError:
        changes.add(package_dir.as_posix())
        return changed_result(changes)
    changes.update(path.as_posix() for path in current_package_files ^ recorded_package_files)
    return changed_result(changes)


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
        if not Path(args.manifest).is_absolute():
            raise CopyError("manifest must be absolute")
        value, code = verify_original(Path(args.manifest))
        return emit(value, code)
    except (CopyError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"review-copy: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
