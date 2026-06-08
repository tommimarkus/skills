#!/usr/bin/env python3
"""Detect correction signals in a Claude Code session transcript (lesson loop, Plan 2).

Conservative by design: matches only strong correction phrases in USER turns, so the
Stop-hook gate prefers false negatives over noise. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# (label, pattern): strong, low-false-positive phrases only. Never bare "no".
CORRECTION_PATTERNS = (
    ("revert", r"\brevert(s|ed|ing)?\b"),
    ("undo", r"\bundo\b"),
    ("rollback", r"\broll ?back\b"),
    ("not-like-that", r"\bnot like that\b"),
    ("not-what-i", r"\bnot what i (asked|meant|wanted|said)\b"),
    ("thats-wrong", r"\bthat'?s wrong\b|\bthat is wrong\b"),
    ("incorrect", r"\bincorrect\b"),
    ("misunderstood", r"\byou misunderstood\b"),
    ("dont-do-that", r"\bdon'?t do that\b"),
    ("you-broke", r"\byou broke\b"),
    ("go-back", r"\bgo back to\b"),
)


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b["text"] for b in content
                 if isinstance(b, dict) and isinstance(b.get("text"), str)]
        return " ".join(parts)
    return ""


def _user_texts(transcript_path) -> list[str]:
    path = Path(transcript_path)
    if not path.exists():
        return []
    texts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        message = entry.get("message")
        role = message.get("role") if isinstance(message, dict) else None
        if role is None:
            role = entry.get("role") or entry.get("type")
        if role != "user":
            continue
        content = message.get("content") if isinstance(message, dict) else None
        text = _content_text(content)
        if text:
            texts.append(text)
    return texts


def detect_corrections(transcript_path) -> list[str]:
    """Return sorted labels of correction phrases found across user turns."""
    blob = "\n".join(_user_texts(transcript_path))
    found = {label for label, pattern in CORRECTION_PATTERNS
             if re.search(pattern, blob, re.IGNORECASE)}
    return sorted(found)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: lessons_capture_signals <transcript_path>", file=sys.stderr)
        return 2
    labels = detect_corrections(argv[0])
    for label in labels:
        print(label)
    return 0 if labels else 1


if __name__ == "__main__":
    raise SystemExit(main())
