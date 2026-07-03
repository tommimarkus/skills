"""lean-audit PreToolUse guard hook (opt-in, fail-open).

Soft-blocks an Edit/Write/MultiEdit that would introduce a NEW block-severity
duplication into guarded markdown. Reads the PreToolUse JSON on stdin, emits a
`deny` decision on a block hit, and ALWAYS allows (exit 0, no stdout) on any
error, non-match, or non-guarded path. Carve-outs and the sync-intentional
override are inherited from the engine — this hook adds no duplication logic.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from leanaudit import hook_envelope
from leanaudit.discovery import is_guarded
from leanaudit.engine import evaluate_added_block
from leanaudit.hook_envelope import HookPayload

__all__ = ["evaluate", "main"]


def _added_content(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    if tool_name == "Write":
        c = tool_input.get("content")
        return c if isinstance(c, str) and c else None
    if tool_name == "Edit":
        c = tool_input.get("new_string")
        return c if isinstance(c, str) and c else None
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            parts = [e.get("new_string", "") for e in edits if isinstance(e, dict)]
            joined = "\n".join(p for p in parts if isinstance(p, str))
            return joined or None
    return None


def _repo_root(cwd: str) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except Exception as exc:
        # A non-repo cwd exits via returncode != 0 without raising; this fires
        # only on real execution failure (git missing, timeout, OSError).
        hook_envelope.fail_open_log("lean-guard", "repo-root", exc)
        return None
    return None


def evaluate(payload: HookPayload) -> str | None:
    """Return a deny-reason if the edit introduces a block dup, else None."""
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if tool_name not in ("Edit", "Write", "MultiEdit") or not isinstance(tool_input, dict):
        return None
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    content = _added_content(tool_name, tool_input)
    if not content:
        return None
    root = _repo_root(payload.get("cwd") or os.getcwd())
    if root is None:
        return None
    try:
        rel = Path(file_path).resolve().relative_to(root).as_posix()
    except Exception:
        return None  # edit is outside the repo or unresolvable path
    try:
        if not is_guarded(rel):
            return None
        findings = evaluate_added_block(root, rel, content, None)
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "engine-evaluate", exc)
        return None  # fail-open on engine error
    blocks = [f for f in findings if f.severity == "block"]
    if not blocks:
        return None
    try:
        f = blocks[0]
        return (
            f"lean-audit: this edit to {rel} duplicates "
            f'{f.matched_path} §"{f.matched_heading}" '
            f"(containment={f.containment}). {f.action} "
            "To override: cite the canonical source, restructure, or add "
            "'<!-- lean-audit:sync-intentional: <reason> -->' to the block."
        )
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "reason-format", exc)
        return None


def main() -> None:
    try:
        payload = hook_envelope.read_payload()
    except Exception:
        return  # fail-open: unreadable input
    try:
        reason = evaluate(payload) if isinstance(payload, dict) else None
    except Exception as exc:
        hook_envelope.fail_open_log("lean-guard", "main-backstop", exc)
        reason = None  # backstop fail-open
    if reason:
        print(json.dumps(hook_envelope.permission_decision("deny", reason)))
