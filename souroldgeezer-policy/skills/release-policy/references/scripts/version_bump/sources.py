from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import source_read, source_write
from .source_formats import READERS, WRITERS


def read_version(path: Path, requested_kind: str) -> tuple[str, str]:
    kind = detect_source_kind(path, requested_kind)
    try:
        text = path.read_text(encoding="utf-8")
        return kind, read_version_text(path, kind, text)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        raise source_read(f"{path}: {exc}") from exc


def detect_source_kind(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    name = path.name.lower()
    suffix = path.suffix.lower()
    suffix_kinds = {".json": "json", ".toml": "toml", ".txt": "text", ".version": "text"}
    if suffix in suffix_kinds:
        return suffix_kinds[suffix]
    if name in {"version", ".version"}:
        return "text"
    raise source_read(f"cannot infer source kind for {path}; pass --source-kind")


def read_version_text(path: Path, kind: str, text: str) -> str:
    reader = READERS.get(kind)
    if not reader:
        raise source_read(f"unsupported source kind: {kind}")
    return reader(path, text)


def write_version(path: Path, kind: str, current: str, next_version: str) -> None:
    try:
        text = path.read_text(encoding="utf-8")
        updated = write_version_text(path, kind, text, current, next_version)
        path.write_text(updated, encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise source_write(f"{path}: {exc}") from exc


def write_version_text(
    path: Path,
    kind: str,
    text: str,
    current: str,
    next_version: str,
) -> str:
    writer = WRITERS.get(kind)
    if not writer:
        raise source_write(f"unsupported source kind: {kind}")
    return writer(path, text, current, next_version)
