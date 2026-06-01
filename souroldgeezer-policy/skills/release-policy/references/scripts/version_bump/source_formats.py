from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import source_read, source_write


def read_json(path: Path, text: str) -> str:
    data = json.loads(text)
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str):
        raise source_read(f"{path} has no top-level string version field")
    return version


def write_json(path: Path, text: str, current: str, next_version: str) -> str:
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("version") != current:
        raise source_write(f"{path} no longer has expected version {current}")
    data["version"] = next_version
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def read_toml(path: Path, text: str) -> str:
    import tomllib

    data = tomllib.loads(text)
    values = [
        nested_get(data, ("version",)),
        nested_get(data, ("project", "version")),
        nested_get(data, ("package", "version")),
        nested_get(data, ("workspace", "package", "version")),
        nested_get(data, ("tool", "poetry", "version")),
    ]
    candidates = sorted({value for value in values if isinstance(value, str)})
    if len(candidates) != 1:
        raise source_read(f"{path} must expose exactly one TOML version source")
    return candidates[0]


def write_toml(path: Path, text: str, current: str, next_version: str) -> str:
    pattern = re.compile(
        r"(?m)^(\s*version\s*=\s*['\"])" + re.escape(current) + r"(['\"]\s*(?:#.*)?)$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise source_write(f"{path} must contain one writable version assignment")
    return pattern.sub(r"\g<1>" + next_version + r"\g<2>", text, count=1)


def read_text(path: Path, text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise source_read(f"{path} must contain exactly one version line")
    return lines[0]


def write_text(_path: Path, _text: str, _current: str, next_version: str) -> str:
    return next_version + "\n"


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


READERS = {"json": read_json, "toml": read_toml, "text": read_text}
WRITERS = {"json": write_json, "toml": write_toml, "text": write_text}
