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

# lean-audit:dup-intentional — declarative (label, pattern) tuple literal, same
# shape as lessons_secret_scan.py's SECRET_PATTERNS but distinct content (correction
# phrases vs secret shapes); this is data-table shape, not extractable logic.
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


AUDIT_SKILLS = ("lean-audit", "ip-hygiene", "devsecops-audit", "test-quality-audit")
_AUDIT_SKILL_RE = re.compile(r"(?:^|[:/])(" + "|".join(AUDIT_SKILLS) + r")(?:/SKILL\.md)?$")
_REPORT_RE = re.compile(r"skill[-_]architecture[-_]report")


def _tool_calls(entry: dict):
    """Yield (name, input) for tool calls in a Claude or Codex transcript entry."""
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block.get("name"), block.get("input")
    payload = entry.get("payload")
    if isinstance(payload, dict) and payload.get("type") == "function_call":
        arguments = payload.get("arguments")
        try:
            arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            pass
        yield payload.get("name"), arguments


def _call_labels(name, args) -> set[str]:
    found = set()
    if name == "Skill" and isinstance(args, dict):
        match = _AUDIT_SKILL_RE.search(str(args.get("skill", "")))
        if match:
            found.add(match.group(1))
    text = json.dumps(args) if not isinstance(args, str) else args
    if _REPORT_RE.search(text):
        found.add("skill-architecture-report")
    for skill in AUDIT_SKILLS:
        if f"{skill}/SKILL.md" in text:
            found.add(skill)
    return found


def detect_audit_runs(transcript_path) -> list[str]:
    """Return sorted audit skills / report runs recorded as tool calls; [] on any error."""
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    found: set[str] = set()
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        for name, args in _tool_calls(entry):
            found |= _call_labels(name, args)
    return sorted(found)


def detect_corrections(transcript_path) -> list[str]:
    """Return sorted labels of correction phrases found across user turns."""
    blob = "\n".join(_user_texts(transcript_path))
    found = {label for label, pattern in CORRECTION_PATTERNS
             if re.search(pattern, blob, re.IGNORECASE)}
    return sorted(found)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    audit = bool(argv) and argv[0] == "--audit-runs"
    if audit:
        argv = argv[1:]
    if not argv:
        print("usage: lessons_capture_signals [--audit-runs] <transcript_path>", file=sys.stderr)
        return 2
    labels = detect_audit_runs(argv[0]) if audit else detect_corrections(argv[0])
    for label in labels:
        print(label)
    return 0 if labels else 1


if __name__ == "__main__":
    raise SystemExit(main())
