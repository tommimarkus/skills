"""Shared JSON object/list and JSONL reader for metadata-only evidence rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

__all__ = ["read_json_rows"]


def read_json_rows(
    path: Path,
    *,
    nested_list_key: str | None = None,
    scalar_error: str,
    row_error: str,
) -> list[dict[str, Any]]:
    """Read JSON/JSONL rows and require every returned row to be an object."""
    text = path.read_text(encoding="utf-8")
    rows: list[Any]
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # JSONL readers intentionally use the canonical nonblank-line decode expression.
        # lean-audit:dup-intentional:begin
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        # lean-audit:dup-intentional:end
    else:
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            nested = payload.get(nested_list_key) if nested_list_key is not None else None
            rows = nested if isinstance(nested, list) else [payload]
        else:
            raise ValueError(f"{path}: {scalar_error}")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: {row_error}")
    return cast(list[dict[str, Any]], rows)
