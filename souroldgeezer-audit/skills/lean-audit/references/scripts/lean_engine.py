"""lean-audit deterministic duplication engine (stdlib-only)."""
from __future__ import annotations

import re

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_WORD = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> list[str]:
    text = _FENCE.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _INLINE_CODE.sub(" ", text)
    return _WORD.findall(text.lower())
